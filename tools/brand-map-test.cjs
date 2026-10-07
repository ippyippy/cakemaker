'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),vm=require('vm');
const {chromium,webkit}=require('playwright');
const root=path.resolve('web'),out=path.resolve('qa-brand-map');fs.mkdirSync(out,{recursive:true});
const source=fs.readFileSync(path.join(root,'index.html'),'utf8');
for(const m of source.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi))new vm.Script(m[1]);
new vm.Script(fs.readFileSync(path.join(root,'sw.js'),'utf8'));
const assets=JSON.parse(fs.readFileSync(path.join(root,'assets/brands/sources.json'))).assets;
assets.forEach(a=>assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'assets/brands',a.file))).digest('hex'),a.sha256));
const fixtures=['BP','Shell','Caltex','Ampol','7-Eleven','United','Metro','Liberty','Puma','Reddy Express'].map((brand,i)=>({station_id:'BRAND-'+i,station_name:brand+' Test Station',brand,suburb:'Sydney',address:'Test fixture only',latitude:-33.8688,longitude:151.2093,price:179.9+i,fuel_type:'Diesel',price_date:new Date().toISOString().slice(0,10),synced_at:new Date().toISOString()}));
fixtures.push({ ...fixtures[0],station_id:'OUTSIDE',station_name:'Outside viewport',latitude:-33.75,longitude:151.3});
// Instrument a test-only copy. No debug globals are committed in web/index.html.
const html=source.replace('map=new maplibregl.Map({','map=window.__qaMap=new maplibregl.Map({').replace('window.FD={','window.__qaBrandMark=brandMark;window.__qaBrandKey=brandKey;window.FD={');
const MIME={'.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.json':'application/json','.webmanifest':'application/manifest+json'};
const report={assets:assets.length,fixtureDescription:'Synthetic co-located stations test fan-out. Not real fuel-price claims.',runs:[]};
const flags=process.env.SANDBOX_BROWSER==='1'?['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process','--in-process-gpu','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']:['--no-sandbox','--enable-unsafe-swiftshader'];
(async()=>{
 const matrix=process.env.QUICK==='1'?[['chromium',390,844]]:[['chromium',320,740],['chromium',390,844],['chromium',768,1024],['chromium',1440,900],['webkit',390,844],['webkit',1440,900]];
 for(const [engine,width,height] of matrix){
  const browser=await ({chromium,webkit}[engine]).launch({headless:true,...(engine==='chromium'?{args:flags}:{})});
  try{
   const context=await browser.newContext({viewport:{width,height},hasTouch:width<1025,isMobile:width<600,serviceWorkers:'block',ignoreHTTPSErrors:true});
   await context.route('https://fillmenow.vercel.app/**',async r=>{const u=new URL(r.request().url()),rel=u.pathname==='/'?'index.html':u.pathname.slice(1);const file=path.resolve(root,rel);assert.ok(file.startsWith(root+path.sep));if(!fs.existsSync(file))return r.fulfill({status:404,body:'not found'});return r.fulfill({status:200,contentType:MIME[path.extname(file)]||'application/octet-stream',body:rel==='index.html'?html:fs.readFileSync(file)})});
   await context.route('**/functions/v1/fueldrop*',r=>{assert.equal(r.request().method(),'GET','No backend writes allowed');const api=new URL(r.request().url()).searchParams.get('api');return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(api==='prices'?{ok:true,rows:fixtures,price_date:new Date().toISOString().slice(0,10),snapshot_synced_at:new Date().toISOString()}:{ok:true,configured:false,regions:[],candidates:[]})})});
   await context.addInitScript(()=>{localStorage.setItem('fmnOnboarded','1');localStorage.setItem('fdLoc',JSON.stringify({lat:-33.8688,lng:151.2093,label:'Sydney NSW',state:'NSW'}));localStorage.setItem('fdPrefs',JSON.stringify({state:'NSW',fuel:'Diesel',radius:20,alertRadius:25,tank:65,economy:9,vehicle:'car',frequency:'off',time1:'06:00',time2:'15:30',threshold:''}));window.open=u=>{window.__qaNavigation=u;return null}});
   const page=await context.newPage();page.setDefaultTimeout(12000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto('https://fillmenow.vercel.app/',{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>window.__qaMap&&Number(document.querySelector('#statCount').textContent)>=10);
   if(width<1025){await page.evaluate(()=>FD.sheet());await page.waitForTimeout(400);assert.ok(await page.locator('#mobileSheet').evaluate(e=>e.classList.contains('is-collapsed')))}
   const result={engine,width,height,zooms:[],logosLoaded:0,checks:[]};
   for(const zoom of [10,11.2,12,14,18]){
    await page.evaluate(z=>window.__qaMap.jumpTo({center:[151.2093,-33.8688],zoom:z}),zoom);await page.waitForTimeout(160);
    const state=await page.evaluate(rows=>{const map=window.__qaMap,host=document.querySelector('#exploreMap'),w=host.clientWidth,h=host.clientHeight;
     const expected=rows.filter(x=>{const q=map.project([x.longitude,x.latitude]);return q.x>=0&&q.y>=0&&q.x<=w&&q.y<=h}).map(x=>x.station_id).sort();
     const nodes=[...document.querySelectorAll('#exploreMap .station-pin')];const boxes=nodes.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}});let collisions=0;
     boxes.forEach((a,i)=>boxes.slice(i+1).forEach(b=>{if(a.left<b.right-1&&a.right>b.left+1&&a.top<b.bottom-1&&a.bottom>b.top+1)collisions++}));
     return {expected,actual:nodes.map(e=>e.dataset.stationId).sort(),clusters:host.querySelectorAll('.station-cluster').length,hidden:nodes.filter(e=>getComputedStyle(e).visibility==='hidden'||e.tabIndex<0).length,collisions,layout:host.dataset.pinLayout,priceVisible:nodes.every(e=>getComputedStyle(e.querySelector('.pin-price')).display!=='none')};
    },fixtures);
    assert.deepEqual(state.actual,state.expected);assert.equal(state.clusters,0);assert.equal(state.hidden,0);assert.equal(state.collisions,0);if(zoom>=12)assert.equal(state.priceVisible,true);result.zooms.push({zoom,count:state.actual.length,collisions:state.collisions});
   }
   await page.waitForFunction(()=>[...document.querySelectorAll('#exploreMap .official-brand img')].every(i=>i.complete&&i.naturalWidth>0));
   result.logosLoaded=await page.locator('#exploreMap .official-brand img').count();assert.equal(result.logosLoaded,10);
   assert.equal(await page.evaluate(()=>__qaBrandKey('Caltex','Former Ampol Shell station')),'caltex');assert.equal(await page.evaluate(()=>__qaBrandKey('Shell','Shell Reddy Express')),'shell');
   await page.screenshot({path:path.join(out,`${engine}-${width}-individual.png`)});
   // Actual pointer selection, not a synthetic call to the station-opening function.
   for(const i of [0,1,2]){
    await page.locator(`[data-station-id="BRAND-${i}"]`).click();const title=width>=1025?'#desktopStationTitle':'#stationTitle';assert.ok((await page.locator(title).innerText()).includes(fixtures[i].brand));await page.keyboard.press('Escape');
   }
   await page.evaluate(()=>FD.nav('BRAND-2'));assert.ok((await page.evaluate(()=>window.__qaNavigation)).includes(encodeURIComponent('-33.8688,151.2093')));
   if(width<1025){await page.locator('#sheetPeek').click();assert.equal(await page.locator('#mobileSheet').evaluate(e=>e.classList.contains('is-collapsed')),false);await page.evaluate(()=>FD.sheet());await page.waitForTimeout(320)}
   await page.evaluate(()=>FD.options());assert.equal(await page.locator('.option-row').count(),fixtures.length);
   for(const screen of ['saved','alerts','more','explore'])await page.locator(`.nav[data-page="${screen}"]`).click();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   result.checks.push('all in-view stations individually selectable','ten real logos decode','no grouped or hidden pins','shared coordinates fan out without collisions','brand field wins over historic station names','navigation retains real coordinates','Dash and navigation regressions');
   // Pan: pins for newly visible stations are rebuilt, not limited to the cheapest subset.
   await page.evaluate(()=>window.__qaMap.jumpTo({center:[151.3,-33.75],zoom:18}));await page.waitForTimeout(200);assert.equal(await page.locator('[data-station-id="OUTSIDE"]').count(),1);
   result.checks.push('panning reveals newly visible stations');assert.deepEqual(errors,[]);result.errors=errors;result.status='PASS';report.runs.push(result);console.log(JSON.stringify(result));
   if(engine==='chromium'&&width===390){
    await page.evaluate(list=>{const gallery=document.createElement('div');gallery.id='qaLogoGallery';gallery.style='position:fixed;inset:0;background:white;z-index:10000;display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:20px;align-content:start';list.forEach(brand=>{let row=document.createElement('div');row.style='display:flex;flex-direction:column;align-items:center;gap:8px;padding:14px;border:1px solid #ddd';row.innerHTML=window.__qaBrandMark(brand,brand)+'<b>'+brand+'</b>';row.querySelector('.brand-mark').style='width:80px;height:60px';gallery.appendChild(row)});document.body.appendChild(gallery)},fixtures.slice(0,10).map(x=>x.brand));await page.waitForTimeout(250);await page.screenshot({path:path.join(out,'retailer-logos.png')});
   }
  }finally{await browser.close()}
 }
 report.status='PASS';fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));fs.cpSync(root,path.join(out,'reviewed-web'),{recursive:true});
})().catch(e=>{report.status='FAIL';report.error=String(e.stack||e);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.error(e);process.exitCode=1});
