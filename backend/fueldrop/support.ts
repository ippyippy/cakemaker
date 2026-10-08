// FillMeNow support: public submission, private storage, no public complaint listing.
export type SupportDeps = { base:()=>string; headers:()=>Record<string,string> };
const topics=new Set(['loading','map','prices','location','dash','alerts','accessibility','privacy','suggestion','other']);
const screens=new Set(['explore','options','saved','alerts','more','onboarding','support','privacy','terms']);
const browsers=new Set(['Chrome','Safari','Firefox','Edge','Other']);
const enc=new TextEncoder();
async function digest(value:string){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(value))),x=>x.toString(16).padStart(2,'0')).join('')}
export function validateSupport(body:any){
 if(!body||body.consent!==true||!topics.has(body.category)||typeof body.message!=='string')return null;
 const message=body.message.trim();
 if(message.length<10||message.length>2000||!/^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$/.test(body.request_id||'')||!/^[a-f0-9]{64}$/.test(body.device_token||''))return null;
 if(body.website)return null; // hidden honeypot, not a security boundary
 const d=body.diagnostics||{};
 return {request_id:body.request_id,category:body.category,message:message.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,''),screen:screens.has(d.screen)?d.screen:'support',browser:browsers.has(d.browser)?d.browser:'Other',viewport:typeof d.viewport==='string'&&/^\d{2,4}x\d{2,4}$/.test(d.viewport)?d.viewport:null,app_version:typeof d.app_version==='string'&&/^[a-z0-9.-]{1,48}$/.test(d.app_version)?d.app_version:'unknown'};
}
export async function supportAPI(api:string,req:Request,deps:SupportDeps){
 if(!['support-report','support-delete'].includes(api))return null;
 const expected=api==='support-delete'?'DELETE':'POST';
 if(req.method!==expected)return {status:405,body:{ok:false,error:'method_not_allowed'}};
 if(!(req.headers.get('content-type')||'').toLowerCase().startsWith('application/json'))return {status:415,body:{ok:false,error:'json_required'}};
 const declared=Number(req.headers.get('content-length')||0);if(declared>16000)return {status:413,body:{ok:false,error:'report_too_long'}};
 try{
  const reader=req.body?.getReader();let length=0,parts:Uint8Array[]=[];
  if(!reader)return {status:400,body:{ok:false,error:'invalid_report'}};
  while(true){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>16000){await reader.cancel();return {status:413,body:{ok:false,error:'report_too_long'}}}parts.push(value)}
  const bytes=new Uint8Array(length);let offset=0;for(const p of parts){bytes.set(p,offset);offset+=p.length}
  const body=JSON.parse(new TextDecoder().decode(bytes));
  if(api==='support-delete'){
   if(!/^[a-f0-9]{64}$/.test(body.device_token||'')||!/^[a-f0-9-]{36}$/.test(body.receipt||''))return {status:400,body:{ok:false,error:'invalid_report'}};
   const hash=await digest(body.device_token);
   const r=await fetch(deps.base()+'/rest/v1/fmn_support_reports?id=eq.'+body.receipt+'&device_hash=eq.'+hash,{method:'DELETE',headers:{...deps.headers(),prefer:'return=minimal'},signal:AbortSignal.timeout(10000)});
   return r.ok?{status:200,body:{ok:true}}:{status:503,body:{ok:false,error:'support_unavailable'}};
  }
  const clean=validateSupport(body);if(!clean)return {status:400,body:{ok:false,error:'invalid_report'}};
  const hash=await digest(body.device_token);
  const r=await fetch(deps.base()+'/rest/v1/rpc/fmn_submit_support',{method:'POST',headers:{...deps.headers(),'content-type':'application/json'},body:JSON.stringify({p_request:clean.request_id,p_device:hash,p_category:clean.category,p_message:clean.message,p_screen:clean.screen,p_browser:clean.browser,p_viewport:clean.viewport,p_version:clean.app_version}),signal:AbortSignal.timeout(12000)});
  if(!r.ok)return {status:503,body:{ok:false,error:'support_unavailable'}};
  const result=await r.json();
  if(result?.error==='rate_limited')return {status:429,body:{ok:false,error:'try_later'}};
  if(result?.ok!==true||typeof result.receipt!=='string')return {status:503,body:{ok:false,error:'support_unavailable'}};
  return {status:201,body:{ok:true,receipt:result.receipt}};
 }catch{return {status:503,body:{ok:false,error:'support_unavailable'}}}
}
