/* FillMeNow nearby rules. Pure functions; no location tracking, network or storage. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.FMNNearbyCore=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){'use strict';
const truckKinds=['rigid','articulated','b-double','road-train','other'];
const limits={height:[0.5,10],width:[0.5,10],length:[1,70],weight:[0.5,300]};
function number(v){return v!==''&&v!=null&&Number.isFinite(Number(v))?Number(v):null;}
function truckMode(p){return p&&['truck','heavy'].includes(p.vehicle);}
function validateTruck(raw){const t={configuration:String(raw?.configuration||'rigid')};for(const k of Object.keys(limits)){const v=number(raw?.[k]),[lo,hi]=limits[k];if(v===null||v<lo||v>hi)return {ok:false,field:k};t[k]=Math.round(v*100)/100;}if(!truckKinds.includes(t.configuration))return {ok:false,field:'configuration'};return {ok:true,truck:t};}
function priceReview(row){const p=number(row?.price);return row?.recommendation_eligible===false||p===null||p<100||p>500;}
function normaliseFilters(raw={},radius=20){let max=number(raw.maxKm),min=number(raw.minKm);max=max===null?radius:Math.max(1,Math.min(100,max));min=min===null?0:Math.max(0,Math.min(max,min));return {version:1,minKm:min,maxKm:max,sort:['value','price','distance','deal'].includes(raw.sort)?raw.sort:'value',deals:['all','active','eligible'].includes(raw.deals)?raw.deals:'all',access:raw.access==='matches'?'matches':'all'};}
function https(v){try{const u=new URL(v);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}}
function current(r,now){const start=Date.parse(r.starts_at),end=Date.parse(r.ends_at),checked=Date.parse(r.verified_at);return Number.isFinite(start)&&Number.isFinite(end)&&Number.isFinite(checked)&&checked<=now&&now-checked<=7*86400000&&start<=now&&end>now&&r.status==='verified';}
function offerKey(o){return [o.id,o.verified_at,o.ends_at,o.discount_cpl,o.max_litres,o.minimum_litres,o.terms,o.terms_url,o.eligibility].join('|');}
function offersFor(row,ctx,catalog,accepted=[],now=Date.now()){
 const id=String(row.station_id);return (catalog?.offers||[]).filter(o=>o&&o.state===ctx.state&&String(o.station_id)===id&&Array.isArray(o.fuels)&&o.fuels.includes(row.fuel_type||ctx.fuel)&&typeof o.id==='string'&&/^[a-z0-9-]{3,80}$/.test(o.id)&&current(o,now)&&https(o.terms_url)&&typeof o.title==='string'&&o.title.length>2&&typeof o.terms==='string'&&o.terms.length>=10&&['everyone','conditions'].includes(o.eligibility)&&number(o.discount_cpl)>0&&number(o.discount_cpl)<=50&&number(o.max_litres)>0&&number(o.minimum_litres)>=0).map(o=>{
  const fill=number(ctx.tank)||0,qualifies=fill>=Number(o.minimum_litres)&&(o.eligibility==='everyone'||accepted.includes(offerKey(o)));
  const saving=qualifies&&!priceReview(row)?Math.min(fill,Number(o.max_litres))*Number(o.discount_cpl)/100:0;
  return {...o,qualifies,saving,key:offerKey(o)};
 }).sort((a,b)=>b.saving-a.saving||a.id.localeCompare(b.id));
}
function truckAccess(row,ctx,catalog,now=Date.now()){
 if(!truckMode(ctx))return {status:'off',label:''};const input=validateTruck(ctx.truck);if(!input.ok)return {status:'unknown',label:'Truck dimensions incomplete'};
 const r=(catalog?.access||[]).find(r=>r&&r.state===ctx.state&&String(r.station_id)===String(row.station_id));
 if(!r||r.status!=='verified'||!https(r.source_url)||!Number.isFinite(Date.parse(r.verified_at))||Date.parse(r.verified_at)>now||now-Date.parse(r.verified_at)>90*86400000||!Number.isFinite(Date.parse(r.expires_at))||Date.parse(r.expires_at)<=now)return {status:'unknown',label:'Truck access not verified'};
 const t=input.truck,known=Object.keys(limits).filter(k=>number(r[k])!==null&&number(r[k])>0);
 if(known.some(k=>t[k]>Number(r[k]))||(Array.isArray(r.configurations)&&!r.configurations.includes(t.configuration)))return {status:'mismatch',label:'Does not match recorded truck limits'};
 if(known.length<4||!Array.isArray(r.configurations)||r.turning_access_verified!==true)return {status:'unknown',label:'Truck access partly recorded — check first'};
 if(t.height+.1>r.height||t.width+.1>r.width)return {status:'unknown',label:'Limited clearance — check with station'};
 return {status:'match',label:'Matches recorded dimensions · route not checked'};
}
function select(rows,ctx,filters,catalog,accepted=[],now=Date.now()){
 const f=normaliseFilters(filters,ctx.radius);const list=rows.filter(r=>Number.isFinite(r.distance)&&r.distance>=f.minKm&&r.distance<=f.maxKm).map(r=>{
  const offers=offersFor(r,ctx,catalog,accepted,now),access=truckAccess(r,ctx,catalog,now),best=offers.find(o=>o.qualifies);
  return {...r,_offers:offers,_access:access,_review:priceReview(r),_dealSaving:best?.saving||0};
 }).filter(r=>(f.deals==='all'||r._offers.some(o=>f.deals==='active'||o.qualifies))&&(!truckMode(ctx)||f.access!=='matches'||r._access.status==='match'));
 const cost=r=>Number(r.effective)-((ctx.tank>0?r._dealSaving/ctx.tank:0)*100);
 list.sort((a,b)=>Number(a._review)-Number(b._review)||(f.sort==='distance'?a.distance-b.distance:f.sort==='price'?a.price-b.price:f.sort==='deal'?cost(a)-cost(b):a.effective-b.effective)||String(a.station_id).localeCompare(String(b.station_id)));return list;
}
return Object.freeze({number,truckMode,validateTruck,priceReview,normaliseFilters,offersFor,offerKey,truckAccess,select});
});
