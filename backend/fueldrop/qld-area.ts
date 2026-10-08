// Search centres, not station locations. Official QLD boundary geometry; no GPS is sent.
const areaCache=new Map<string,{at:number;rows:any[]}>();
export function areaCentre(rings:any){
 if(!Array.isArray(rings))return null;
 let best:any=null,bestArea=0;
 for(const ring of rings){if(!Array.isArray(ring)||ring.length<4||ring.length>10000)continue;
  if(ring.some((p:any)=>!Array.isArray(p)||!Number.isFinite(p[0])||!Number.isFinite(p[1])))continue;
  let a=0,x=0,y=0;for(let i=0;i<ring.length-1;i++){const p=ring[i],q=ring[i+1],cross=p[0]*q[1]-q[0]*p[1];a+=cross;x+=(p[0]+q[0])*cross;y+=(p[1]+q[1])*cross;}
  if(Math.abs(a)>bestArea){const lng=x/(3*a),lat=y/(3*a);if(lat>=-29.5&&lat<=-9&&lng>=137&&lng<=154.5){best={lat,lng};bestArea=Math.abs(a);}}
 }
 return best;
}
export async function qldAreaSearch(query:string){
 const q=String(query).trim().toUpperCase();if(!/^[A-Z0-9 -]{2,60}$/.test(q))return [];
 const now=Date.now(),cached=areaCache.get(q);if(cached&&now-cached.at<600000)return cached.rows;
 const postcode=/^\d{4}$/.test(q),field=postcode?'pc_pid':'locality',layer=postcode?'3':'2';
 const where=postcode?"pc_pid LIKE 'QLD"+q+"%'":"UPPER(locality) LIKE '"+q+"%'";
 const params=new URLSearchParams({f:'json',where,outFields:field,returnGeometry:'true',outSR:'4326',maxAllowableOffset:'0.001',resultRecordCount:'10',orderByFields:field+'.ASC'});
 // ArcGIS order syntax is a space, not PostgREST dot notation.
 params.set('orderByFields',field+' ASC');
 const base='https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Boundaries/AdministrativeBoundaries/MapServer/';
 const response=await fetch(base+layer+'/query?'+params,{signal:AbortSignal.timeout(7000),headers:{accept:'application/json'}});
 if(!response.ok)throw new Error('area_service_unavailable');const raw=await response.text();if(raw.length>2000000)throw new Error('area_response_too_large');const j=JSON.parse(raw);if(j.error||!Array.isArray(j.features))throw new Error('invalid_area_response');
 const rows=j.features.map((f:any)=>{const centre=areaCentre(f.geometry?.rings),name=f.attributes?.[field];if(!centre||typeof name!=='string')return null;if(postcode&&!name.startsWith('QLD'+q))return null;
  return {label:postcode?'Postcode '+q+' QLD · area centre':name+' QLD · area centre',state:'QLD',suburb:postcode?null:name,postcode:postcode?q:null,...centre,source:'Queensland Government boundary area centre'};
 }).filter(Boolean);
 if(areaCache.size>=256)areaCache.delete(areaCache.keys().next().value!);areaCache.set(q,{at:now,rows});return rows;
}
