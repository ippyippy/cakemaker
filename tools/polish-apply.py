"""Guarded repairs to the existing FillMeNow web app; no production release."""
from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text()
original_images=re.findall(r'data:image/[^\s"\')]+',s)
def fn(name,replacement):
    global s
    start=s.index('function '+name+'(');end=s.index('\nfunction ',start+10)
    s=s[:start]+replacement.rstrip()+'\n'+s[end:]
if 'FMN_COLLISION_REPAIR_20261007' not in s:
    fn('markerProfile','function markerProfile(){return {clusterPx:0,cls:"zoom-locked"}}')
    fn('clusterStations','''function clusterStations(points,pixelSize){
 // Reserve the complete label footprint, including its pointer and spacing.
 // Keep each group anchored at its best-ranked station, not a moving centroid.
 // Keep grouping enabled even at maximum zoom for co-located stations.
 if(!map)return [];
 var groups=[];
 points.forEach(function(x){
  if(!Number.isFinite(+x.longitude)||!Number.isFinite(+x.latitude))return;
  var q=map.project([+x.longitude,+x.latitude]);
  if(!Number.isFinite(q.x)||!Number.isFinite(q.y))return;
  var g=groups.find(function(a){return Math.abs(a.x-q.x)<126&&Math.abs(a.y-q.y)<84});
  if(g){g.items.push(x);return}
  groups.push({items:[x],lng:+x.longitude,lat:+x.latitude,x:q.x,y:q.y});
 });
 return groups;
}''')
    fn('renderMapMarkers','''function renderMapMarkers(){
 if(!map||!loc||!window.maplibregl)return;
 clearMapMarkers();
 var user=document.createElement("div");user.className="user-map-marker";
 user.setAttribute("aria-label","Your selected location");
 mapLayer.push(new maplibregl.Marker({element:user,anchor:"center"}).setLngLat([+loc.lng,+loc.lat]).addTo(map));
 var groups=clusterStations(ranked,0),countEl=$("mapStationCount");
 if(countEl){
  countEl.textContent=ranked.length+" station"+(ranked.length===1?"":"s")+" · View all";
  countEl.setAttribute("role","button");countEl.tabIndex=0;
  countEl.setAttribute("aria-label","View all "+ranked.length+" nearby stations");
  countEl.onclick=function(){showPage("options")};
  countEl.onkeydown=function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();showPage("options")}};
 }
 groups.forEach(function(g){
  var el=document.createElement("button"),best=g.items.indexOf(ranked[0])>=0;
  el.type="button";el.dataset.stationCount=String(g.items.length);
  if(g.items.length===1){
   var x=g.items[0];el.className="price-marker zoom-locked"+(best?" best":"");
   el.innerHTML=brandMark(x.brand,x.station_name)+x.price.toFixed(1)+"¢";
   el.setAttribute("aria-label",x.station_name+" "+x.price.toFixed(1)+" cents per litre");
   el.onclick=function(e){e.preventDefault();e.stopPropagation();openStation(x.station_id)};
  }else{
   var min=Math.min.apply(null,g.items.map(function(x){return +x.price}));
   el.className="station-cluster"+(best?" contains-best":"");
   el.innerHTML='<b>'+g.items.length+' stations</b><small>from '+min.toFixed(1)+'¢</small>';
   el.setAttribute("aria-label","Compare "+g.items.length+" grouped stations, from "+min.toFixed(1)+" cents per litre"+(best?", includes Best Stop":""));
   el.onclick=function(e){e.preventDefault();e.stopPropagation();showPage("options");renderOptions(g.items)};
  }
  mapLayer.push(new maplibregl.Marker({element:el,anchor:"bottom",offset:[0,-8]}).setLngLat([g.lng,g.lat]).addTo(map));
 });
 scheduleMapLabelLayout();
}
var mapLabelFrame=0;
function scheduleMapLabelLayout(){
 if(mapLabelFrame)return;
 mapLabelFrame=requestAnimationFrame(function(){mapLabelFrame=0;layoutMapLabels()});
}
function layoutMapLabels(){
 if(!map||document.body.dataset.page!=="explore")return;
 var host=$("exploreMap"),bounds=host.getBoundingClientRect(),placed=[];
 function overlaps(a,b){return a.left<b.right+6&&a.right>b.left-6&&a.top<b.bottom+6&&a.bottom>b.top-6}
 var reserved=Array.from(document.querySelectorAll('.map-overlay>*,.map-station-count,.map-tools-bottom button,.maplibregl-ctrl,.mobile-sheet')).filter(function(e){var c=getComputedStyle(e);return e.getClientRects().length&&c.visibility!=="hidden"&&c.display!=="none"}).map(function(e){return e.getBoundingClientRect()});
 var markers=Array.from(host.querySelectorAll('.price-marker,.station-cluster'));
 markers.sort(function(a,b){return Number(b.classList.contains("best")||b.classList.contains("contains-best"))-Number(a.classList.contains("best")||a.classList.contains("contains-best"))});
 markers.forEach(function(e){
  var r=e.getBoundingClientRect();
  var hidden=r.left<bounds.left+4||r.right>bounds.right-4||r.top<bounds.top+4||r.bottom>bounds.bottom-4||reserved.some(function(a){return overlaps(r,a)})||placed.some(function(a){return overlaps(r,a)});
  e.style.visibility=hidden?"hidden":"visible";e.tabIndex=hidden?-1:0;
  e.setAttribute("aria-hidden",hidden?"true":"false");if(!hidden)placed.push(r);
 });
}''')
    old='map.on("zoomend",function(){renderMapMarkers()});'
    assert s.count(old)==1
    s=s.replace(old,'map.on("moveend",renderMapMarkers);\n map.on("move",scheduleMapLabelLayout);\n map.on("resize",renderMapMarkers);')
    s=s.replace('window.addEventListener("resize",refreshViewportMap);','window.addEventListener("resize",refreshViewportMap);\ndocument.addEventListener("transitionend",function(e){if(e.target.id==="mobileSheet")scheduleMapLabelLayout()});')
    a=s.index('function renderOptions(){');b=s.index('\nfunction ',a+10)
    part=s[a:b].replace('function renderOptions(){','function renderOptions(group){var list=Array.isArray(group)?group:ranked;var grouped=Array.isArray(group);')
    part=part.replace('ranked.length','list.length').replace('ranked.map(','list.map(')
    part=part.replace('$("optionsList").innerHTML=list.map(','''var reset=$("mapGroupReset");if(!reset){reset=document.createElement("button");reset.id="mapGroupReset";reset.type="button";reset.className="btn btn-soft full-btn";reset.textContent="Show all nearby stations";reset.onclick=function(){renderOptions()};$("optionsList").before(reset)}reset.hidden=!grouped;if(grouped)$("optionsSummary").textContent=list.length+" grouped stations · ranked by estimated total trip cost.";$("optionsList").innerHTML=list.map(''')
    part=part.replace('if(!list.length){','if(!grouped&&$("mapGroupReset"))$("mapGroupReset").hidden=true;if(!list.length){')
    s=s[:a]+part+s[b:]
    old='function toast(t){$("toast").textContent=t;$("toast").classList.add("show");setTimeout(function(){$("toast").classList.remove("show")},2200)}'
    new='var toastTimer=null;function toast(t){clearTimeout(toastTimer);$("toast").textContent=t;$("toast").classList.add("show");toastTimer=setTimeout(function(){$("toast").classList.remove("show")},4000)}'
    assert old in s;s=s.replace(old,new)
    s=s.replace('if(!j||j.ok!==true||!Array.isArray(j.rows))','if(!j||j.ok!==true||j.error||j.connected===false||!Array.isArray(j.rows))')
    css='''
/* FMN_COLLISION_REPAIR_20261007: one measured footprint at every breakpoint. */
body #page-explore .price-marker.zoom-locked,body #page-explore .station-cluster{
 width:112px!important;min-width:112px!important;max-width:112px!important;
 height:64px!important;min-height:64px!important;max-height:64px!important;
 box-sizing:border-box!important;padding:8px!important;border-radius:14px!important;
 font-size:14px!important;line-height:1.2!important;overflow:visible!important;
}
body #page-explore .price-marker.zoom-locked{display:flex!important;gap:6px!important;justify-content:center!important}
body #page-explore .station-cluster{position:absolute!important;display:flex!important;flex-direction:column!important;gap:3px!important;border:2px solid #fff!important}
body #page-explore .station-cluster b{font-size:14px!important;white-space:nowrap!important}
body #page-explore .station-cluster small{font-size:12px!important;color:#fff!important;white-space:nowrap!important;margin:0!important}
body #page-explore .station-cluster.contains-best{background:#16c94b!important;color:#10200c!important}
body #page-explore .station-cluster.contains-best small{color:#10200c!important}
body #page-explore .price-marker .brand-mark{width:26px!important;height:26px!important;flex-basis:26px!important}
body .map-station-count{cursor:pointer;font-size:12px!important;line-height:1.3!important;min-height:36px!important;display:flex!important;align-items:center!important}
body #mapGroupReset{margin:0 0 14px!important;min-height:44px!important;font-size:14px!important}
body #mapGroupReset[hidden]{display:none!important}
body .toast{opacity:1!important;visibility:hidden;transition:none!important;transform:translateX(-50%)!important;background:#14201a!important;color:#fff!important}
body .toast.show{visibility:visible}
body .drive{overflow-y:auto!important;overscroll-behavior:contain}
body .drive-body{min-height:0;padding:20px 18px calc(24px + env(safe-area-inset-bottom))!important}
body .drive-card{min-width:0;max-width:100%}
body .drive-price{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;font-size:clamp(48px,12vw,82px)!important;letter-spacing:-2px!important}
body .drive-station{font-size:clamp(20px,5vw,28px)!important;overflow-wrap:anywhere}
body .drive-meta,body .drive-small{font-size:14px!important;line-height:1.5!important;color:#cbd8cf!important}
body .drive-exit{min-height:44px!important;min-width:60px!important;font-size:14px!important}
@media(max-height:600px){body .drive-mascot{width:60px;height:50px}body .drive-price{font-size:48px!important}body .drive-body{display:block!important}body .drive-card{margin:auto}}
'''
    idx=s.index('<style id="fillmenow-public-readiness-2026-10-07">');end=s.index('</style>',idx)
    s=s[:end]+css+s[end:]
    assert re.findall(r'data:image/[^\s"\')]+',s)==original_images,'Mascot/image bytes must not change'
    p.write_text(s)
    sw=Path('web/sw.js');sw.write_text(re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v6-20261007';",sw.read_text(),count=1))
print('Collision-aware grouping, toast and Drive Mode repairs applied. Images preserved.')
