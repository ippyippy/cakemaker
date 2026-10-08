'use strict';
// Every request below is an isolated fixture. No network, secrets or production writes.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {stripTypeScriptTypes}=require('node:module');
const source=fs.readFileSync('backend/fueldrop/index.ts','utf8');
const tests=[];
const fuels=[
 [2,'Unleaded','U91'],[3,'Diesel','Diesel'],[4,'LPG',null],
 [5,'Premium Unleaded 95','U95'],[6,'ULSD','ULSD'],[8,'Premium Unleaded 98','U98'],
 [11,'LRP',null],[12,'e10','E10'],[13,'Premium e5',null],[14,'Premium Diesel','Premium Diesel'],
 [16,'Bio-Diesel 20',null],[19,'e85',null],[21,'OPAL',null],
 [22,'Compressed natural gas',null],[23,'Liquefied natural gas',null],
 [999,'e10/Unleaded',null],[1000,'Diesel/Premium Diesel',null]
];
const site={station_id:'QLD-FIXTURE-1',station_name:'Fixture only',brand:'BP',suburb:'Brisbane',address:'Test fixture',postcode:'4000',latitude:-27.4698,longitude:153.0251};
let requested=[],prices=[],handler;
const response=data=>new Response(JSON.stringify(data),{headers:{'content-type':'application/json'}});
const c={console,Intl,Date,Math,JSON,Map,Set,Number,String,Boolean,Array,Uint8Array,TextEncoder,TextDecoder,Response,Request,URL,AbortSignal,crypto:crypto.webcrypto,
 Deno:{env:{get:k=>({SUPABASE_URL:'https://database.invalid',SUPABASE_SERVICE_ROLE_KEY:'FIXTURE_ONLY',QLD_FUEL_API_TOKEN:'FIXTURE_ONLY'})[k]},serve:fn=>{handler=fn}},
 fetch:async(u,init={})=>{
  const url=new URL(u);assert.ok(['database.invalid','fppdirectapi-prod.fuelpricesqld.com.au'].includes(url.hostname),'Unexpected fixture destination');requested.push({url,init});
  if(url.hostname==='fppdirectapi-prod.fuelpricesqld.com.au'){assert.ok(url.pathname.endsWith('/GetSitesPrices'));return response({SitePrices:prices});}
  if((init.method||'GET')!=='GET')return response([]);
  if(url.pathname.endsWith('fuel_type_reference'))return response(fuels.map(([id,name,type])=>({fuel_id:id,name,app_fuel_type:id===16?'Diesel':id===6?null:type})));
  if(url.pathname.endsWith('fuel_site_reference')){assert.equal(url.searchParams.get('state_code'),'eq.QLD');assert.equal(url.searchParams.get('provider_code'),'eq.qld-fpqld');return response([site]);}
  if(url.pathname.endsWith('fuel_data_providers'))return response([]);
  if(url.pathname.endsWith('fuel_price_daily'))return response(url.searchParams.get('select')==='price_date'?[{price_date:'2026-10-09'}]:[]);
  if(url.pathname.endsWith('fueldrop_private_config'))return response([]);
  throw Error('Unexpected fixture read: '+url.pathname);
 }
};
vm.createContext(c);vm.runInContext(stripTypeScriptTypes(source).replace(/^import .*;\s*$/gm,''),c);
function check(name,fn){fn();tests.push(name)}
const ref={fuels:new Map(fuels.map(([id,,type])=>[id,type||''])),sites:new Map([[site.station_id,site]])};
const row=(fuel,price,extra={})=>({SiteId:site.station_id,FuelId:fuel,Price:price,...extra});
const prepare=rows=>c.queenslandPriceRows(rows,ref,'2026-10-09','2026-10-09T00:00:00Z');
(async()=>{
 for(const [,name,type] of fuels)check('Exact mapping: '+name,()=>assert.equal(c.appFuelName(name),type));
 check('Case and whitespace normalized',()=>assert.equal(c.appFuelName('  PREMIUM   DIESEL '),'Premium Diesel'));
 check('Unsupported unknown grade cannot masquerade as fuel',()=>{assert.equal(c.appFuelName('__proto__'),null);assert.equal(c.appFuelName('special 95 biodiesel'),null)});
 const refs=await c.loadQueenslandReference();check('Stale reference mappings do not relabel B20 or exclude ULSD',()=>{assert.equal(refs.fuels.get(16),'');assert.equal(refs.fuels.get(6),'ULSD')});
 check('ULSD is retained as its actual labelled grade',()=>{const a=prepare([row(6,1759)]);assert.equal(a[0].fuel_type,'ULSD');assert.equal(a[0].price,175.9)});
 check('B20 and aggregate fuel selections are excluded',()=>{const a=prepare([row(16,999),row(1000,1599),row(999,1499),row(3,1819)]);assert.equal(a.length,1);assert.equal(a[0].fuel_type,'Diesel')});
 check('All seven supported source grades remain distinct',()=>{const a=prepare([2,3,5,6,8,12,14].map((id,i)=>row(id,1700+i)));assert.equal(a.length,7);assert.equal(new Set(a.map(x=>x.fuel_type)).size,7)});
 check('Unavailable, absent, invalid and non-positive prices excluded',()=>{const a=prepare([row(3,9999),row(3,null),row(3,-10),row(3,'oops'),row(3,0),row(3,''),row(14,1859)]);assert.equal(a.length,1);assert.equal(a[0].price,185.9)});
 check('Exact provider coordinates and Queensland scope retained',()=>{const a=prepare([row(3,1819)])[0];assert.equal(a.latitude,site.latitude);assert.equal(a.longitude,site.longitude);assert.equal(a.state_code,'QLD');assert.equal(a.provider_code,'qld-fpqld')});
 check('Unknown sites and invalid coordinates never create pins',()=>{ref.sites.set('invalid',{...site,latitude:0,longitude:0});const a=prepare([row(3,1819),row(3,1000,{SiteId:'unknown'}),row(3,1000,{SiteId:'invalid'})]);assert.equal(a.length,1)});
 check('UTC timestamps without suffix normalized correctly',()=>{const a=prepare([row(3,1819,{TransactionDateUtc:'2026-10-09T01:00:00'})]);assert.equal(a[0].transaction_date_utc,'2026-10-09T01:00:00.000Z')});
 check('Identical duplicate records are deduplicated',()=>assert.equal(prepare([row(3,1819),row(3,1819)]).length,1));
 check('Newest duplicate wins, not artificially cheapest',()=>{const a=prepare([row(3,1800,{TransactionDateUtc:'2026-10-09T01:00:00'}),row(3,1900,{TransactionDateUtc:'2026-10-09T02:00:00'})]);assert.equal(a.length,1);assert.equal(a[0].price,190)});
 check('Ambiguous conflicting duplicates reject whole snapshot',()=>assert.throws(()=>prepare([row(3,1800),row(3,1900)]),/qld_conflicting_price_rows/));
 check('Conflicting equal-time prices reject whole snapshot',()=>assert.throws(()=>prepare([row(3,1800,{TransactionDateUtc:'2026-10-09T01:00:00'}),row(3,1900,{TransactionDateUtc:'2026-10-09T01:00:00'})]),/qld_conflicting_price_rows/));
 check('Malformed timestamp rejects whole snapshot',()=>assert.throws(()=>prepare([row(3,1800,{TransactionDateUtc:'not-a-time'})]),/qld_invalid_price_timestamp/));
 check('Empty snapshot cannot erase data',()=>assert.throws(()=>prepare([]),/qld_empty_price_snapshot/));
 prices=[row(3,1819),row(3,1819),row(6,1799),row(16,1500)];requested=[];const result=await c.syncQueenslandFuel();
 check('Full mocked importer writes distinct correct grades',()=>{assert.equal(result.rowsWritten,2);const w=requested.find(x=>x.init.method==='POST'&&x.url.pathname.endsWith('fuel_price_daily'));assert.ok(w);assert.equal(JSON.parse(w.init.body).length,2)});
 check('Cleanup limited to Queensland/provider/date',()=>{const d=requested.find(x=>x.init.method==='DELETE');assert.ok(d);assert.equal(d.url.searchParams.get('state_code'),'eq.QLD');assert.equal(d.url.searchParams.get('provider_code'),'eq.qld-fpqld');assert.ok(d.url.searchParams.has('price_date'))});
 requested=[];prices=[row(3,1800),row(3,1900)];await assert.rejects(()=>c.syncQueenslandFuel(),/qld_conflicting_price_rows/);check('Conflict makes zero outgoing data writes',()=>assert.equal(requested.filter(x=>(x.init.method||'GET')!=='GET').length,0));
 for(const state of ['QLD','NSW','WA','TAS']){requested=[];await c.latestFuelRows('Diesel',state,-27.4698,153.0251,20);const q=requested.find(x=>x.url.pathname.endsWith('fuel_price_daily'));check('Diesel comparison scope: '+state,()=>assert.equal(q.url.searchParams.get('fuel_type'),state==='QLD'?'in.(Diesel,Premium Diesel,ULSD)':'in.(Diesel,Premium Diesel)'));}
 requested=[];const denied=await handler(new Request('https://app.invalid/?api=sync',{method:'POST'}));check('Sync still requires administrative authentication',()=>assert.equal(denied.status,401));
 const out={status:'PASS',tests,checkCount:tests.length,network:'isolated fixtures only',productionImportPerformed:false,sourceSha256:crypto.createHash('sha256').update(source).digest('hex')};
 fs.mkdirSync('qa-results/qld-grade-guard',{recursive:true});fs.writeFileSync('qa-results/qld-grade-guard/report.json',JSON.stringify(out,null,2));console.log(JSON.stringify({status:out.status,checks:out.checkCount,productionImportPerformed:false}));
})().catch(e=>{console.error(e);process.exitCode=1});
