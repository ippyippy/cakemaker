'use strict';
// Patch only the existing publicPricePayload guard. Preserve its field whitelist,
// routes, authentication, native push, feeds and embedded assets byte-for-byte.
const fs=require('fs'),assert=require('assert/strict'),vm=require('vm');
const marker='function publicPricePayload(payload:any){';
const guard='\n // FMN_PRICE_FAILURE_GUARD_20261007: a failed read is not an empty search.\n if(payload?.connected!==true||payload?.error||!Array.isArray(payload?.rows))throw new Error("price_unavailable");';
function patch(source){
 if(source.includes('FMN_PRICE_FAILURE_GUARD_20261007'))return source;
 assert.equal(source.split(marker).length,2,'Expected exactly one publicPricePayload function');
 assert.ok(source.includes('json({ok:false,rows:[],error:"price_unavailable"},500)'),'Existing sanitised route catch is required');
 const result=source.replace(marker,marker+guard);
 assert.equal(result.replace(guard,''),source,'Only the guarded insertion is allowed');
 return result;
}
const fixture=`function publicPricePayload(payload:any){
 const rows=(Array.isArray(payload?.rows)?payload.rows:[]).map((x:any)=>({station_id:x.station_id,station_name:x.station_name,brand:x.brand||null,suburb:x.suburb||null,address:x.address||"",postcode:x.postcode||null,latitude:x.latitude,longitude:x.longitude,price:x.price,fuel_type:x.fuel_type,price_date:x.price_date,transaction_date_utc:x.transaction_date_utc,synced_at:x.synced_at}));
 return {ok:true,rows,price_date:payload?.price_date||null,snapshot_synced_at:payload?.snapshot_synced_at||null,state_code:payload?.state_code||null};
}
// Existing outer catch: json({ok:false,rows:[],error:"price_unavailable"},500)
`;
let source=fixture;
if(process.argv[2])source=fs.readFileSync(process.argv[2],'utf8');
const repaired=patch(source);
const start=repaired.indexOf(marker),end=repaired.indexOf('\nasync function isAdminRequest',start);
let fn=end<0?repaired.slice(start):repaired.slice(start,end);
fn=fn.replace(/:any\b/g,'');
const context={};vm.createContext(context);vm.runInContext(fn,context);
function response(payload){try{return {status:200,body:context.publicPricePayload(payload)}}catch{return {status:500,body:{ok:false,rows:[],error:'price_unavailable'}}}}
const tests=[];
for(const [name,input] of [['database failure',{connected:false,error:'supabase_price_query_failed',rows:[]}],['date query failure',{connected:false,error:'supabase_price_date_query_failed',rows:[]}],['credentials failure',{connected:false,error:'supabase_server_credentials_missing',rows:[]}],['mixed failure',{connected:true,error:'internal detail',rows:[]}],['missing envelope',null],['missing rows',{connected:true}]]){let r=response(input);assert.equal(r.status,500);assert.equal(r.body.ok,false);assert.equal(r.body.error,'price_unavailable');assert.equal(JSON.stringify(r).includes('supabase_'),false);tests.push(name)}
let empty=response({connected:true,rows:[],state_code:'NSW'});assert.equal(empty.status,200);assert.equal(empty.body.ok,true);assert.equal(empty.body.rows.length,0);tests.push('genuinely empty search remains successful');
let success=response({connected:true,rows:[{station_id:'QA-1',station_name:'Fixture only',price:199.9,secret:'must not leak'}],provider:{secret:'must not leak'}});assert.equal(success.status,200);assert.equal(success.body.rows.length,1);assert.equal(JSON.stringify(success).includes('must not leak'),false);tests.push('successful data retains existing public whitelist');
assert.equal(patch(repaired),repaired);tests.push('idempotence and byte-preserving patch');
if(process.argv[2])fs.writeFileSync(process.argv[2],repaired);
fs.mkdirSync('qa-results',{recursive:true});fs.writeFileSync('qa-results/backend-guard-tests.json',JSON.stringify({passed:tests.length,tests,testedAgainst:process.argv[2]?'downloaded existing function':'isolated original function fixture',deployed:false},null,2));
console.log(JSON.stringify({backendGuardTests:tests.length,passed:true,appliedToDownloadedSource:!!process.argv[2]}));
