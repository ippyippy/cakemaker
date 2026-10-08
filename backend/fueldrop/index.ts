// FMN_QLD_SUPPORT_20261008
import { supportAPI } from "./support.ts";
// Existing fueldrop Edge Function v61, with a guarded public price response.
// Legacy assets are snapshotted separately without changing their response bytes.
import * as webpush from "jsr:@negrel/webpush@0.5.0";
import { nativePushAPI, sendNativePushes, mergePushRuns } from "./native-push.ts";
import { HTML, ICON, MANIFEST, SW } from "./legacy-assets.ts";

const CORS={"access-control-allow-origin":"*","access-control-allow-methods":"GET,POST,DELETE,OPTIONS","access-control-allow-headers":"content-type,authorization,apikey"};
function json(data,status=200){return new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store",...CORS}})}
async function geocode(q,state="NSW"){
 q=String(q||"").trim().replace(/\s+/g," ").toLowerCase().replace(/[^a-z0-9 -]/g,"").slice(0,80);
 const st=String(state||"NSW").toUpperCase();
 if(q.length<2||!["NSW","WA","TAS","QLD"].includes(st))return[];
 try{
  const base=Deno.env.get("SUPABASE_URL")||"",headers=adminHeaders();
  if(!base)return[];
  const filter=/^\d{4}$/.test(q)?"postcode=eq."+encodeURIComponent(q):"suburb=ilike."+encodeURIComponent("*"+q+"*");
  const u=base+"/rest/v1/fuel_site_reference?select=station_id,state_code,suburb,postcode,latitude,longitude&state_code=eq."+encodeURIComponent(st)+"&"+filter+"&limit=2000";
  const rr=await fetch(u,{headers});
  if(!rr.ok)return[];
  const rows=await rr.json(),groups=new Map<string,any>();
  for(const x of (Array.isArray(rows)?rows:[])){
   const suburb=String(x.suburb||"").trim(),postcode=String(x.postcode||"").trim(),lat=Number(x.latitude),lng=Number(x.longitude);
   if(!suburb||!Number.isFinite(lat)||!Number.isFinite(lng))continue;
   const key=(suburb+"|"+postcode).toLowerCase(),g=groups.get(key)||{suburb,postcode,lat:0,lng:0,n:0};
   g.lat+=lat;g.lng+=lng;g.n++;groups.set(key,g);
  }
  return [...groups.values()].map(g=>({
   label:g.suburb+" "+st+(g.postcode?" "+g.postcode:""),
   state:st,suburb:g.suburb,postcode:g.postcode,lat:g.lat/g.n,lng:g.lng/g.n,
   source:"Government fuel station centroid"
  })).sort((a,b)=>{
   const al=a.suburb.toLowerCase(),bl=b.suburb.toLowerCase();
   const ae=al===q?0:al.startsWith(q)?1:2,be=bl===q?0:bl.startsWith(q)?1:2;
   return ae-be||a.label.localeCompare(b.label)
  }).slice(0,10);
 }catch{return[]}
}
function adminApiKey(){
 try{const keys=JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS")||"{}");if(keys&&keys.default)return keys.default}catch(_){}
 return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")||"";
}
function adminHeaders(){const key=adminApiKey();const h:Record<string,string>={"apikey":key,"accept":"application/json"};if(key&&!key.startsWith("sb_secret_"))h["authorization"]="Bearer "+key;return h}

let pushServerPromise:Promise<any>|null=null;
async function configValue(name:string){
 const base=Deno.env.get("SUPABASE_URL")||"";if(!base)return null;
 const r=await fetch(base+"/rest/v1/fueldrop_private_config?select=value&key=eq."+encodeURIComponent(name)+"&limit=1",{headers:adminHeaders()});
 if(!r.ok)return null;const rows=await r.json();return Array.isArray(rows)&&rows[0]?.value?String(rows[0].value):null;
}
async function pushServer(){
 if(pushServerPromise)return pushServerPromise;
 pushServerPromise=(async()=>{
  const raw=await configValue("vapid_jwk");if(!raw)throw new Error("vapid_not_configured");
  const keys=await webpush.importVapidKeys(JSON.parse(raw),{extractable:false});
  return await webpush.ApplicationServer.new({contactInformation:(Deno.env.get("SUPABASE_URL")||"https://supabase.com"),vapidKeys:keys});
 })();
 return pushServerPromise;
}
const FUEL_TYPES=new Set(["Diesel","U91","E10","U95","U98"]);
function clampNum(v:any,min:number,max:number,fallback:number){const n=Number(v);return Number.isFinite(n)?Math.min(max,Math.max(min,n)):fallback}
function cleanText(v:any,max=120){return String(v??"").trim().slice(0,max)}
function validPushEndpoint(v:any){try{const u=new URL(String(v||""));return u.protocol==="https:"&&String(v).length<=4096}catch{return false}}
function serverDistanceKm(a:number,b:number,c:number,d:number){const r=(x:number)=>x*Math.PI/180,R=6371,dp=r(c-a),dl=r(d-b),q=Math.sin(dp/2)**2+Math.cos(r(a))*Math.cos(r(c))*Math.sin(dl/2)**2;return 2*R*Math.atan2(Math.sqrt(q),Math.sqrt(1-q))}
function timezoneForState(state:any){
 const s=String(state||"QLD").toUpperCase();
 return s==="WA"?"Australia/Perth":s==="SA"?"Australia/Adelaide":s==="NT"?"Australia/Darwin":s==="VIC"?"Australia/Melbourne":s==="TAS"?"Australia/Hobart":s==="NSW"||s==="ACT"?"Australia/Sydney":"Australia/Brisbane";
}
function dateInTimezone(tz:string){
 const parts=new Intl.DateTimeFormat("en-AU",{timeZone:tz,year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date());
 const pick=(t:string)=>parts.find(p=>p.type===t)?.value||"";
 return pick("year")+"-"+pick("month")+"-"+pick("day");
}
function timeInTimezone(tz:string){
 const parts=new Intl.DateTimeFormat("en-AU",{timeZone:tz,hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(new Date());
 const pick=(t:string)=>parts.find(p=>p.type===t)?.value||"";
 return pick("hour")+":"+pick("minute");
}
function weekdayInTimezone(tz:string){
 return new Intl.DateTimeFormat("en-AU",{timeZone:tz,weekday:"short"}).format(new Date());
}
function hmMinutes(v:any){
 const m=String(v||"").match(/^(\d{1,2}):(\d{2})/);return m?Number(m[1])*60+Number(m[2]):360;
}
function timeDue(nowHm:string,target:any,windowMinutes=15){
 const n=hmMinutes(nowHm),t=hmMinutes(target);let d=n-t;if(d<0)d+=1440;return d>=0&&d<windowMinutes;
}
function valueRank(rows:any[],lat:number,lng:number,radius:number,tankLitres:number,economy:number){
 const inRange=rows.map((x:any)=>{
  const distance_km=serverDistanceKm(lat,lng,Number(x.latitude),Number(x.longitude));
  if(!Number.isFinite(distance_km)||distance_km>radius)return null;
  const price=Number(x.price);if(!Number.isFinite(price)||price<=0)return null;
  const estimatedRoadKm=distance_km*1.18;
  const roundTripKm=estimatedRoadKm*2;
  const travelLitres=roundTripKm*economy/100;
  const travelCost=travelLitres*(price/100);
  const fillCost=tankLitres*(price/100);
  const effectiveCpl=(fillCost+travelCost)/tankLitres*100;
  return {...x,distance_km,estimated_road_km:estimatedRoadKm,travel_cost:travelCost,effective_cpl:effectiveCpl};
 }).filter(Boolean) as any[];
 if(!inRange.length)return {ranked:[],median:NaN,bestValue:null,cheapest:null};
 const prices=inRange.map(x=>Number(x.price)).sort((a,b)=>a-b);
 const median=prices[Math.floor(prices.length/2)];
 for(const x of inRange)x.net_saving=Math.max(-9999,tankLitres*(median-Number(x.price))/100-Number(x.travel_cost));
 const ranked=[...inRange].sort((a,b)=>Number(a.effective_cpl)-Number(b.effective_cpl)||Number(a.price)-Number(b.price)||Number(a.distance_km)-Number(b.distance_km));
 const cheapest=[...inRange].sort((a,b)=>Number(a.price)-Number(b.price)||Number(a.distance_km)-Number(b.distance_km))[0];
 return {ranked,median,bestValue:ranked[0],cheapest};
}
async function savePushSubscription(body:any){
 const s=body?.subscription||body;if(!validPushEndpoint(s?.endpoint)||!s?.keys?.p256dh||!s?.keys?.auth)return {ok:false,error:"invalid_subscription"};
 const lat=clampNum(body?.latitude,-90,90,NaN),lng=clampNum(body?.longitude,-180,180,NaN);if(!Number.isFinite(lat)||!Number.isFinite(lng))return {ok:false,error:"location_required"};
 const fuel=FUEL_TYPES.has(body?.fuel_type)?body.fuel_type:"Diesel";
 const requestedState=cleanText(body?.state_code,3).toUpperCase();
 const state=["NSW","WA","TAS","QLD"].includes(requestedState)?requestedState:"NSW";
 const region=cleanText(body?.region_name,120)||null;
 const allowedFreq=new Set(["off","daily","weekdays","twice_daily","price_drop_only"]);
 const frequency=allowedFreq.has(body?.notification_frequency)?body.notification_frequency:"daily";
 const notify1=/^\d{2}:\d{2}$/.test(String(body?.notify_time||""))?String(body.notify_time)+":00":"06:00:00";
 const notify2=/^\d{2}:\d{2}$/.test(String(body?.notify_time_2||""))?String(body.notify_time_2)+":00":"15:30:00";
 const row={
  endpoint:String(s.endpoint),p256dh:cleanText(s.keys.p256dh,300),auth:cleanText(s.keys.auth,200),
  location_label:cleanText(body?.location_label,120)||null,latitude:lat,longitude:lng,state_code:state,region_name:region,
  fuel_type:fuel,radius_km:Math.round(clampNum(body?.radius_km,1,100,20)),
  tank_litres:clampNum(body?.tank_litres,20,1500,70),economy_l_per_100km:clampNum(body?.economy_l_per_100km,2,80,10),
  notification_frequency:frequency,notify_time:notify1,notify_time_2:frequency==="twice_daily"?notify2:null,timezone:timezoneForState(state),
  weather_addon:Boolean(body?.weather_addon),traffic_addon:Boolean(body?.traffic_addon),
  price_drop_threshold:frequency!=="off"&&body?.price_drop_threshold?clampNum(body.price_drop_threshold,1,1000,NaN):null,
  active:frequency!=="off",failure_count:0,last_error:null,last_error_at:null,updated_at:new Date().toISOString()
 };
 const h=adminHeaders();h["content-type"]="application/json";h["prefer"]="resolution=merge-duplicates,return=minimal";
 const base=Deno.env.get("SUPABASE_URL")||"";const r=await fetch(base+"/rest/v1/push_subscriptions?on_conflict=endpoint",{method:"POST",headers:h,body:JSON.stringify(row)});
 if(!r.ok)return {ok:false,error:"subscription_store_failed_"+r.status};return {ok:true};
}
async function removePushSubscription(endpoint:any){
 if(!validPushEndpoint(endpoint))return {ok:false,error:"invalid_endpoint"};
 const h=adminHeaders();h["prefer"]="return=minimal";const base=Deno.env.get("SUPABASE_URL")||"";
 const r=await fetch(base+"/rest/v1/push_subscriptions?endpoint=eq."+encodeURIComponent(String(endpoint)),{method:"DELETE",headers:h});
 return r.ok?{ok:true}:{ok:false,error:"unsubscribe_failed_"+r.status};
}
async function listActiveSubscriptions(){
 const base=Deno.env.get("SUPABASE_URL")||"",out:any[]=[];let offset=0;
 while(offset<100000){const r=await fetch(base+"/rest/v1/push_subscriptions?select=*&active=eq.true&order=id.asc&limit=1000&offset="+offset,{headers:adminHeaders()});if(!r.ok)throw new Error("subscription_query_failed_"+r.status);const page=await r.json();if(!Array.isArray(page))break;out.push(...page);if(page.length<1000)break;offset+=1000}return out;
}
async function patchPushSubscription(endpoint:string,patch:any){
 const base=Deno.env.get("SUPABASE_URL")||"",h=adminHeaders();h["content-type"]="application/json";h["prefer"]="return=minimal";
 await fetch(base+"/rest/v1/push_subscriptions?endpoint=eq."+encodeURIComponent(endpoint),{method:"PATCH",headers:h,body:JSON.stringify({...patch,updated_at:new Date().toISOString()})});
}
async function sendPriceDropPushes(){
 const subs=(await listActiveSubscriptions()).filter((s:any)=>Number(s.price_drop_threshold)>0);if(!subs.length)return {ok:true,subscriptions:0,sent:0,skipped:0,failed:0};
 const server=await pushServer(),fuelCache=new Map<string,any>();let sent=0,skipped=0,failed=0,gone=0;
 for(const sub of subs){
  const threshold=Number(sub.price_drop_threshold);if(!Number.isFinite(threshold)||threshold<=0){skipped++;continue}
  const state=String(sub.state_code||"QLD").toUpperCase(),tz=sub.timezone||timezoneForState(state),day=dateInTimezone(tz);
  const fuel=FUEL_TYPES.has(sub.fuel_type)?sub.fuel_type:"Diesel",cacheKey=state+"|"+fuel;
  if(!fuelCache.has(cacheKey))fuelCache.set(cacheKey,await latestFuelRows(fuel,state));
  const snap=fuelCache.get(cacheKey);if(!snap?.rows?.length||snap.price_date!==day){skipped++;continue}
  const lat=Number(sub.latitude),lng=Number(sub.longitude),radius=clampNum(sub.radius_km,1,100,20);if(!Number.isFinite(lat)||!Number.isFinite(lng)){skipped++;continue}
  const ranked=snap.rows.map((x:any)=>({...x,distance_km:serverDistanceKm(lat,lng,Number(x.latitude),Number(x.longitude))})).filter((x:any)=>Number.isFinite(x.distance_km)&&x.distance_km<=radius).sort((a:any,b:any)=>Number(a.price)-Number(b.price)||a.distance_km-b.distance_km);
  if(!ranked.length){skipped++;continue}
  const best=ranked[0],price=Number(best.price);if(!Number.isFinite(price)||price>threshold){skipped++;continue}
  const prior=Number(sub.last_price_drop_price),alreadyToday=sub.last_price_drop_notified_on===day;
  if(alreadyToday&&Number.isFinite(prior)&&price>=prior-0.01){skipped++;continue}
  const payload=JSON.stringify({title:`FillMeNow price alert · ${price.toFixed(1)}¢/${fuel}`,body:`${cleanText(best.station_name,48)} · ${Number(best.distance_km).toFixed(1)} km away · target ${threshold.toFixed(1)}¢`,url:"/",tag:"fueldrop-price-drop",data:{fuel,station_id:best.station_id,price,distance_km:Number(best.distance_km.toFixed(1)),threshold}});
  try{
   const subscriber=server.subscribe({endpoint:sub.endpoint,keys:{p256dh:sub.p256dh,auth:sub.auth}});
   await subscriber.pushTextMessage(payload,{urgency:webpush.Urgency.Normal,ttl:10800,topic:"fueldrop-price-drop"});
   await patchPushSubscription(sub.endpoint,{last_price_drop_notified_on:day,last_price_drop_price:price,failure_count:0,last_error:null,last_error_at:null});sent++;
  }catch(e){
   failed++;const status=e instanceof webpush.PushMessageError?e.response.status:0;const message=cleanText(String(e),400);
   if(status===404||status===410){gone++;await patchPushSubscription(sub.endpoint,{active:false,last_error:message,last_error_at:new Date().toISOString(),failure_count:Number(sub.failure_count||0)+1})}
   else await patchPushSubscription(sub.endpoint,{last_error:message,last_error_at:new Date().toISOString(),failure_count:Number(sub.failure_count||0)+1});
  }
 }
 return {ok:true,subscriptions:subs.length,sent,skipped,failed,gone};
}
async function sendDailyPushes(){
 const subs=await listActiveSubscriptions();if(!subs.length)return {ok:true,subscriptions:0,sent:0,skipped:0,failed:0};
 const server=await pushServer(),fuelCache=new Map<string,any>();let sent=0,skipped=0,failed=0,gone=0;
 for(const sub of subs){
  const state=String(sub.state_code||"NSW").toUpperCase();if(!["NSW","WA","TAS","QLD"].includes(state)){skipped++;continue}
  const freq=String(sub.notification_frequency||"daily");
  if(freq==="off"||freq==="price_drop_only"){skipped++;continue}
  const tz=sub.timezone||timezoneForState(state),day=dateInTimezone(tz),localTime=timeInTimezone(tz);
  if(freq==="weekdays"&&["Sat","Sun"].includes(weekdayInTimezone(tz))){skipped++;continue}
  const firstDue=timeDue(localTime,sub.notify_time||"06:00:00",16);
  const secondDue=freq==="twice_daily"&&timeDue(localTime,sub.notify_time_2||"15:30:00",16);
  if(!firstDue&&!secondDue){skipped++;continue}
  const lastAt=sub.last_notified_at?new Date(sub.last_notified_at).getTime():0;
  if(lastAt&&Date.now()-lastAt<45*60*1000){skipped++;continue}
  if(freq!=="twice_daily"&&sub.last_notified_on===day){skipped++;continue}
  const fuel=FUEL_TYPES.has(sub.fuel_type)?sub.fuel_type:"Diesel",cacheKey=state+"|"+fuel;
  if(!fuelCache.has(cacheKey))fuelCache.set(cacheKey,await latestFuelRows(fuel,state));
  const snap=fuelCache.get(cacheKey);if(!snap?.rows?.length){skipped++;continue}
  const lat=Number(sub.latitude),lng=Number(sub.longitude),radius=clampNum(sub.radius_km,1,100,20),tank=clampNum(sub.tank_litres,20,1500,70),economy=clampNum(sub.economy_l_per_100km,2,80,10);
  if(!Number.isFinite(lat)||!Number.isFinite(lng)){skipped++;continue}
  const value=valueRank(snap.rows,lat,lng,radius,tank,economy);if(!value.bestValue){skipped++;continue}
  const best=value.bestValue,cheapest=value.cheapest;
  const saving=Number(best.net_saving||0),same=cheapest&&cheapest.station_id===best.station_id;
  const body=same
   ?`${cleanText(best.station_name,42)} · ${Number(best.price).toFixed(1)}¢/${fuel} · ${Number(best.distance_km).toFixed(1)} km · est. save $${Math.max(0,saving).toFixed(2)}`
   :`Best value: ${cleanText(best.station_name,34)} ${Number(best.price).toFixed(1)}¢ · Cheapest pump ${Number(cheapest.price).toFixed(1)}¢ · est. save $${Math.max(0,saving).toFixed(2)}`;
  const payload=JSON.stringify({
   title:`FillMeNow · Best value near you`,body,url:"/",tag:"fueldrop-deal",
   data:{fuel,state,station_id:best.station_id,price:best.price,distance_km:Number(best.distance_km.toFixed(1)),effective_cpl:Number(best.effective_cpl.toFixed(1)),net_saving:Number(saving.toFixed(2))}
  });
  try{
   const subscriber=server.subscribe({endpoint:sub.endpoint,keys:{p256dh:sub.p256dh,auth:sub.auth}});
   await subscriber.pushTextMessage(payload,{urgency:webpush.Urgency.Normal,ttl:21600,topic:"fueldrop-deal"});
   await patchPushSubscription(sub.endpoint,{last_notified_on:day,last_notified_at:new Date().toISOString(),failure_count:0,last_error:null,last_error_at:null});sent++;
  }catch(e){
   failed++;const status=e instanceof webpush.PushMessageError?e.response.status:0;const message=cleanText(String(e),400);
   if(status===404||status===410){gone++;await patchPushSubscription(sub.endpoint,{active:false,last_error:message,last_error_at:new Date().toISOString(),failure_count:Number(sub.failure_count||0)+1})}
   else await patchPushSubscription(sub.endpoint,{last_error:message,last_error_at:new Date().toISOString(),failure_count:Number(sub.failure_count||0)+1});
  }
 }
 return {ok:true,subscriptions:subs.length,sent,skipped,failed,gone};
}
function xmlDecode(s:string){return String(s||"").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,"$1").replace(/&amp;/g,"&").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&quot;/g,"\"").replace(/&#39;/g,"'").trim()}
function xmlTag(block:string,name:string){const m=block.match(new RegExp("<"+name+"(?:\\s[^>]*)?>([\\s\\S]*?)<\\/"+name+">","i"));return m?xmlDecode(m[1]):""}
function stableHash(s:string){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0).toString(36)}
function waProduct(fuel:string){const f=String(fuel||"Diesel");return f==="Diesel"?4:f==="U91"?1:f==="U95"?2:f==="U98"?6:null}
async function waSyncState(fuel:string){
 const base=Deno.env.get("SUPABASE_URL")||"";if(!base)return null;
 const u=base+"/rest/v1/fuel_sync_state?select=last_success_at,status&provider_code=eq.wa-fuelwatch&fuel_type=eq."+encodeURIComponent(fuel)+"&limit=1";
 const r=await fetch(u,{headers:adminHeaders()});if(!r.ok)return null;const a=await r.json();return Array.isArray(a)&&a.length?a[0]:null;
}
async function markNationalSync(provider:string,fuel:string,patch:any){
 const row={provider_code:provider,fuel_type:fuel,updated_at:new Date().toISOString(),...patch};
 await upsertRows("fuel_sync_state","provider_code,fuel_type",[row]);
}
async function syncWesternAustralia(fuel:string){
 const product=waProduct(fuel);if(product==null)return {ok:true,skipped:"fuel_not_published_in_connector",fuel};
 const previous=await waSyncState(fuel);
 if(previous?.last_success_at&&Date.now()-new Date(previous.last_success_at).getTime()<15*60*1000)return {ok:true,skipped:"fresh_cache",lastSuccessAt:previous.last_success_at};
 const attempt=new Date().toISOString();await markNationalSync("wa-fuelwatch",fuel,{last_attempt_at:attempt,status:"running",error_message:null});
 try{
  const r=await fetch("https://www.fuelwatch.wa.gov.au/fuelwatch/fuelWatchRSS?Product="+product,{headers:{"accept":"application/rss+xml,application/xml,text/xml"}});
  if(!r.ok)throw new Error("fuelwatch_http_"+r.status);
  const xml=await r.text(),blocks=[...xml.matchAll(/<item>([\s\S]*?)<\/item>/gi)].map(m=>m[1]);
  const syncedAt=new Date().toISOString(),prices:any[]=[],sites:any[]=[];
  for(const b of blocks){
   const price=Number(xmlTag(b,"price")),name=xmlTag(b,"trading-name")||xmlTag(b,"title").replace(/^\d+(?:\.\d+)?:\s*/,""),brand=xmlTag(b,"brand"),suburb=xmlTag(b,"location"),address=xmlTag(b,"address"),lat=Number(xmlTag(b,"latitude")),lng=Number(xmlTag(b,"longitude")),date=xmlTag(b,"date");
   if(!name||!Number.isFinite(price)||!Number.isFinite(lat)||!Number.isFinite(lng))continue;
   const providerId=stableHash([brand,name,address,suburb].join("|").toLowerCase()),stationId="WA-"+providerId,priceDate=/^\d{4}-\d{2}-\d{2}$/.test(date)?date:brisbaneDate();
   sites.push({station_id:stationId,provider_station_id:providerId,state_code:"WA",provider_code:"wa-fuelwatch",region_name:suburb||null,station_name:name,brand:brand||null,suburb:suburb||null,address:address||"",postcode:null,latitude:lat,longitude:lng,source_modified_at:null,synced_at:syncedAt});
   prices.push({station_id:stationId,state_code:"WA",provider_code:"wa-fuelwatch",fuel_type:fuel,price_date:priceDate,station_name:name,brand:brand||null,suburb:suburb||null,address:address||"",postcode:null,latitude:lat,longitude:lng,price,transaction_date_utc:null,synced_at:syncedAt});
  }
  const uniqueSites=[...new Map(sites.map(x=>[x.station_id,x])).values()];
  const uniquePrices=[...new Map(prices.map(x=>[x.station_id+"|"+x.fuel_type+"|"+x.price_date,x])).values()];
  if(uniqueSites.length)await upsertRows("fuel_site_reference","station_id",uniqueSites);
  if(uniquePrices.length)await upsertFuelRows(uniquePrices);
  const dates=[...new Set(uniquePrices.map(x=>x.price_date))];
  for(const d of dates)await removeOlderRows("fuel_price_daily",syncedAt,"state_code=eq.WA&provider_code=eq.wa-fuelwatch&fuel_type=eq."+encodeURIComponent(fuel)+"&price_date=eq."+encodeURIComponent(d));
  await markNationalSync("wa-fuelwatch",fuel,{last_success_at:syncedAt,status:"ok",records_received:uniquePrices.length,error_message:null});
  return {ok:true,provider:"FuelWatch",fuel,records:uniquePrices.length,syncedAt};
 }catch(e){
  const msg=String(e&&e.message||e);await markNationalSync("wa-fuelwatch",fuel,{status:"error",error_message:msg});return {ok:false,error:msg};
 }
}

async function nationalRegions(state:string){
 const st=String(state||"QLD").toUpperCase().replace(/[^A-Z]/g,"").slice(0,3)||"QLD";
 const base=Deno.env.get("SUPABASE_URL")||"",key=adminApiKey();if(!base||!key)return [];
 const r=await fetch(base+"/rest/v1/australia_regions?select=state_code,region_code,region_name,latitude,longitude,sort_order&state_code=eq."+encodeURIComponent(st)+"&order=sort_order.asc,region_name.asc",{headers:adminHeaders()});
 if(!r.ok)return [];const rows=await r.json();return Array.isArray(rows)?rows:[];
}
async function providerInfo(state:string){
 const base=Deno.env.get("SUPABASE_URL")||"",key=adminApiKey();
 if(!base||!key)return null;
 const st=String(state||"NSW").toUpperCase();
 if(!["NSW","WA","TAS","QLD"].includes(st))return null;
 const code=encodeURIComponent(st);
 const r=await fetch(base+"/rest/v1/fuel_data_providers?select=provider_code,provider_name,is_realtime,typical_delay_minutes,attribution,status&state_codes=cs.{"+code+"}&limit=1",{headers:adminHeaders()});
 if(!r.ok)return null;const rows=await r.json();
 if(!Array.isArray(rows)||!rows.length)return null;
 const p=rows[0];return {...p,status:(p.status==="connected_trial"||p.status==="connected"||p.status==="live")?"connected":"unavailable"};
}
// FMN_DIESEL_COVERAGE_20261008
function selectComparableFuelRows(rows:any[]){
 const stations=new Map<string,any>();
 for(const row of rows){
  const id=String(row.station_id),prior=stations.get(id);
  if(!prior||Number(row.price)<Number(prior.price)||(Number(row.price)===Number(prior.price)&&row.fuel_type==="Diesel"&&prior.fuel_type!=="Diesel"))stations.set(id,row);
 }
 return [...stations.values()].sort((a,b)=>Number(a.price)-Number(b.price)||String(a.station_id).localeCompare(String(b.station_id)));
}
async function qldCoverageReady(){
 if(!(Deno.env.get("QLD_FUEL_API_TOKEN")||"").trim())return false;
 try{const base=Deno.env.get("SUPABASE_URL")||"";const r=await fetch(base+"/rest/v1/fuel_price_daily?select=synced_at&state_code=eq.QLD&provider_code=eq.qld-fpqld&order=synced_at.desc&limit=1",{headers:adminHeaders(),signal:AbortSignal.timeout(8000)});if(!r.ok)return false;const rows=await r.json();const age=Array.isArray(rows)&&rows.length?Date.now()-Date.parse(rows[0].synced_at):NaN;return Number.isFinite(age)&&age>=0&&age<86400000;}catch{return false}
}
async function latestFuelRows(fuel,state="QLD",lat?:number,lng?:number,radiusKm?:number){
 const st=String(state||"QLD").toUpperCase().replace(/[^A-Z]/g,"").slice(0,3)||"QLD";
 const provider=await providerInfo(st);
 const qldConfigured=Boolean(Deno.env.get("QLD_FUEL_API_TOKEN"));
 const base=Deno.env.get("SUPABASE_URL")||"";const key=adminApiKey();
 if(!base||!key)return {connected:false,rows:[],error:"supabase_server_credentials_missing",state_code:st,provider};
 const f=encodeURIComponent(String(fuel||"Diesel").slice(0,20));
 const stateFilter="&state_code=eq."+encodeURIComponent(st);
 const fuelFilter=String(fuel||"Diesel")==="Diesel"?(st==="QLD"?"fuel_type=in.(Diesel,Premium%20Diesel,ULSD)":"fuel_type=in.(Diesel,Premium%20Diesel)"):"fuel_type=eq."+f;
 const la=Number(lat),lo=Number(lng),rk=Number(radiusKm);let geoFilter="";
 if(Number.isFinite(la)&&Number.isFinite(lo)&&Number.isFinite(rk)&&rk>=1&&rk<=100){
  const latDelta=rk/110.574,cos=Math.max(.2,Math.abs(Math.cos(la*Math.PI/180))),lngDelta=rk/(111.320*cos);
  const minLat=(la-latDelta).toFixed(6),maxLat=(la+latDelta).toFixed(6),minLng=(lo-lngDelta).toFixed(6),maxLng=(lo+lngDelta).toFixed(6);
  geoFilter="&latitude=gte."+minLat+"&latitude=lte."+maxLat+"&longitude=gte."+minLng+"&longitude=lte."+maxLng;
 }
 const d=await fetch(base+"/rest/v1/fuel_price_daily?select=price_date&"+fuelFilter+stateFilter+"&order=price_date.desc&limit=1",{headers:adminHeaders()});
 if(!d.ok)return {connected:false,rows:[],error:"supabase_price_date_query_failed",state_code:st,provider};
 const dates=await d.json();
 if(!Array.isArray(dates)||!dates.length)return {connected:true,rows:[],price_date:null,state_code:st,provider,qldCredentialConfigured:st==="QLD"?qldConfigured:undefined};
 const date=dates[0].price_date;
 const select="station_id,state_code,provider_code,station_name,brand,suburb,address,postcode,latitude,longitude,price,fuel_type,price_date,transaction_date_utc,synced_at";
 const rows:any[]=[];let offset=0;const pageSize=1000;
 while(offset<10000){
  const u=base+"/rest/v1/fuel_price_daily?select="+select+"&"+fuelFilter+stateFilter+geoFilter+"&price_date=eq."+encodeURIComponent(date)+"&order=price.asc,station_id.asc,fuel_type.asc&limit="+pageSize+"&offset="+offset;
  const r=await fetch(u,{headers:adminHeaders()});
  if(!r.ok)return {connected:false,rows:[],error:"supabase_price_query_failed",state_code:st,provider};
  const page=await r.json();if(!Array.isArray(page))break;rows.push(...page);if(page.length<pageSize)break;offset+=pageSize;
 }
 let snapshotSyncedAt:string|null=null;
 for(const x of rows){if(x.synced_at&&(!snapshotSyncedAt||String(x.synced_at)>snapshotSyncedAt))snapshotSyncedAt=String(x.synced_at)}
 return {connected:true,rows:selectComparableFuelRows(rows),price_date:date,snapshot_synced_at:snapshotSyncedAt,state_code:st,provider,source:provider?.provider_name||"FillMeNow government data cache"};
}

function publicPricePayload(payload:any){
 // FMN_PRICE_FAILURE_GUARD_20261007: a failed read is not an empty search.
 if(payload?.connected!==true||payload?.error||!Array.isArray(payload?.rows))throw new Error("price_unavailable");
 const rows=(Array.isArray(payload?.rows)?payload.rows:[]).map((x:any)=>({
  station_id:x.station_id,station_name:x.station_name,brand:x.brand||null,suburb:x.suburb||null,address:x.address||"",postcode:x.postcode||null,
  latitude:x.latitude,longitude:x.longitude,price:x.price,fuel_type:x.fuel_type,price_date:x.price_date,
  transaction_date_utc:x.transaction_date_utc,synced_at:x.synced_at
 }));
 return {ok:true,rows,price_date:payload?.price_date||null,snapshot_synced_at:payload?.snapshot_synced_at||null,state_code:payload?.state_code||null};
}
async function isAdminRequest(req:Request){
 const expected=adminApiKey();
 if(expected){const apiKey=req.headers.get("apikey")||"";if(apiKey===expected)return true;const auth=req.headers.get("authorization")||"";if(auth==="Bearer "+expected)return true}
 const supplied=req.headers.get("x-cron-secret")||"";if(!supplied)return false;
 const cron=await configValue("cron_secret");return Boolean(cron&&supplied===cron);
}
function qldHeaders(){
 const token=Deno.env.get("QLD_FUEL_API_TOKEN")||"";
 return {"accept":"application/json","authorization":"FPDAPI SubscriberToken="+token};
}
async function qldGet(path:string){
 const token=Deno.env.get("QLD_FUEL_API_TOKEN")||"";if(!token)throw new Error("qld_api_token_not_configured");
 const base=(Deno.env.get("QLD_FUEL_API_BASE")||"https://fppdirectapi-prod.fuelpricesqld.com.au").replace(/\/$/,"");
 const r=await fetch(base+path,{headers:qldHeaders()});
 if(!r.ok)throw new Error("qld_api_"+r.status+"_"+path.split("?")[0]);
 return await r.json();
}
function qldArray(payload:any,keys:string[]){
  if(Array.isArray(payload))return payload;
  for(const k of keys){if(Array.isArray(payload?.[k]))return payload[k]}
  if(payload&&typeof payload==="object"){for(const v of Object.values(payload)){if(Array.isArray(v))return v}}
  return [];
}
// FMN_QLD_GRADE_GUARD_20261009
function appFuelName(name:string){
 // Exact provider grades only. B20 and aggregate filter names are not ordinary diesel.
 const n=String(name||"").trim().toLowerCase().replace(/\s+/g," ");
 switch(n){
  case "unleaded": return "U91";
  case "premium unleaded 95": return "U95";
  case "premium unleaded 98": return "U98";
  case "e10": return "E10";
  case "diesel": return "Diesel";
  case "premium diesel": return "Premium Diesel";
  case "ulsd": return "ULSD";
  default: return null;
 }
}
function brisbaneDate(){
 const parts=new Intl.DateTimeFormat("en-AU",{timeZone:"Australia/Brisbane",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date());
 const pick=(t:string)=>parts.find(p=>p.type===t)?.value||"";
 return pick("year")+"-"+pick("month")+"-"+pick("day");
}
async function upsertRows(table:string,conflict:string,rows:any[]){
 const base=Deno.env.get("SUPABASE_URL")||"";const headers=adminHeaders();headers["content-type"]="application/json";headers["prefer"]="resolution=merge-duplicates,return=minimal";
 let written=0;
 for(let i=0;i<rows.length;i+=500){
  const chunk=rows.slice(i,i+500);if(!chunk.length)continue;
  const r=await fetch(base+"/rest/v1/"+table+"?on_conflict="+encodeURIComponent(conflict),{method:"POST",headers,body:JSON.stringify(chunk)});
  if(!r.ok)throw new Error("supabase_"+table+"_upsert_failed_"+r.status);
  written+=chunk.length;
 }
 return written;
}
async function removeOlderRows(table:string,syncedAt:string,extraFilter=""){
 const base=Deno.env.get("SUPABASE_URL")||"";const headers=adminHeaders();headers["prefer"]="return=minimal";
 const url=base+"/rest/v1/"+table+"?synced_at=lt."+encodeURIComponent(syncedAt)+(extraFilter?"&"+extraFilter:"");
 const r=await fetch(url,{method:"DELETE",headers});if(!r.ok)throw new Error("supabase_"+table+"_cleanup_failed_"+r.status);
}
async function readAllRows(table:string,select:string,filter=""){
 const base=Deno.env.get("SUPABASE_URL")||"",out:any[]=[];let offset=0;
 while(offset<20000){
  const r=await fetch(base+"/rest/v1/"+table+"?select="+select+(filter?"&"+filter:"")+"&order="+(table==="fuel_site_reference"?"station_id.asc":"fuel_id.asc")+"&limit=1000&offset="+offset,{headers:adminHeaders()});
  if(!r.ok)throw new Error("supabase_"+table+"_read_failed_"+r.status);
  const page=await r.json();if(!Array.isArray(page))throw new Error("invalid_reference_response");out.push(...page);if(page.length<1000)break;offset+=1000;
 }
 return out;
}
async function refreshQueenslandReference(){
 const token=Deno.env.get("QLD_FUEL_API_TOKEN")||"";if(!token)return {ok:true,skipped:"qld_api_token_not_configured"};
 const qs="?countryId=21&geoRegionLevel=3&geoRegionId=1",syncedAt=new Date().toISOString();
 const [fuelRes,brandRes,regionRes,siteRes]=await Promise.all([
  qldGet("/Subscriber/GetCountryFuelTypes?countryId=21"),
  qldGet("/Subscriber/GetCountryBrands?countryId=21"),
  qldGet("/Subscriber/GetCountryGeographicRegions?countryId=21"),
  qldGet("/Subscriber/GetFullSiteDetails"+qs)
 ]);
 const fuelRows=qldArray(fuelRes,["Fuels","FuelTypes","F"]).map((x:any)=>({fuel_id:Number(x.FuelId),name:String(x.Name||""),app_fuel_type:appFuelName(String(x.Name||"")),synced_at:syncedAt})).filter((x:any)=>Number.isFinite(x.fuel_id)&&x.name);
 const brands=new Map<number,string>(qldArray(brandRes,["Brands","B"]).map((x:any)=>[Number(x.BrandId),String(x.Name||"")]));
 const suburbs=new Map<number,string>(qldArray(regionRes,["GeographicRegions","Regions","G"]).filter((x:any)=>Number(x.GeoRegionLevel)===1).map((x:any)=>[Number(x.GeoRegionId),String(x.Name||"")]));
 const siteRows:any[]=[];
 for(const s of qldArray(siteRes,["S","Sites"])){
  const lat=Number(s.Lat),lng=Number(s.Lng),id=Number(s.S);if(!Number.isFinite(id)||!Number.isFinite(lat)||!Number.isFinite(lng))continue;
  const mod=Date.parse(String(s.M||""));
  siteRows.push({station_id:String(id),provider_station_id:String(id),state_code:"QLD",provider_code:"qld-fpqld",region_name:suburbs.get(Number(s.G1))||null,station_name:String(s.N||"Fuel station"),brand:brands.get(Number(s.B))||null,brand_id:Number.isFinite(Number(s.B))?Number(s.B):null,suburb:suburbs.get(Number(s.G1))||null,suburb_region_id:Number.isFinite(Number(s.G1))?Number(s.G1):null,address:String(s.A||""),postcode:s.P?String(s.P):null,latitude:lat,longitude:lng,source_modified_at:Number.isFinite(mod)?new Date(mod).toISOString():null,synced_at:syncedAt});
 }
 if(!fuelRows.length||!siteRows.length)throw new Error("qld_empty_reference_snapshot");
 const fuelsWritten=await upsertRows("fuel_type_reference","fuel_id",fuelRows),sitesWritten=await upsertRows("fuel_site_reference","station_id",siteRows);
 await removeOlderRows("fuel_type_reference",syncedAt);await removeOlderRows("fuel_site_reference",syncedAt,"state_code=eq.QLD&provider_code=eq.qld-fpqld");
 return {ok:true,source:"Queensland Fuel Price Reporting Direct API",referenceSyncedAt:syncedAt,fuelsWritten,sitesWritten};
}
async function loadQueenslandReference(){
 const [fuels,sites]=await Promise.all([readAllRows("fuel_type_reference","fuel_id,name,app_fuel_type"),readAllRows("fuel_site_reference","station_id,station_name,brand,suburb,address,postcode,latitude,longitude","state_code=eq.QLD&provider_code=eq.qld-fpqld")]);
 return {fuels:new Map<number,string>(fuels.map((x:any)=>[Number(x.fuel_id),appFuelName(String(x.name||""))||""])),sites:new Map<string,any>(sites.map((x:any)=>[String(x.station_id),x])),fuelCount:fuels.length,siteCount:sites.length};
}
async function upsertFuelRows(rows:any[]){return await upsertRows("fuel_price_daily","station_id,fuel_type,price_date",rows)}
async function removeStaleSnapshotRows(priceDate:string,syncedAt:string,state="QLD",provider="qld-fpqld"){await removeOlderRows("fuel_price_daily",syncedAt,"state_code=eq."+encodeURIComponent(state)+"&provider_code=eq."+encodeURIComponent(provider)+"&price_date=eq."+encodeURIComponent(priceDate))}
function queenslandPriceRows(records:any[],refs:{fuels:Map<number,string>;sites:Map<string,any>},date:string,syncedAt:string){
 const unique=new Map<string,any>();
 const allowed=new Set(["Diesel","Premium Diesel","ULSD","U91","U95","U98","E10"]);
 for(const p of records){
  if(!p||p.Price==null||p.Price==="")continue;
  const raw=Number(p.Price);if(!Number.isFinite(raw)||raw<=0||raw===9999)continue;
  const fuelType=refs.fuels.get(Number(p.FuelId));if(!fuelType||!allowed.has(fuelType))continue;
  const site=refs.sites.get(String(p.SiteId));if(!site)continue;
  if(site.latitude==null||site.longitude==null||site.latitude===""||site.longitude==="")continue;
  const lat=Number(site.latitude),lng=Number(site.longitude);
  if(!Number.isFinite(lat)||!Number.isFinite(lng)||lat< -29.5||lat> -9||lng<137||lng>154.5)continue;
  let transaction:string|null=null;
  if(p.TransactionDateUtc!=null&&p.TransactionDateUtc!==""){
   const text=String(p.TransactionDateUtc).trim();
   if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$/.test(text))throw new Error("qld_invalid_price_timestamp");
   const timestamp=Date.parse(/[zZ]|[+-]\d{2}:?\d{2}$/.test(text)?text:text+"Z");
   if(!Number.isFinite(timestamp))throw new Error("qld_invalid_price_timestamp");
   transaction=new Date(timestamp).toISOString();
  }
  const row={station_id:String(p.SiteId),state_code:"QLD",provider_code:"qld-fpqld",fuel_type:fuelType,price_date:date,station_name:String(site.station_name||"Fuel station"),brand:site.brand||null,suburb:site.suburb||null,address:String(site.address||""),postcode:site.postcode?String(site.postcode):null,latitude:lat,longitude:lng,price:raw/10,transaction_date_utc:transaction,synced_at:syncedAt};
  const key=row.station_id+"|"+fuelType,prior=unique.get(key);
  if(prior&&prior.price!==row.price&&(!prior.transaction_date_utc||!transaction||prior.transaction_date_utc===transaction))throw new Error("qld_conflicting_price_rows");
  if(!prior||(transaction||"")>(prior.transaction_date_utc||""))unique.set(key,row);
 }
 if(!unique.size)throw new Error("qld_empty_price_snapshot");
 return [...unique.values()];
}
async function syncQueenslandFuel(){
 const token=Deno.env.get("QLD_FUEL_API_TOKEN")||"";if(!token)return {ok:true,skipped:"qld_api_token_not_configured"};
 let refs=await loadQueenslandReference();
 let referenceBootstrapped=false;
 if(!refs.siteCount||!refs.fuelCount){const boot=await refreshQueenslandReference();if(!boot.ok)return boot;refs=await loadQueenslandReference();referenceBootstrapped=true}
 const qs="?countryId=21&geoRegionLevel=3&geoRegionId=1",priceRes=await qldGet("/Price/GetSitesPrices"+qs);
 const date=brisbaneDate(),syncedAt=new Date().toISOString();
 const rows=queenslandPriceRows(qldArray(priceRes,["SitePrices","Prices","P"]),refs,date,syncedAt);
 const written=await upsertFuelRows(rows);await removeStaleSnapshotRows(date,syncedAt);
 return {ok:true,source:"Queensland Fuel Price Reporting Direct API",priceDate:date,snapshotSyncedAt:syncedAt,rowsWritten:written,sitesLoaded:refs.siteCount,pricesReceived:qldArray(priceRes,["SitePrices","Prices","P"]).length,referenceBootstrapped};
}

function standaloneExportHtml(){
 let h=HTML;
 h=h.replace('<link rel="manifest" href="?asset=manifest">','<link rel="manifest" href="/manifest.webmanifest">');
 h=h.replace('<link rel="icon" href="?asset=icon">','<link rel="icon" href="/icon.svg">');
 h=h.replace(
  'function api(q){var u=new URL(location.href);u.search="";',
  'const BACKEND="https://psytztnkeeymavzmpomv.supabase.co/functions/v1/fueldrop";\nfunction api(q){var u=new URL(BACKEND);u.search="";'
 );
 h=h.replace(
  'navigator.serviceWorker.register(location.pathname+"?asset=sw",{scope:location.pathname})',
  'navigator.serviceWorker.register("/sw.js",{scope:"/"})'
 );
 h=h.replaceAll('navigator.serviceWorker.getRegistration(location.pathname)','navigator.serviceWorker.getRegistration("/")');
 h=h.replaceAll('location.pathname+"?asset=icon"','"/icon.svg"');
 h=h.replace(
  'summary=null;if(!loc||!rows.length)return null;var a=rows.map',
  'summary=null;if(!loc||!rows.length){ranked=[];if(!loc&&typeof clearMapMarkers==="function")clearMapMarkers();return null}var a=rows.map'
 );
 return h;
}

Deno.serve(async req=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:CORS});
 const url=new URL(req.url),asset=url.searchParams.get("asset");
 if(asset==="standalone")return new Response(standaloneExportHtml(),{headers:{...CORS,"content-type":"text/html; charset=utf-8","cache-control":"no-cache"}});
 if(asset==="manifest")return new Response(MANIFEST,{headers:{"content-type":"application/manifest+json; charset=utf-8","cache-control":"public,max-age=3600"}});
 if(asset==="icon")return new Response(ICON,{headers:{"content-type":"image/svg+xml; charset=utf-8","cache-control":"public,max-age=86400"}});
 if(asset==="sw")return new Response(SW,{headers:{"content-type":"application/javascript; charset=utf-8","cache-control":"no-cache","service-worker-allowed":"/functions/v1/fueldrop"}});
 if(url.searchParams.get("api")==="status"){const vapid=await configValue("vapid_public_key");return json({ok:true,launchStates:["NSW","WA","TAS",...(await qldCoverageReady()?["QLD"]:[])],pushConfigured:Boolean(vapid)})}
 if(["support-report","support-delete"].includes(url.searchParams.get("api")||"")){const a=await supportAPI(url.searchParams.get("api")!,req,{base:()=>Deno.env.get("SUPABASE_URL")||"",headers:adminHeaders});return json(a!.body,a!.status)}
 const nativeDeps={base:()=>Deno.env.get("SUPABASE_URL")||"",headers:adminHeaders,fuelRows:latestFuelRows,rank:valueRank};
 if(["native-push-status","native-subscribe","native-unsubscribe"].includes(url.searchParams.get("api")||"")){const response=await nativePushAPI(url.searchParams.get("api")!,req,nativeDeps);return json(response!.body,response!.status)}
 if(url.searchParams.get("api")==="push-public-key"){const key=await configValue("vapid_public_key");return key?json({configured:true,publicKey:key}):json({configured:false,error:"push_not_configured"},503)}
 if(url.searchParams.get("api")==="subscribe"){if(req.method!=="POST")return json({ok:false,error:"method_not_allowed"},405);try{return json(await savePushSubscription(await req.json()))}catch(e){return json({ok:false,error:"subscribe_failed"},400)}}
 if(url.searchParams.get("api")==="unsubscribe"){if(req.method!=="POST")return json({ok:false,error:"method_not_allowed"},405);try{const b=await req.json();return json(await removePushSubscription(b?.endpoint))}catch{return json({ok:false,error:"unsubscribe_failed"},400)}}
 if(url.searchParams.get("api")==="send-price-drops"){if(!await isAdminRequest(req))return json({ok:false,error:"unauthorized"},401);try{return json(await mergePushRuns(sendPriceDropPushes,()=>sendNativePushes("price_drop",nativeDeps)))}catch(e){return json({ok:false,error:String(e&&e.message||e)},500)}}
 if(url.searchParams.get("api")==="send-daily"){if(!await isAdminRequest(req))return json({ok:false,error:"unauthorized"},401);try{return json(await mergePushRuns(sendDailyPushes,()=>sendNativePushes("daily",nativeDeps)))}catch(e){return json({ok:false,error:String(e&&e.message||e)},500)}}
 if(url.searchParams.get("api")==="sync-reference"){if(!await isAdminRequest(req))return json({ok:false,error:"unauthorized"},401);try{return json(await refreshQueenslandReference())}catch(e){return json({ok:false,error:String(e&&e.message||e)},500)}}
 if(url.searchParams.get("api")==="sync-wa"){
  if(!await isAdminRequest(req))return json({ok:false,error:"unauthorized"},401);
  try{
   const fuels=["Diesel","U91","U95","U98"],results=[];
   for(const fuel of fuels)results.push(await syncWesternAustralia(fuel));
   return json({ok:results.every((x:any)=>x?.ok!==false),results});
  }catch(e){return json({ok:false,error:String(e&&e.message||e)},500)}
 }
 if(url.searchParams.get("api")==="sync"){if(!await isAdminRequest(req))return json({ok:false,error:"unauthorized"},401);try{return json(await syncQueenslandFuel())}catch(e){return json({ok:false,error:String(e&&e.message||e)},500)}}
 if(url.searchParams.get("api")==="prices"){try{if(url.searchParams.get("state")==="QLD"&&!await qldCoverageReady())return json({ok:false,rows:[],error:"coverage_pending"},503);const hasGeo=url.searchParams.has("lat")&&url.searchParams.has("lng")&&url.searchParams.has("radius");return json(publicPricePayload(await latestFuelRows(url.searchParams.get("fuel")||"Diesel",url.searchParams.get("state")||"NSW",hasGeo?Number(url.searchParams.get("lat")):undefined,hasGeo?Number(url.searchParams.get("lng")):undefined,hasGeo?Number(url.searchParams.get("radius")):undefined)))}catch(e){return json({ok:false,rows:[],error:"price_unavailable"},500)}}
 if(url.searchParams.get("api")==="regions"){try{return json({state:(url.searchParams.get("state")||"NSW").toUpperCase(),regions:await nationalRegions(url.searchParams.get("state")||"NSW")})}catch(e){return json({regions:[],error:"regions_failed"},500)}}
 if(url.searchParams.get("api")==="geocode"){try{return json({candidates:(await geocode(url.searchParams.get("q")||"",url.searchParams.get("state")||"NSW")).map((x:any)=>({label:x.label,state:x.state,suburb:x.suburb,postcode:x.postcode,lat:x.lat,lng:x.lng}))})}catch(e){return json({candidates:[],error:"geocode_failed"})}}
 return new Response(HTML,{status:200,headers:new Headers([["Content-Type","text/html; charset=utf-8"],["Cache-Control","no-store, no-cache, must-revalidate"],["Pragma","no-cache"],["Referrer-Policy","strict-origin-when-cross-origin"]])});
});
