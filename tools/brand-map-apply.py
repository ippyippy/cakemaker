"""Patch the existing map in place; preserve Dash, feed, prices and navigation coordinates."""
from pathlib import Path
import re,json,hashlib
p=Path('web/index.html');s=p.read_text();marker='FMN_INDIVIDUAL_BRANDS_20261008'
if marker in s:
 print('Individual brand pins already applied.');raise SystemExit(0)
images=re.findall(r'data:image/[^\s\"\)]+',s)
backend=re.search(r'const BACKEND=([^;]+);',s).group(0)
def section(start,end,replacement):
 global s
 a=s.index(start);b=s.index(end,a);s=s[:a]+replacement+'\n'+s[b:]
registry={x['file'].split('.')[0]:'/assets/brands/'+x['file'] for x in json.loads(Path('web/assets/brands/sources.json').read_text())['assets']}
section('const BRAND_LOGOS={','function brandKey(', 'const BRAND_LOGOS='+json.dumps(registry,separators=(',',':'))+';')
section('function brandKey(','function brandLabel(',r'''function brandKey(brand,name){
 // Prefer the feed's brand over historical or convenience-store names.
 function match(value){
  var v=String(value||"").toLowerCase();
  if(/\bbp\b/.test(v))return "bp";
  if(/\bcaltex\b/.test(v))return "caltex";
  if(/\bampol\b/.test(v))return "ampol";
  if(/\bshell\b/.test(v))return "shell";
  if(/7[\s-]*eleven/.test(v))return "seven";
  if(/\breddy\b/.test(v))return "reddy";
  if(/\bpuma\b/.test(v))return "puma";
  if(/\bmetro\b/.test(v))return "metro";
  if(/\bunited\b/.test(v))return "united";
  if(/\bliberty\b/.test(v))return "liberty";
  return "";
 }
 return match(brand)||match(name);
}''')
section('function brandMark(','function brandRank(',r'''function brandMark(brand,name){
 var key=brandKey(brand,name),url=BRAND_LOGOS[key]||"",label=brandLabel(brand,name),title=esc(brand||name||"Fuel station");
 if(!url){
  if(label)return '<span class="brand-mark wordmark" title="'+title+'"><span class="brand-word">'+esc(label)+'</span></span>';
  return '<span class="brand-mark generic" title="Fuel station"><span class="brand-fallback">'+pumpIcon()+'</span></span>';
 }
 return '<span class="brand-mark official-brand" data-brand="'+key+'" title="'+title+'"><img src="'+url+'" alt="" decoding="async" loading="eager" onerror="this.parentElement.classList.add(\'logo-failed\');this.remove()"><span class="brand-word logo-fallback">'+esc(label||"FUEL")+'</span></span>';
}''')
section('function markerProfile(){','function syncMapStationCount(){',r'''// FMN_INDIVIDUAL_BRANDS_20261008: no count clusters and no collision-based hiding.
var individualPins=[],pinLeaders=null;
function markerProfile(){
 var detailed=!!map&&map.getZoom()>=12;
 return {detailed:detailed,width:detailed?66:48,height:detailed?68:48};
}
function clearMapMarkers(){
 if(!Array.isArray(mapLayer))mapLayer=[];
 mapLayer.forEach(function(m){try{m.remove()}catch(e){}});mapLayer=[];individualPins=[];
 if(pinLeaders){pinLeaders.remove();pinLeaders=null}
}''')
section('function renderMapMarkers(){','function renderMap(){',r'''function renderMapMarkers(){
 syncMapStationCount();
 if(!map||!window.maplibregl)return;
 clearMapMarkers();if(!loc)return;
 var host=$("exploreMap"),w=host.clientWidth,h=host.clientHeight,profile=markerProfile();
 if(w<1||h<1)return;
 var user=document.createElement("div");user.className="user-map-marker";user.setAttribute("aria-label","Your selected location");
 mapLayer.push(new maplibregl.Marker({element:user,anchor:"center"}).setLngLat([+loc.lng,+loc.lat]).addTo(map));
 pinLeaders=document.createElementNS("http://www.w3.org/2000/svg","svg");pinLeaders.classList.add("station-pin-leaders");pinLeaders.setAttribute("aria-hidden","true");host.appendChild(pinLeaders);
 var seen=new Set();
 ranked.forEach(function(x){
  if(x.latitude==null||x.longitude==null||!Number.isFinite(+x.latitude)||!Number.isFinite(+x.longitude))return;
  var id=String(x.station_id);if(seen.has(id))return;seen.add(id);
  var q=map.project([+x.longitude,+x.latitude]);
  if(!Number.isFinite(q.x)||!Number.isFinite(q.y)||q.x<0||q.x>w||q.y<0||q.y>h)return;
  var el=document.createElement("button"),best=x===ranked[0];el.type="button";
  el.className="price-marker station-pin "+(profile.detailed?"pin-detail":"pin-compact")+(best?" best":"");
  el.dataset.stationId=id;el.dataset.stationCount="1";
  el.innerHTML=brandMark(x.brand,x.station_name)+'<span class="pin-price">'+(+x.price).toFixed(1)+'<small>¢</small></span>';
  el.setAttribute("aria-label",x.station_name+", "+(+x.price).toFixed(1)+" cents per litre. Open station details.");
  el.title=(x.brand||x.station_name)+" · "+(+x.price).toFixed(1)+"¢/L";
  el.onclick=function(e){e.preventDefault();e.stopPropagation();openStation(x.station_id);highlightStationPin(x.station_id)};
  var m=new maplibregl.Marker({element:el,anchor:"center"}).setLngLat([+x.longitude,+x.latitude]).addTo(map);
  var line=document.createElementNS("http://www.w3.org/2000/svg","line");pinLeaders.appendChild(line);
  individualPins.push({marker:m,element:el,station:x,line:line});mapLayer.push(m);
 });
 host.dataset.visibleStations=String(individualPins.length);layoutMapLabels();
 if(current)highlightStationPin(current.station_id);
}
function highlightStationPin(id){
 individualPins.forEach(function(pin){var selected=String(pin.station.station_id)===String(id);pin.element.classList.toggle("selected",selected);pin.element.setAttribute("aria-pressed",selected?"true":"false")});
}
var mapLabelFrame=0;
function scheduleMapLabelLayout(){
 if(mapLabelFrame)return;
 mapLabelFrame=requestAnimationFrame(function(){mapLabelFrame=0;layoutMapLabels()});
}
function layoutMapLabels(){
 if(!map||document.body.dataset.page!=="explore")return;
 var host=$("exploreMap"),w=host.clientWidth,h=host.clientHeight,profile=markerProfile(),pw=profile.width,ph=profile.height,gap=5,placed=[];
 if(!w||!h)return;
 if(pinLeaders){pinLeaders.setAttribute("viewBox","0 0 "+w+" "+h);pinLeaders.setAttribute("width",w);pinLeaders.setAttribute("height",h)}
 function clamp(v,min,max){return Math.max(min,Math.min(max,v))}
 function collides(point){return placed.some(function(a){return Math.abs(a.x-point.x)<pw+gap&&Math.abs(a.y-point.y)<ph+gap})}
 function inside(point){return point.x>=pw/2+4&&point.x<=w-pw/2-4&&point.y>=ph/2+4&&point.y<=h-ph/2-4}
 var ordered=individualPins.slice().sort(function(a,b){return String(a.station.station_id).localeCompare(String(b.station.station_id))});
 var crowded=false;
 ordered.forEach(function(pin){
  var q=map.project(pin.marker.getLngLat());
  pin.element.classList.toggle("pin-detail",profile.detailed);pin.element.classList.toggle("pin-compact",!profile.detailed);
  var origin={x:clamp(q.x,pw/2+4,w-pw/2-4),y:clamp(q.y,ph/2+4,h-ph/2-4)},chosen=origin;
  if(collides(origin)){
   chosen=null;
   // Fan out in screen space only: geographic coordinates and navigation stay exact.
   for(var ring=1;ring<=9&&!chosen;ring++){
    var steps=8*ring;
    for(var i=0;i<steps;i++){
     var angle=2*Math.PI*i/steps,candidate={x:origin.x+Math.cos(angle)*ring*(pw+gap),y:origin.y+Math.sin(angle)*ring*(ph+gap)};
     if(inside(candidate)&&!collides(candidate)){chosen=candidate;break}
    }
   }
   if(!chosen){
    var bestDistance=Infinity;
    for(var yy=ph/2+4;yy<=h-ph/2-4;yy+=ph+gap){for(var xx=pw/2+4;xx<=w-pw/2-4;xx+=pw+gap){
     var spot={x:xx,y:yy},dist=(xx-origin.x)**2+(yy-origin.y)**2;
     if(dist<bestDistance&&!collides(spot)){chosen=spot;bestDistance=dist}
    }}
   }
   // At continent-scale density there may be no free screen space. Never remove a station.
   if(!chosen){chosen=origin;crowded=true}
  }
  placed.push(chosen);var dx=chosen.x-q.x,dy=chosen.y-q.y;pin.marker.setOffset([dx,dy]);
  pin.element.style.visibility="visible";pin.element.tabIndex=0;pin.element.removeAttribute("aria-hidden");
  pin.line.setAttribute("x1",q.x);pin.line.setAttribute("y1",q.y);pin.line.setAttribute("x2",chosen.x);pin.line.setAttribute("y2",chosen.y);
  pin.line.style.display=Math.hypot(dx,dy)>8?"":"none";
 });
 host.dataset.pinLayout=crowded?"dense-zoom-in":"separated";
}
''')
# Preserve existing public interaction; select/close state is reflected on the map.
old='if(!x)return;current=x;';assert s.count(old)==1;s=s.replace(old,'if(!x)return;current=x;highlightStationPin(id);',1)
old=' current=null\n}';assert old in s;s=s.replace(old,' current=null;highlightStationPin(null)\n}',1)
old='Fuel prices can change. Confirm the displayed pump price before purchase."}$("drawerTitle")'
assert old in s
s=s.replace(old,'Fuel prices can change. Confirm the displayed pump price before purchase.<br><br><b>Independent comparison</b><br>Retailer names and logos identify stations only. FillMeNow is independent and is not endorsed by or affiliated with these retailers."}$("drawerTitle")',1)
css=r'''
/* FMN_INDIVIDUAL_BRANDS_20261008: logo-first pins; do not transform map coordinates in CSS. */
body .brand-mark.official-brand{position:relative!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;background:#fff!important;padding:3px!important;overflow:hidden!important}
body .brand-mark.official-brand img{position:static!important;inset:auto!important;display:block!important;width:100%!important;height:100%!important;max-width:100%!important;object-fit:contain!important;opacity:1!important;padding:0!important;border:0!important;background:transparent!important}
body .brand-mark.official-brand .logo-fallback{display:none!important}
body .brand-mark.official-brand.logo-failed .logo-fallback{display:block!important;font-size:9px!important;color:#15241b!important}
body .brand-mark.official-brand[data-brand="reddy"]{background:#cf1635!important}
body #page-explore .price-marker.station-pin{display:flex!important;flex-direction:column!important;justify-content:center!important;align-items:center!important;gap:2px!important;width:66px!important;min-width:66px!important;max-width:66px!important;height:68px!important;min-height:68px!important;max-height:68px!important;padding:4px!important;border:2px solid #fff!important;border-radius:12px!important;background:#fff!important;color:#15241b!important;box-shadow:0 2px 9px #15241b45!important;cursor:pointer!important;overflow:hidden!important;z-index:35!important;visibility:visible!important}
body #page-explore .price-marker.station-pin:before,body #page-explore .price-marker.station-pin:after{content:none!important;display:none!important}
body #page-explore .price-marker.station-pin .brand-mark{width:50px!important;height:35px!important;min-width:50px!important;flex:0 0 35px!important;border:0!important;border-radius:5px!important}
body #page-explore .price-marker.station-pin .pin-price{display:block!important;font-size:14px!important;font-weight:900!important;line-height:18px!important;letter-spacing:-.3px!important;color:#15241b!important}
body #page-explore .price-marker.station-pin .pin-price small{font-size:11px!important;font-weight:800!important}
body #page-explore .price-marker.station-pin.pin-compact{width:48px!important;min-width:48px!important;max-width:48px!important;height:48px!important;min-height:48px!important;max-height:48px!important;border-radius:10px!important;padding:3px!important}
body #page-explore .price-marker.station-pin.pin-compact .brand-mark{width:38px!important;min-width:38px!important;height:36px!important;flex-basis:36px!important}
body #page-explore .price-marker.station-pin.pin-compact .pin-price{display:none!important}
body #page-explore .price-marker.station-pin.best{border-color:#078439!important;background:#e9f9ee!important}
body #page-explore .price-marker.station-pin.selected{border-color:#184ece!important;box-shadow:0 0 0 3px #184ece55,0 3px 12px #15241b55!important;z-index:40!important}
body #page-explore .price-marker.station-pin:focus-visible{outline:3px solid #184ece!important;outline-offset:3px!important;z-index:41!important}
body #page-explore .price-marker.station-pin .brand-word{font-size:9px!important;line-height:1.2!important;letter-spacing:0!important;color:#15241b!important}
.station-pin-leaders{position:absolute;inset:0;pointer-events:none;z-index:20;overflow:hidden}
.station-pin-leaders line{stroke:#455b68;stroke-width:1.2;stroke-opacity:.75}
'''
i=s.index('</style>',s.index('<style id="fillmenow-public-readiness-2026-10-07">'));s=s[:i]+css+s[i:]
assert re.findall(r'data:image/[^\s\"\)]+',s)==images,'Dash and embedded images must remain identical'
assert re.search(r'const BACKEND=([^;]+);',s).group(0)==backend,'Backend must remain unchanged'
assert 'groups=clusterStations' not in s
p.write_text(s)
sw=Path('web/sw.js');w=sw.read_text();w=re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v13-brand-pins-20261008';",w,count=1)
a=w.index('const SHELL = ');b=w.index(';',a);shell=json.loads(w[a+14:b].replace("'",'"'));shell+=list(registry.values());w=w[:a]+'const SHELL = '+json.dumps(list(dict.fromkeys(shell)))+w[b:];sw.write_text(w)
print('Applied individual branded station pins; original Dash, feed and coordinates preserved.')
