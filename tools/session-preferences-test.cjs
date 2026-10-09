'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const {chromium,webkit}=require('playwright');
const root=path.resolve('web'),out=path.resolve(process.env.OUT||'qa-results/session-preferences');fs.mkdirSync(out,{recursive:true});
const source=fs.readFileSync(path.join(root,'index.html'),'utf8');
const helper=source.match(/\/\/ FMN_PREF_MERGE_BEGIN\n([\s\S]*?)\/\/ FMN_PREF_MERGE_END/);assert.ok(helper);
const merge=vm.runInNewContext(helper[1]+';mergeStoredPreferences');
const base={state:'QLD',fuel:'Diesel',radius:10,vehicle:'car',tank:65,economy:9,frequency:'off'};
const truck={...base,vehicle:'truck',tank:250,economy:35,truck:{height:4.2,width:2,length:12,weight:12,configuration:'rigid'},vehicleProfiles:{truck:{tank:250,economy:35,truck:{height:4.2,width:2,length:12,weight:12,configuration:'rigid'}}}};
const report={unitChecks:0,runs:[],backendWrites:0,simulatedBrowserProfiles:true};
function unit(ok){assert.ok(ok);report.unitChecks++}
unit(merge(base,{...base,radius:20},truck).tank===250);
unit(merge(base,{...base,radius:20},truck).radius===20);
unit(merge(base,base,truck).vehicle==='truck');
unit(merge(truck,{...truck,tank:400},{...truck,radius:30}).tank===400);
unit(merge(truck,{...truck,tank:400},{...truck,radius:30}).radius===30);
unit(merge(truck,{...truck,vehicle:'car',tank:65,economy:9},{...truck,tank:300}).vehicle==='car');
const profiles=merge(base,{...base,vehicleProfiles:{car:{tank:70,economy:9}}},truck).vehicleProfiles;
unit(profiles.car.tank===70&&profiles.truck.tank===250);
unit(merge(base,base,null).tank===65);
unit(merge(base,base,[]).tank===65);
unit(!Object.hasOwn(merge(base,base,JSON.parse('{"__proto__":{"polluted":true}}')),'__proto__'));
unit(merge(truck,truck,{...truck,truck:{...truck.truck,height:4.3}}).truck.height===4.3);
const original=JSON.stringify(truck);merge(base,base,truck);unit(JSON.stringify(truck)===original);
const stamp=new Date().toISOString();
const fixture=[{station_id:'SESSION-QA-A',station_name:'Isolated test station',brand:'BP',latitude:-27.475,longitude:153.028,price:270,fuel_type:'Diesel',price_date:stamp.slice(0,10),synced_at:stamp,recommendation_eligible:true},{station_id:'SESSION-QA-B',station_name:'Second test station',brand:'Shell',latitude:-27.49,longitude:153.04,price:290,fuel_type:'Diesel',price_date:stamp.slice(0,10),synced_at:stamp,recommendation_eligible:true}];
const mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
async function context(browser,width,height){const c=await browser.newContext({viewport:{width,height},hasTouch:true,isMobile:width<900,serviceWorkers:'block'});
 await c.addInitScript(({base})=>{try{localStorage.setItem('fmnOnboarded','1');if(!localStorage.getItem('fdPrefs'))localStorage.setItem('fdPrefs',JSON.stringify(base));if(!localStorage.getItem('fdLoc'))localStorage.setItem('fdLoc',JSON.stringify({lat:-27.47,lng:153.025,label:'Isolated QA area',state:'QLD'}));}catch{}},{base});
 if(!process.env.TARGET){await c.route('https://fillmenow.vercel.app/**',r=>{const u=new URL(r.request().url()),f=path.join(root,u.pathname==='/'?'index.html':u.pathname);return fs.existsSync(f)?r.fulfill({contentType:mime[path.extname(f)]||'application/octet-stream',body:fs.readFileSync(f)}):r.fulfill({status:404,body:'not a fixture file'})});await c.route('https://tiles.openfreemap.org/**',r=>r.fulfill({json:{version:8,sources:{},layers:[]}}));}
 await c.route('**/functions/v1/fueldrop*',r=>{if(!['GET','OPTIONS'].includes(r.request().method())){report.backendWrites++;return r.abort()}if(process.env.TARGET)return r.continue();const api=new URL(r.request().url()).searchParams.get('api');return r.fulfill({json:api==='prices'?{ok:true,rows:fixture}:api==='geocode'?{candidates:[]}:{ok:true,launchStates:['QLD','NSW','WA','TAS'],regions:[],configured:false}})});return c;}
async function ready(p){await p.goto(process.env.TARGET||'https://fillmenow.vercel.app/',{waitUntil:'domcontentloaded'});await p.waitForFunction(()=>window.FMNNearbyApp&&window.FMNNearbyUI&&document.getElementById('truckHeight')&&Number(document.getElementById('statCount').textContent)>0)}
async function vehicle(p){await p.locator('.nav[data-page=more]').click();await p.locator('[data-open-panel=vehicle]').click()}
async function run(engine,width,height){const b=await ({chromium,webkit}[engine]).launch({headless:true,...(engine==='chromium'&&process.env.SANDBOX_BROWSER?{args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process','--in-process-gpu','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']}: {})});const result={engine,width,height,checks:[],errors:[]};let a,d,c;try{
 c=await context(b,width,height);a=await c.newPage();d=await c.newPage();for(const p of [a,d]){p.on('pageerror',e=>result.errors.push(e.message));await ready(p)}
 await vehicle(d);await d.locator('#truckModeToggle').check();for(const [id,value]of Object.entries({tankInput:'250',economyInput:'35',truckHeight:'4.2',truckWidth:'2',truckLength:'12',truckWeight:'12'}))await d.locator('#'+id).fill(value);await d.locator('#truckConfiguration').selectOption('rigid');await d.locator('#saveVehicle').click();
 await a.waitForFunction(()=>FMNNearbyApp.getPrefs().vehicle==='truck'&&FMNNearbyApp.getPrefs().tank===250);
 assert.match(await a.locator('#sheetMain').innerText(),/250 L fill/);
 result.checks.push('Saving a250L truck in another same-origin tab updates the older tab and Best Stop without reload');
 await a.evaluate(()=>FMNNearbyApp.applyRadius(20));await d.waitForFunction(()=>JSON.parse(localStorage.getItem('fdPrefs')).tank===250&&JSON.parse(localStorage.getItem('fdPrefs')).radius===20);
 assert.equal(await d.evaluate(()=>FMNNearbyApp.getPrefs().truck.height),4.2);
 result.checks.push('An older tab changing radius cannot overwrite truck dimensions or restore the65L car default');
 await d.reload({waitUntil:'domcontentloaded'});await d.waitForFunction(()=>window.FMNNearbyUI&&document.getElementById('truckHeight'));await vehicle(d);assert.equal(await d.locator('#tankInput').inputValue(),'250');assert.equal(await d.locator('#truckHeight').inputValue(),'4.2');
 await d.locator('#truckModeToggle').uncheck();await d.locator('#truckModeToggle').check();assert.equal(await d.locator('#tankInput').inputValue(),'250');
 await d.locator('#truckHeight').fill('');await d.locator('#drawerBack').click();await d.locator('[data-open-panel=vehicle]').click();assert.equal(await d.locator('#truckHeight').inputValue(),'');await d.locator('#truckHeight').fill('4.2');
 result.checks.push('Reload, Car/Truck switching and unfinished drafts retain the existing behaviour');
 await d.locator('#drawerBack').click();await d.locator('.nav[data-page=explore]').click();await d.screenshot({path:path.join(out,engine+'-'+width+'-restored-profile.png')});
 // Reset only this isolated synthetic browser profile for the missed-event scenario.
 await d.close();await a.evaluate(b=>{localStorage.setItem('fdPrefs',JSON.stringify(b));localStorage.removeItem('fmnVehicleDraft')},base);await ready(a);
 await a.evaluate(t=>localStorage.setItem('fdPrefs',JSON.stringify(t)),truck);
 assert.equal(await a.evaluate(()=>FMNNearbyApp.getPrefs().tank),65);
 await a.evaluate(()=>FMNNearbyApp.applyRadius(20));assert.equal(await a.evaluate(()=>JSON.parse(localStorage.getItem('fdPrefs')).tank),250);assert.equal(await a.evaluate(()=>FMNNearbyApp.getPrefs().vehicle),'truck');
 result.checks.push('Write-time reconciliation also protects a suspended page that missed the storage event');
 assert.equal(await a.evaluate(()=>{const original=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='fdPrefs')throw new DOMException('Test-only storage failure','QuotaExceededError');return original.call(this,k,v)};try{return FMNNearbyApp.saveVehicleQuiet({tank:300})}finally{Storage.prototype.setItem=original}}),false);
 assert.equal(await a.evaluate(()=>JSON.parse(localStorage.getItem('fdPrefs')).tank),250);
 result.checks.push('Storage failure is reported and does not replace the saved250L value');
 assert.deepEqual(result.errors,[]);result.status='PASS';report.runs.push(result);console.log(JSON.stringify(result));
 }catch(e){if(a)await a.screenshot({path:path.join(out,engine+'-'+width+'-failure.png')}).catch(()=>{});throw e}finally{await b.close()}}
(async()=>{const cases=process.env.QUICK?[['chromium',390,844]]:[['chromium',320,740],['chromium',390,844],['webkit',390,844]];for(const args of cases)await run(...args);assert.equal(report.backendWrites,0);report.status='PASS';fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:'PASS',units:report.unitChecks,runs:report.runs.length}))})().catch(e=>{report.status='FAIL';report.error=String(e.stack);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.error(e);process.exitCode=1});
