'use strict';
// Evaluate the real handler and native module with controlled dependencies.
// No database, push service, or production endpoint is contacted by this suite.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {stripTypeScriptTypes}=require('node:module');
const dir='backend/fueldrop',source=fs.readFileSync(dir+'/index.ts','utf8'),native=fs.readFileSync(dir+'/native-push.ts','utf8'),assets=fs.readFileSync(dir+'/legacy-assets.ts','utf8');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const clean=s=>stripTypeScriptTypes(s,{mode:'strip'}).replace(/^import .*;\s*$/gm,'').replace(/^export /gm,'');
new vm.Script(clean(source));new vm.Script(clean(native));new vm.Script(clean(assets));
const tests=[];let outgoingWrites=0;
const fixture={station_id:'TEST-001',station_name:'Fixture only',brand:'BP',suburb:'Sydney',address:'Fixture address',postcode:'2000',latitude:-33.8688,longitude:151.2093,price:199.9,fuel_type:'Diesel',price_date:'2026-10-08',synced_at:'2026-10-08T00:00:00Z',secret:'NOT_PUBLIC',provider_code:'PRIVATE_PROVIDER'};
function harness(mode='normal',withoutGuard=false){
 let handler;const calls=[];
 const env=mode==='no-credentials'?{}:{SUPABASE_URL:'https://database.invalid',SUPABASE_SERVICE_ROLE_KEY:'TEST_ONLY_NOT_A_SECRET'};
 const fetch=async(input,init={})=>{
  const url=new URL(input);calls.push(url.toString());
  assert.equal(url.hostname,'database.invalid','No external network in isolated route tests');
  if((init.method||'GET')!=='GET'){outgoingWrites++;throw Error('Unexpected outgoing write')}
  const response=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json'}});
  if(url.pathname.endsWith('/fuel_data_providers'))return response([]);
  if(url.pathname.endsWith('/fueldrop_private_config'))return response([]);
  if(url.pathname.endsWith('/fuel_price_daily')){
   const dateQuery=url.searchParams.get('select')==='price_date';
   if(mode==='network-error')throw Error('INTERNAL_DATABASE_DETAIL');
   if(mode==='invalid-json')return new Response('{broken');
   if(dateQuery){
    if(mode==='date-error')return response({message:'INTERNAL_DATABASE_DETAIL'},503);
    if(mode==='no-dates')return response([]);
    return response([{price_date:'2026-10-08'}]);
   }
   if(mode==='rows-error')return response({message:'INTERNAL_DATABASE_DETAIL'},500);
   if(mode==='later-page-error')return url.searchParams.get('offset')==='0'?response(Array.from({length:1000},(_,i)=>({...fixture,station_id:'TEST-'+i}))):response({message:'INTERNAL_DATABASE_DETAIL'},500);
   if(mode==='empty')return response([]);
   return response([fixture]);
  }
  if(url.pathname.endsWith('/australia_regions'))return response([{region_name:'Fixture',latitude:-33.8,longitude:151.2}]);
  if(url.pathname.endsWith('/fuel_site_reference'))return response([{suburb:'SYDNEY',postcode:'2000',latitude:-33.8,longitude:151.2}]);
  throw Error('Unexpected mocked path '+url.pathname);
 };
 const globals={Request,Response,Headers,URL,URLSearchParams,TextEncoder,TextDecoder,AbortSignal,Uint8Array,crypto:crypto.webcrypto,btoa,atob,console,fetch,Deno:{env:{get:n=>env[n]},serve:fn=>{handler=fn},createHttpClient:()=>{throw Error('No real push clients in tests')}}};
 const nc=vm.createContext({...globals});new vm.Script(clean(native)).runInContext(nc);
 const ctx=vm.createContext({...globals,nativePushAPI:nc.nativePushAPI,sendNativePushes:nc.sendNativePushes,mergePushRuns:nc.mergePushRuns,webpush:{}});
 new vm.Script(clean(assets)).runInContext(ctx);
 let code=clean(source);
 if(withoutGuard)code=code.replace(/if\(payload\?\.connected!==true\|\|payload\?\.error\|\|!Array\.isArray\(payload\?\.rows\)\)throw new Error\("price_unavailable"\);/,'');
 new vm.Script(code).runInContext(ctx);assert.equal(typeof handler,'function');
 return {handler,ctx,nc,calls};
}
async function invoke(h,query='',method='GET'){return h.handler(new Request('https://edge.invalid/functions/v1/fueldrop'+query,{method}))}
async function check(name,fn){await fn();tests.push(name)}
(async()=>{
 await check('Before-fix control reproduces masked empty success',async()=>{const r=await invoke(harness('rows-error',true),'?api=prices');assert.equal(r.status,200);assert.equal((await r.json()).ok,true)});
 for(const mode of ['no-credentials','date-error','rows-error','network-error','invalid-json','later-page-error'])await check(mode+' returns sanitised HTTP 500, not successful empty data',async()=>{
  const r=await invoke(harness(mode),'?api=prices&state=NSW&fuel=Diesel');assert.equal(r.status,500);assert.equal(r.headers.get('cache-control'),'no-store');assert.equal(r.headers.get('access-control-allow-origin'),'*');assert.deepEqual(await r.json(),{ok:false,rows:[],error:'price_unavailable'});
 });
 for(const mode of ['no-dates','empty'])await check(mode+' remains a genuine successful empty result',async()=>{const r=await invoke(harness(mode),'?api=prices');assert.equal(r.status,200);const j=await r.json();assert.equal(j.ok,true);assert.equal(j.rows.length,0)});
 for(const state of ['NSW','WA','TAS'])await check(state+' keeps whitelisted station data, geographic filters and real navigation coordinates',async()=>{
  const h=harness(),r=await invoke(h,'?api=prices&state='+state+'&fuel=Diesel&lat=-33.8688&lng=151.2093&radius=25');assert.equal(r.status,200);const j=await r.json();assert.equal(j.ok,true);assert.equal(j.state_code,state);assert.equal(j.rows[0].latitude,fixture.latitude);assert.equal(j.rows[0].longitude,fixture.longitude);assert.equal(j.rows[0].brand,'BP');assert.equal(j.rows[0].price,199.9);assert.ok(!JSON.stringify(j).includes('NOT_PUBLIC'));assert.ok(!JSON.stringify(j).includes('PRIVATE_PROVIDER'));assert.ok(h.calls.some(u=>u.includes('latitude=gte.')&&u.includes('state_code=eq.'+state)));
 });
 await check('OPTIONS preflight unchanged',async()=>{const r=await invoke(harness(),'', 'OPTIONS');assert.equal(r.status,204)});
 for(const api of ['send-price-drops','send-daily','sync-reference','sync-wa','sync'])await check(api+' still rejects unauthenticated requests before any writes',async()=>{const h=harness(),r=await invoke(h,'?api='+api);assert.equal(r.status,401);assert.deepEqual(await r.json(),{ok:false,error:'unauthorized'});assert.equal(h.calls.length,0)});
 for(const api of ['subscribe','unsubscribe','native-subscribe','native-unsubscribe'])await check(api+' preserves method guard',async()=>{const r=await invoke(harness(),'?api='+api);assert.equal(r.status,405)});
 await check('Native push remains disabled when Apple credentials are absent',async()=>{const r=await invoke(harness(),'?api=native-push-status');assert.deepEqual(await r.json(),{ok:true,configured:false})});
 await check('Status and launch states preserved',async()=>{const r=await invoke(harness(),'?api=status');assert.deepEqual(await r.json(),{ok:true,launchStates:['NSW','WA','TAS'],pushConfigured:false})});
 await check('Public push key reports unconfigured correctly in fixture',async()=>{const r=await invoke(harness(),'?api=push-public-key');assert.equal(r.status,503)});
 await check('Region lookup still returns expected envelope',async()=>{const r=await invoke(harness(),'?api=regions&state=WA');assert.equal(r.status,200);const j=await r.json();assert.equal(j.state,'WA');assert.equal(j.regions.length,1)});
 await check('Suburb lookup preserves public coordinate envelope',async()=>{const r=await invoke(harness(),'?api=geocode&state=NSW&q=sydney');assert.equal(r.status,200);const j=await r.json();assert.equal(j.candidates.length,1);assert.equal(j.candidates[0].state,'NSW');assert.ok(!('source' in j.candidates[0]))});
 const hashes=[['','215e2fb824b1546ee3904cddbcbf1b6c1865b8ba48c462ea535c135639157e3d'],['?asset=icon','cc9fce6903f6f88ea105fca1293228dbe9b0da27e75cede5bb111720751b0ce7'],['?asset=manifest','06a5f3897adc6cca79e84a270f451ec345d72cdf815b9c02b14d880fa4088f10'],['?asset=sw','f7bc4a6286f47d9226786e70735f45087424dbb81ea08307980b5357c2494113'],['?asset=standalone','ddb6875215c9966a73603a3d13158c8275f4113f1b42d3762d30ad20423f99d5']];
 for(const [query,digest]of hashes)await check('Existing legacy response '+(query||'HTML')+' is byte-identical',async()=>{const r=await invoke(harness(),query);assert.equal(r.status,200);assert.equal(sha(Buffer.from(await r.arrayBuffer())),digest)});
 await check('Native Off ignores stale threshold',async()=>{const n=harness().nc;const result=n.nativeSettings({latitude:-33,longitude:151,state_code:'NSW',fuel_type:'Diesel',notification_frequency:'off',radius_km:25,tank_litres:65,economy_l_per_100km:9,notify_time:'06:00',notify_time_2:'15:30',price_drop_threshold:200});assert.equal(result.active,false);assert.equal(result.price_drop_threshold,null)});
 await check('No outgoing database or notification writes attempted',async()=>assert.equal(outgoingWrites,0));
 const report={status:'PASS',passed:tests.length,tests,sourceSha256:sha(source),nativeSha256:sha(native),legacySha256:sha(assets),network:'isolated mocks only',outgoingWrites,productionDeployed:false};
 fs.mkdirSync('qa-results/backend',{recursive:true});fs.writeFileSync('qa-results/backend/route-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1});
