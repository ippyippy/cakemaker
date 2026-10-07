'use strict';
// Deterministic UI tests only: every backend request is intercepted; no subscriptions or production writes.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium,webkit}=require('playwright');const AxeBuilder=require('@axe-core/playwright').default;
const root=path.resolve('web'),out=path.resolve('qa-results/recovery');fs.mkdirSync(out,{recursive:true});
const fixture=JSON.parse(fs.readFileSync('qa-results/polish/fuel-fixture.json','utf8'));
const report={testedAt:new Date().toISOString(),scope:'Local current web source; intercepted fixture data and simulated failures; no backend writes',cases:[],failures:[]};
const server=http.createServer((req,res)=>{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403);return res.end()}if(file===root)file=path.join(root,'index.html');if(!fs.existsSync(file)&&!path.extname(file))file+='.html';if(!fs.existsSync(file)){res.writeHead(404);return res.end()}const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.webmanifest':'application/manifest+json','.svg':'image/svg+xml','.png':'image/png'};res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res)});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function run(type,width){const name=type===webkit?'webkit':'chromium',height=width===320?740:width===390?844:900;let browser;const result={browser:name,width,height,checks:[],pageErrors:[],accessibility:{}};
try{
 browser=await type.launch(type===chromium?{headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']}:{headless:true});
 const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,hasTouch:width<1025,isMobile:width<601,serviceWorkers:'block',ignoreHTTPSErrors:true});
 await context.addInitScript(()=>{localStorage.setItem('fmnOnboarded','1');localStorage.setItem('fdPrefs',JSON.stringify({state:'NSW',fuel:'Diesel',radius:20,alertRadius:20,tank:65,economy:9,vehicle:'car',frequency:'daily',time1:'06:00',time2:'15:30',threshold:''}))});
 let regionsMode='race',searchMode='normal',pricesMode='normal',regionHits=0,searchHits=0;
 await context.route('**/functions/v1/fueldrop*',async route=>{
  const request=route.request(),u=new URL(request.url()),api=u.searchParams.get('api'),state=u.searchParams.get('state');
  if(request.method()!=='GET')return route.fulfill({status:503,json:{ok:false,error:'QA blocks writes'}});
  const response={status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*','cache-control':'no-store'}};
  let body={ok:true,configured:false};
  if(api==='regions'){
   regionHits++;const mode=regionsMode;
   if(mode==='race')await wait(state==='NSW'?750:30);
   if(mode==='error'){response.status=503;body={error:'regions_failed',regions:[]}}
   else if(mode==='empty')body={regions:[]};
   else body={regions:[{region_name:state==='WA'?'Perth':'Sydney',latitude:state==='WA'?-31.9523:-33.8688,longitude:state==='WA'?115.8613:151.2093}]};
  }else if(api==='geocode'){
   searchHits++;const mode=searchMode;
   if(mode==='slow')await wait(500);
   if(mode==='error'){response.status=503;body={error:'geocode_failed'}}
   else if(mode==='empty')body={candidates:[]};
   else body={candidates:[{label:state==='WA'?'Perth WA 6000':'Sydney NSW 2000',state,suburb:state==='WA'?'Perth':'Sydney',postcode:state==='WA'?'6000':'2000',lat:state==='WA'?-31.9523:-33.8688,lng:state==='WA'?115.8613:151.2093}]};
  }else if(api==='prices'){
   if(pricesMode==='error'){response.status=503;body={ok:false,rows:[],error:'price_unavailable'}}
   else body=pricesMode==='empty'?{ok:true,rows:[],price_date:fixture.price_date}:fixture;
  }
  try{await route.fulfill({...response,body:JSON.stringify(body)})}catch(e){if(!/closed|handled|cancel/i.test(String(e)))throw e}
 });
 const page=await context.newPage();page.setDefaultTimeout(10000);page.on('pageerror',e=>result.pageErrors.push(e.message));
 await page.goto('http://127.0.0.1:8772/',{waitUntil:'domcontentloaded'});
 for(let i=0;i<100&&!regionHits;i++)await wait(10);assert.ok(regionHits>0);
 await page.locator('#stateSelect').selectOption('WA');
 await page.waitForFunction(()=>document.querySelector('#regions').textContent.includes('Perth'));
 await page.waitForTimeout(850);
 assert.equal(await page.locator('#regions .region').innerText(),'Perth');assert.equal(await page.locator('#regions').getAttribute('aria-busy'),null);
 await page.locator('#regions .region').click();
 const chosen=await page.evaluate(()=>JSON.parse(localStorage.getItem('fdLoc')));assert.equal(chosen.state,'WA');assert.equal(chosen.lat,-31.9523);assert.equal(chosen.label,'Perth WA');
 result.checks.push('Delayed NSW regions cannot replace WA choices or save wrong-state coordinates');
 regionsMode='normal';await page.evaluate(()=>FD.area());await page.locator('#stateSelect').selectOption('NSW');await page.locator('#regions .region').filter({hasText:'Sydney'}).click();
 await page.waitForFunction(()=>Number(document.querySelector('#statCount').textContent)>0);
 pricesMode='error';await page.evaluate(()=>FD.refresh());await page.evaluate(()=>FD.options());await page.locator('#optionsRetry').waitFor();
 result.errorTextSize=await page.locator('#optionsList .empty').evaluate(el=>parseFloat(getComputedStyle(el).fontSize));
 assert.ok(result.errorTextSize>=14,'Unavailable-result messages must use at least 14px text');
 const buttons=await page.locator('#optionsList .empty-actions button').evaluateAll(elements=>elements.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}}));
 assert.equal(buttons.length,2);buttons.forEach(b=>assert.ok(b.h>=44&&b.w>=44));assert.ok(buttons[0].right<=buttons[1].x||buttons[0].bottom<=buttons[1].y||buttons[1].bottom<=buttons[0].y,'Recovery buttons do not overlap');
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 result.accessibility.priceError=(await new AxeBuilder({page}).include('#optionsList').analyze()).violations.map(v=>({id:v.id,count:v.nodes.length}));assert.equal(result.accessibility.priceError.length,0);
 await page.screenshot({path:path.join(out,`${name}-${width}-price-retry.png`),animations:'disabled'});
 pricesMode='normal';await page.locator('#optionsRetry').click();await page.waitForFunction(()=>document.querySelectorAll('.option-row').length>0);assert.equal(await page.locator('#optionsRetry').count(),0);
 result.checks.push('Failed price requests expose readable non-overlapping retry/area buttons; a real retry click restores results');
 pricesMode='empty';await page.evaluate(()=>FD.refresh());await page.locator('#optionsWiden').waitFor();assert.match(await page.locator('#optionsList').innerText(),/No stations found/);
 result.emptyTextSize=await page.locator('#optionsList .empty').evaluate(el=>parseFloat(getComputedStyle(el).fontSize));assert.ok(result.emptyTextSize>=14,'Empty-result messages must use at least 14px text');
 pricesMode='normal';await page.locator('#optionsWiden').click();await page.waitForFunction(()=>document.querySelectorAll('.option-row').length>0);
 const settings=await page.evaluate(()=>JSON.parse(localStorage.getItem('fdPrefs')));assert.equal(settings.radius,30);assert.equal(settings.alertRadius,20);
 result.checks.push('Empty results offer a wider search without changing the alert radius');
 await page.evaluate(()=>FD.area());searchMode='empty';await page.locator('#locationSearch').fill('nowhere');await page.waitForFunction(()=>document.querySelector('#suggestions').textContent.includes('No matching suburbs'));
 assert.equal(await page.locator('#suggestions .suggestion').count(),0);assert.equal(await page.locator('#suggestions').getAttribute('aria-busy'),null);
 await page.screenshot({path:path.join(out,`${name}-${width}-search-empty.png`),animations:'disabled'});
 searchMode='error';await page.locator('#locationSearch').fill('syd');await page.locator('#suggestions .location-feedback button').waitFor();
 result.accessibility.locationError=(await new AxeBuilder({page}).include('#areaModal').analyze()).violations.map(v=>({id:v.id,count:v.nodes.length}));assert.equal(result.accessibility.locationError.length,0);
 searchMode='normal';await page.locator('#suggestions .location-feedback button').click();await page.locator('#suggestions .suggestion').waitFor();assert.match(await page.locator('#suggestions').innerText(),/Sydney NSW/);
 await page.locator('#locationSearch').fill('');assert.equal(await page.locator('#suggestions .suggestion').count(),0);await page.waitForTimeout(250);assert.equal(await page.locator('#suggestions').innerText(),'');
 result.checks.push('No-match searches have an explanation; failed searches retry successfully; clearing input removes stale choices immediately');
 searchMode='slow';const hits=searchHits;await page.locator('#locationSearch').fill('syd');for(let i=0;i<100&&searchHits===hits;i++)await wait(10);assert.ok(searchHits>hits);
 await page.locator('#stateSelect').selectOption('WA');await page.waitForTimeout(650);assert.equal(await page.locator('#locationSearch').inputValue(),'');assert.equal(await page.locator('#suggestions').innerText(),'');assert.equal(await page.locator('#regions .region').innerText(),'Perth');
 result.checks.push('Changing state cancels an in-flight suburb search and clears its previous text and suggestions');
 regionsMode='error';await page.locator('#stateSelect').selectOption('NSW');await page.locator('#regions .location-feedback button').waitFor();
 await page.screenshot({path:path.join(out,`${name}-${width}-region-retry.png`),animations:'disabled'});
 regionsMode='normal';await page.locator('#regions .location-feedback button').click();await page.locator('#regions .region').waitFor();assert.equal(await page.locator('#regions .region').innerText(),'Sydney');
 regionsMode='empty';await page.locator('#stateSelect').selectOption('WA');await page.waitForFunction(()=>document.querySelector('#regions').textContent.includes('No popular areas available'));
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.equal(result.pageErrors.length,0);
 result.checks.push('Popular-area failures and empty lists have visible guidance and working retry, without stale buttons');
 result.passed=true;
}catch(e){result.passed=false;result.failure=e.stack;report.failures.push(`${name} ${width}: ${e.message}`)}finally{if(browser)await browser.close();report.cases.push(result);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(result))}}
(async()=>{await new Promise(resolve=>server.listen(8772,'127.0.0.1',resolve));for(const type of [chromium,webkit])for(const width of [320,390,1440])await run(type,width);server.close();if(report.failures.length)process.exitCode=1})().catch(e=>{console.error(e);server.close();process.exitCode=1});
