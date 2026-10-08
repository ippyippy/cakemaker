"""Apply the reviewed nearby feature stage to the existing app, not a second app."""
from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text();before=s
if 'FMN_NEARBY_STAGE1_20261009' not in s:
 def rep(old,new):
  global s
  assert s.count(old)==1,('web anchor',old[:90],s.count(old));s=s.replace(old,new,1)
 rep('<script src="/assets/maplibre.js"></script>','<script src="/nearby-core.js"></script>\n<script src="/nearby-ui.js"></script>\n<script src="/assets/maplibre.js"></script>')
 rep('</head>','<link rel="stylesheet" href="/nearby.css">\n</head>')
 rep('function renderOptions(group){var list=Array.isArray(group)?group:ranked;','function renderOptions(group){var source=Array.isArray(group)?group:ranked;var list=window.FMNNearbyUI?FMNNearbyUI.select(source,prefs):source;')
 a=s.index('function renderOptions(');b=s.index('\nfunction openDrawer',a);r=s[a:b]
 r=r.replace(' return}', ' if(window.FMNNearbyUI)FMNNearbyUI.afterRender();return}',1)
 r=r.replace('var nextRadius=', 'if(!loading&&!failed&&loc&&source.length&&window.FMNNearbyUI)message=FMNNearbyUI.emptyMessage();\n var nextRadius=',1)
 assert r.endswith('.join("")}')
 r=r[:-1]+';if(window.FMNNearbyUI)FMNNearbyUI.afterRender();}'
 s=s[:a]+r+s[b:]
 rep('function navigate(x){if(x)window.open("https://www.google.com/maps/dir/?api=1&destination="+encodeURIComponent(x.latitude+","+x.longitude),"_blank","noopener")}','function navigate(x){if(!x)return;var proceed=function(){window.open("https://www.google.com/maps/dir/?api=1&destination="+encodeURIComponent(x.latitude+","+x.longitude),"_blank","noopener")};if(window.FMNNearbyUI)FMNNearbyUI.navigate(x,proceed);else if(!["truck","heavy"].includes(prefs.vehicle)||confirm("Truck dimensions are not checked by these standard directions. Continue?"))proceed()}')
 rep('metrics=stationMetricsHtml(x,d),','metrics=(window.FMNNearbyUI?FMNNearbyUI.badges(x,prefs):"")+stationMetricsHtml(x,d),')
 rep('function setPreset(k){prefs.vehicle=k;if(PRESETS[k])','function setPreset(k,applyValues){prefs.vehicle=k;if(applyValues!==false&&PRESETS[k])')
 rep('setPreset(prefs.vehicle||"custom");','setPreset(prefs.vehicle||"custom",false);')
 a=s.index('function setPreset(');b=s.index('\nfunction moreUI',a);part=s[a:b];part=part[:-1]+';if(window.FMNNearbyUI)FMNNearbyUI.syncVehicle();}';s=s[:a]+part+s[b:]
 a=s.index('$("saveVehicle").onclick=function(){');b=s.index(';if($("alertRadius"))',a)
 s=s[:a]+'$("saveVehicle").onclick=function(){if(window.FMNNearbyUI)FMNNearbyUI.saveVehicle()}'+s[b:]
 for old in ['prefs.radius=+this.value;','prefs.radius=+this.dataset.radius;','prefs.radius=nextRadius;']:
  s=s.replace(old,old+'if(window.FMNNearbyUI)FMNNearbyUI.radiusChanged(prefs.radius);')
 rep('"fmnSupportReceipt"].forEach','"fmnSupportReceipt","fmnNearbyFilters","fmnOfferEligibility"].forEach')
 rep('function areaText(){','function priceNeedsReview(x){var p=Number(x.price);return x.recommendation_eligible===false||!Number.isFinite(p)||p<100||p>500}\nfunction areaText(){')
 rep('var ps=a.map(function(x){return x.price})','var eligible=a.filter(function(x){return !priceNeedsReview(x)});ranked=a;if(!eligible.length){a.forEach(function(x){x.saving=0});return null}var ps=eligible.map(function(x){return x.price})')
 rep('x.saving=prefs.tank*(med-x.price)/100-x.travel','x.saving=priceNeedsReview(x)?0:prefs.tank*(med-x.price)/100-x.travel')
 rep('ranked=a.sort(function(x,y){return x.effective-y.effective','ranked=a.sort(function(x,y){return Number(priceNeedsReview(x))-Number(priceNeedsReview(y))||x.effective-y.effective')
 rep('var cheapest=a.slice().sort','var cheapest=eligible.slice().sort')
 rep('var message=priceStatus==="loading"?', 'var message=ranked.length?"Nearby prices need checking. View all stations to inspect the reported values.":priceStatus==="loading"?')
 rep('$("statCount").textContent="0";', '$("statCount").textContent=String(ranked.length);')
 rep('$("sheetAlts").innerHTML="";renderMap();renderDrive();return;', '$("sheetAlts").innerHTML=ranked.length?\'<button class="alt-all" onclick="FD.options()">View all stations</button>\':"";renderMap();renderDrive();return;')
 rep('el.classList.toggle("best",x===ranked[0]);','el.classList.toggle("best",x===ranked[0]&&!priceNeedsReview(x));el.classList.toggle("price-needs-review",priceNeedsReview(x));')
 rep('el.title=(x.brand||x.station_name)+','el.title=(priceNeedsReview(x)?"Price needs checking · ":"")+(x.brand||x.station_name)+')
 rep('return ranked.slice(start,start+limit).map','return ranked.filter(function(x){return !priceNeedsReview(x)}).slice(start,start+limit).map')
 rep('if(!summary){$("driveContent").innerHTML=\'<div class="drive-meta" style="margin-top:20px">Choose an area first.</div>\';return}','if(!summary){$("driveContent").innerHTML=\'<div class="drive-meta" style="margin-top:20px">\'+(ranked.length?"Nearby prices need checking before a Best Stop can be recommended.":"Choose an area first.")+\'</div>\';return}')
 bridge='''// FMN_NEARBY_STAGE1_20261009: one bridge to the existing app state and controls.
window.FMNNearbyApp={getPrefs:function(){return prefs},renderOptions:renderOptions,toast:toast,
 applyRadius:function(radius){if(radius>prefs.radius){prefs.radius=radius;persist();syncFuel();load()}},
 setVehicle:function(kind){setPreset(kind);render();},
 saveVehicle:function(value){Object.assign(prefs,value);persist();setPreset(prefs.vehicle,false);render();moreUI();syncSub();}
};
'''
 rep('function fmnOnboarding(){',bridge+'\nfunction fmnOnboarding(){')
 assert sorted(re.findall(r'data:image/[^\s\"\)]+',before))==sorted(re.findall(r'data:image/[^\s\"\)]+',s))
 p.write_text(s)
 sw=Path('web/sw.js');w=sw.read_text();w=re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v18-nearby-20261009';",w,count=1);w=w.replace('const SHELL = [','const SHELL = ["/nearby-core.js", "/nearby-ui.js", "/nearby.css", "/data/station-information.json", ',1);sw.write_text(w)
 p=Path('web/privacy.html');s=p.read_text();s=s.replace('<h2>Local storage</h2>','<h2>Nearby filters and truck settings</h2><p>Truck dimensions, vehicle configuration, Nearby filters and your offer-eligibility confirmations are stored on this device. They are not automatically attached to support reports or sent to a truck-routing service. Offers are shown only from a reviewed station-specific catalogue. Standard navigation does not apply truck dimensions.</p><p>Queensland area searches may send the suburb or postcode you type to the Queensland Government boundary service. These results are approximate area centres, not verified street addresses or station locations. Boundary data: © State of Queensland.</p><h2>Local storage</h2>');p.write_text(s)
 p=Path('web/support-chat.js');s=p.read_text();s=s.replace("if(/install|home screen/.test(trimmed.toLowerCase()))", "if(/filter|truck|dimension|height|width|weight|deal|offer|distance range|backtrack/.test(trimmed.toLowerCase()))message('Open Nearby Options → Filters for distance ranges, price/value sorting and verified station offers. Ranges are straight-line distances, not distance ahead on a route. In Vehicle Settings, turn on Truck mode and save your actual loaded dimensions. Access remains unverified unless measured records match. Truck-aware routing is not connected. Offer savings apply only when published conditions are met.','bot');\n else if(/install|home screen/.test(trimmed.toLowerCase()))");p.write_text(s)
p=Path('backend/fueldrop/index.ts');s=p.read_text()
if 'FMN_NEARBY_SAFETY_20261009' not in s:
 s='import { qldAreaSearch } from "./qld-area.ts";\n'+s
 a=s.index('async function geocode(');b=s.index('\nfunction adminApiKey',a);g=s[a:b]
 g=g.replace(' try{\n  const base=', ' let areaFailed=false;\n if(st==="QLD"){try{const areas=await qldAreaSearch(q);if(areas.length)return areas}catch{areaFailed=true}}\n try{\n  const base=',1)
 g=g.replace('if(!rr.ok)return[];', 'if(!rr.ok)throw new Error("area_unavailable");')
 g=g.replace('return [...groups.values()]','const candidates=[...groups.values()]',1)
 g=g.replace('}).slice(0,10);','}).slice(0,10);\n  if(!candidates.length&&areaFailed)throw new Error("area_unavailable");return candidates;',1)
 g=g.replace('}catch{return[]}', '}catch{throw new Error("area_unavailable")}')
 s=s[:a]+g+s[b:]
 marker='''// FMN_NEARBY_SAFETY_20261009: conservative review flag, never a guessed source-price correction.
function priceNeedsReview(row:any){const p=Number(row?.price);return row?.recommendation_eligible===false||!Number.isFinite(p)||p<100||p>500}
'''
 s=s.replace('function selectComparableFuelRows(',marker+'function selectComparableFuelRows(',1)
 old='if(!prior||Number(row.price)<Number(prior.price)||(Number(row.price)===Number(prior.price)&&row.fuel_type==="Diesel"&&prior.fuel_type!=="Diesel"))'
 new='if(!prior||(!priceNeedsReview(row)&&priceNeedsReview(prior))||(priceNeedsReview(row)===priceNeedsReview(prior)&&(Number(row.price)<Number(prior.price)||(Number(row.price)===Number(prior.price)&&row.fuel_type==="Diesel"&&prior.fuel_type!=="Diesel"))))'
 assert s.count(old)==1;s=s.replace(old,new,1)
 s=s.replace('const inRange=rows.map((x:any)=>{','const inRange=rows.map((x:any)=>{\n  if(priceNeedsReview(x))return null;',1)
 s=s.replace('const ranked=snap.rows.map((x:any)=>','const ranked=snap.rows.filter((x:any)=>!priceNeedsReview(x)).map((x:any)=>',1)
 s=s.replace('transaction_date_utc:x.transaction_date_utc,synced_at:x.synced_at','transaction_date_utc:x.transaction_date_utc,synced_at:x.synced_at,\n  recommendation_eligible:!priceNeedsReview(x),price_warning:priceNeedsReview(x)?"check_reported_price":null',1)
 s=s.replace('return json({candidates:[],error:"geocode_failed"})','return json({candidates:[],error:"geocode_failed"},503)',1)
 p.write_text(s)
print('Applied stage-one Nearby controls, truck profiles, price-review guards and Queensland area search.')
