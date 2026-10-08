'use strict';
// Isolated fixtures only. No live credentials, notifications or customer-data writes.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),vm=require('node:vm'),crypto=require('node:crypto');
const {stripTypeScriptTypes}=require('node:module');
const {chromium,webkit}=require('playwright');
const out=path.resolve(process.env.OUT||'qa-results/support-release');fs.mkdirSync(out,{recursive:true});
const report={backend:[],browser:[],status:'RUNNING'};
const clean=s=>stripTypeScriptTypes(s).replace(/^import .*;\s*$/gm,'').replace(/^export /gm,'');
const baseContext=()=>({console,Intl,Date,Math,JSON,Map,Set,Number,String,Boolean,Array,Uint8Array,TextEncoder,TextDecoder,Response,Request,URL,AbortSignal,crypto:crypto.webcrypto});
async function backendTests(){
 const calls=[],context=baseContext();let responseMode='success';
 context.fetch=async(u,init={})=>{const url=new URL(u);assert.equal(url.hostname,'database.invalid');calls.push({url,init});if(responseMode==='throw')throw Error('PRIVATE DATABASE DETAILS');return new Response(JSON.stringify(responseMode==='rate'?{error:'rate_limited'}:{ok:true,receipt:'12345678-1234-4234-8234-123456789abc'}),{status:responseMode==='failed'?500:200,headers:{'content-type':'application/json'}})};
 vm.createContext(context);vm.runInContext(clean(fs.readFileSync('backend/fueldrop/support.ts','utf8')),context);
 const fixture={request_id:'12345678-1234-4234-8234-123456789abc',device_token:'a'.repeat(64),category:'map',message:'Fixture report for automated testing only.',consent:true,diagnostics:{screen:'explore',browser:'Chrome',viewport:'390x844',app_version:'support-qld-20261008',latitude:-27.4,longitude:153,email:'DO NOT STORE'}};
 const deps={base:()=> 'https://database.invalid',headers:()=>({apikey:'TEST_ONLY'})};
 const req=(body,method='POST',headers={'content-type':'application/json'})=>new Request('https://app.invalid/',{method,headers,body:method==='GET'?undefined:typeof body==='string'?body:JSON.stringify(body)});
 const run=async(label,body,status,method='POST',api='support-report',headers)=>{const result=await context.supportAPI(api,req(body,method,headers),deps);assert.equal(result.status,status,label);report.backend.push(label);return result};
 await run('Consent required',{...fixture,consent:false},400);
 await run('Strict request UUID',{...fixture,request_id:'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'},400);
 await run('Bounded note',{...fixture,message:'x'.repeat(2001)},400);
 await run('Short note rejected',{...fixture,message:'a'},400);
 await run('Unknown topic rejected',{...fixture,category:'secret'},400);
 await run('GET does not submit',fixture,405,'GET');
 await run('JSON type required',fixture,415,'POST','support-report',{'content-type':'text/plain'});
 await run('Invalid JSON rejected','{',400);
 await run('Actual body limit enforced',' '.repeat(17000),413);
 const ok=await run('Successful opt-in submission returns receipt',fixture,201);
 const stored=JSON.parse(calls.at(-1).init.body);assert.equal(stored.p_device,crypto.createHash('sha256').update(fixture.device_token).digest('hex'));assert.ok(!JSON.stringify(stored).includes('DO NOT STORE'));assert.equal(stored.p_request,fixture.request_id);assert.ok(!Object.keys(stored).some(k=>/latitude|longitude|email|token/.test(k)));report.backend.push('Only allowed diagnostic fields and hashed device ID stored');
 responseMode='rate';await run('Rate limit handled',fixture,429);responseMode='failed';await run('Database failure sanitised',fixture,503);responseMode='throw';const failed=await run('Network failure sanitised',fixture,503);assert.ok(!JSON.stringify(failed).includes('PRIVATE'));
 responseMode='success';await run('Deletion requires DELETE',fixture,405,'POST','support-delete');
 await run('Malformed deletion receipt rejected',{receipt:'---'.repeat(12),device_token:fixture.device_token},400,'DELETE','support-delete');
 await run('Deletion constrained to receipt and device',{receipt:ok.body.receipt,device_token:fixture.device_token},200,'DELETE','support-delete');assert.ok(calls.at(-1).url.searchParams.has('id'));assert.ok(calls.at(-1).url.searchParams.has('device_hash'));
 const q=baseContext(),writes=[];let empty=false,readInvalid=false;
 q.Deno={env:{get:k=>({SUPABASE_URL:'https://database.invalid',SUPABASE_SERVICE_ROLE_KEY:'TEST_ONLY',QLD_FUEL_API_TOKEN:'TEST_ONLY'})[k]},serve:()=>{}};
 const qSites=[{S:100,N:'Fixture QLD site',B:1,G1:10,A:'Fixture address',P:4000,Lat:-27.4698,Lng:153.0251}];
 q.fetch=async(u,init={})=>{const url=new URL(u);assert.ok(['database.invalid','fppdirectapi-prod.fuelpricesqld.com.au'].includes(url.hostname));const response=b=>new Response(JSON.stringify(b),{headers:{'content-type':'application/json'}});
 if(url.hostname==='fppdirectapi-prod.fuelpricesqld.com.au'){
  if(empty)return response({});
  if(url.pathname.endsWith('GetCountryFuelTypes'))return response({Fuels:[{FuelId:1,Name:'Diesel'},{FuelId:2,Name:'Premium Diesel'}]});
  if(url.pathname.endsWith('GetCountryBrands'))return response({Brands:[{BrandId:1,Name:'BP'}]});
  if(url.pathname.endsWith('GetCountryGeographicRegions'))return response({GeographicRegions:[{GeoRegionLevel:1,GeoRegionId:10,Name:'Brisbane'}]});
  if(url.pathname.endsWith('GetFullSiteDetails'))return response({S:qSites});
  if(url.pathname.endsWith('GetSitesPrices'))return response({SitePrices:[{SiteId:100,FuelId:1,Price:1819},{SiteId:100,FuelId:2,Price:9999}]});
  throw Error('Unexpected provider endpoint');
 }
 if((init.method||'GET')!=='GET'){writes.push({url,init});return response([])}
 if(readInvalid)return response({invalid:true});
 if(url.pathname.endsWith('fuel_type_reference'))return response([{fuel_id:1,name:'Diesel',app_fuel_type:'Diesel'},{fuel_id:2,name:'Premium Diesel',app_fuel_type:'Premium Diesel'}]);
 if(url.pathname.endsWith('fuel_site_reference')){assert.equal(url.searchParams.get('state_code'),'eq.QLD');assert.equal(url.searchParams.get('provider_code'),'eq.qld-fpqld');return response([{station_id:'100',station_name:'Fixture QLD site',brand:'BP',suburb:'Brisbane',latitude:-27.4698,longitude:153.0251}])}
 return response([]);
 };
 vm.createContext(q);vm.runInContext(clean(fs.readFileSync('backend/fueldrop/index.ts','utf8')),q);
 assert.equal(q.appFuelName('Premium Diesel'),'Premium Diesel');assert.equal(q.appFuelName('Diesel'),'Diesel');report.backend.push('Queensland keeps both diesel grades');
 await q.refreshQueenslandReference();const deletion=writes.find(x=>x.init.method==='DELETE'&&x.url.pathname.endsWith('fuel_site_reference'));assert.ok(deletion);assert.equal(deletion.url.searchParams.get('state_code'),'eq.QLD');assert.equal(deletion.url.searchParams.get('provider_code'),'eq.qld-fpqld');report.backend.push('Queensland reference cleanup explicitly scoped to state and provider');
 writes.length=0;empty=true;await assert.rejects(()=>q.refreshQueenslandReference(),/empty_reference/);assert.equal(writes.length,0);report.backend.push('Empty reference snapshot causes no mutations');
 empty=false;await q.loadQueenslandReference();report.backend.push('Queensland references read only Queensland records');readInvalid=true;await assert.rejects(()=>q.loadQueenslandReference(),/invalid_reference/);readInvalid=false;report.backend.push('Malformed reference reads rejected');
 writes.length=0;await q.syncQueenslandFuel();const priceWrite=writes.find(x=>x.init.method==='POST'&&x.url.pathname.endsWith('fuel_price_daily'));assert.ok(priceWrite);const prices=JSON.parse(priceWrite.init.body);assert.equal(prices.length,1);assert.equal(prices[0].price,181.9);assert.equal(prices[0].state_code,'QLD');report.backend.push('QLD price units converted; unavailable prices excluded');
 const before=writes.length;empty=true;await assert.rejects(()=>q.syncQueenslandFuel(),/empty_price/);assert.equal(writes.length,before);report.backend.push('Empty price snapshot cannot clear existing prices');
}
const root=path.resolve('web'),mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.webmanifest':'application/manifest+json'};
async function browserRun(engine,width,height,first,ready){
 const browser=await ({chromium,webkit}[engine]).launch({headless:true,...(process.env.SANDBOX_BROWSER&&engine==='chromium'?{args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process','--in-process-gpu','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']}:{})});
 try{
 const c=await browser.newContext({viewport:{width,height},hasTouch:width<1025,isMobile:width<1025,serviceWorkers:'block'});let posts=[],deletes=0,fail=true;
 await c.addInitScript(first=>{if(!first)localStorage.setItem('fmnOnboarded','1');localStorage.setItem('fdPrefs',JSON.stringify({state:'NSW',fuel:'Diesel',radius:20,alertRadius:25,tank:65,economy:9,vehicle:'car',frequency:'off'}))},first);
 await c.route('https://fillmenow.vercel.app/**',async r=>{let name=new URL(r.request().url()).pathname;if(name==='/')name='/index.html';const file=path.join(root,name);if(name==='/assets/maplibre.js'&&first)await new Promise(resolve=>setTimeout(resolve,1200));return fs.existsSync(file)?r.fulfill({body:fs.readFileSync(file),contentType:mime[path.extname(file)]||'application/octet-stream'}):r.fulfill({status:404,body:'Not found'})});
 await c.route('https://tiles.openfreemap.org/**',r=>r.fulfill({json:{version:8,sources:{},layers:[{id:'test-only',type:'background',paint:{'background-color':'#eef3ed'}}]}}));
 await c.route('**/functions/v1/fueldrop*',r=>{const api=new URL(r.request().url()).searchParams.get('api');if(api==='support-report'){posts.push(r.request().postDataJSON());if(fail)return r.fulfill({status:503,json:{ok:false,error:'support_unavailable'}});return r.fulfill({status:201,json:{ok:true,receipt:'12345678-1234-4234-8234-123456789abc'}})}if(api==='support-delete'){deletes++;return r.fulfill({json:{ok:true}})}assert.ok(['GET','OPTIONS'].includes(r.request().method()),'Unexpected real write');return r.fulfill({json:api==='status'?{ok:true,launchStates:ready?['NSW','WA','TAS','QLD']:['NSW','WA','TAS']}:api==='regions'?{regions:[]}:api==='prices'?{ok:true,rows:[]}:{ok:true,configured:false}})});
 const p=await c.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));p.setDefaultTimeout(15000);
 await p.goto('https://fillmenow.vercel.app/',{waitUntil:'commit'});
 if(first){await p.locator('#fmnOnboard').waitFor({state:'visible'});assert.equal(await p.evaluate(()=>typeof window.FD),'undefined','Onboarding must precede delayed application boot');await p.screenshot({path:path.join(out,engine+'-'+width+'-first-paint.png')});await p.waitForFunction(()=>!!window.FD);for(let i=0;i<3;i++){const b=await p.locator('#fmnOnboardGo').boundingBox();assert.ok(b&&b.y+b.height<=height+1);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await p.locator('#fmnOnboardGo').click()}await p.locator('#fmnOnboard').waitFor({state:'hidden'});}
 await p.waitForFunction(()=>window.FMNCoverage&&window.FMNHelp&&window.FD);
 assert.equal(await p.locator('#stateSelect option[value=QLD]').isDisabled(),!ready);
 await p.evaluate(()=>window.FMNHelp.open());await p.locator('#fmnHelp.open').waitFor();
 const back=await p.locator('.help-back').boundingBox();assert.ok(back&&back.x<50&&back.y+back.height<=height);
 await p.locator('#fmnHelpInput').fill('The map icons overlap a button');await p.locator('.help-composer button').click();assert.equal(posts.length,0);assert.ok((await p.locator('.help-log').innerText()).includes('Nothing is submitted'));
 await p.locator('.help-report-open').click();await p.locator('textarea[name=note]').fill('Fixture complaint: map icon covers the stations button.');await p.locator('.help-submit').click();assert.equal(posts.length,0,'Consent must be required');
 await p.locator('input[name=consent]').check();await p.locator('.help-submit').click();await p.waitForFunction(()=>document.querySelector('.help-result').textContent.includes('not confirmed'));assert.equal(posts.length,1);assert.ok((await p.locator('textarea[name=note]').inputValue()).includes('Fixture complaint'));fail=false;
 await p.locator('.help-submit').click();await p.waitForFunction(()=>document.querySelector('.help-result').textContent.includes('saved privately'));assert.equal(posts.length,2);assert.equal(posts[0].request_id,posts[1].request_id);assert.ok(!JSON.stringify(posts[0].diagnostics).match(/latitude|longitude|saved|email/));
 await p.locator('textarea[name=note]').fill('A different fixture suggestion for a later investigation.');await p.locator('input[name=consent]').check();await p.locator('.help-submit').click();await p.waitForFunction(()=>document.querySelector('.help-submit').disabled===false);assert.equal(posts.length,3);assert.notEqual(posts[2].request_id,posts[1].request_id);
 await p.locator('.help-delete').click();await p.waitForFunction(()=>document.querySelector('.help-result').textContent.includes('has been deleted'));assert.equal(deletes,1);
 await p.screenshot({path:path.join(out,engine+'-'+width+'-help.png')});await p.locator('.help-back').click();assert.equal(await p.locator('#fmnHelp').isVisible(),false);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
 report.browser.push({engine,width,height,firstRun:first,qldReady:ready,checks:['first-run sizing','private guided help','explicit consent','retry uses same request ID','new note uses new request ID','receipt and deletion','bottom-left Back','coverage gate'],errors});
 }finally{await browser.close()}
}
(async()=>{await backendTests();for(const name of ['web/index.html','web/privacy.html','web/terms.html','android/PLAY_STORE_LISTING.md'])assert.ok(!/itglandscape|poloskey|michael@|brisbanegraveldirect|in the green landscaping/i.test(fs.readFileSync(name,'utf8')),'Public identity scan: '+name);const cases=process.env.QUICK?[['chromium',390,844,true,true]]:[['chromium',320,568,true,true],['chromium',390,844,true,false],['chromium',430,932,false,true],['chromium',844,390,true,true],['webkit',390,844,true,true],['webkit',844,390,false,false]];for(const args of cases)await browserRun(...args);report.status='PASS';fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,backendChecks:report.backend.length,browserRuns:report.browser.length}));})().catch(e=>{report.status='FAIL';report.error=String(e.stack);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.error(e);process.exitCode=1});
