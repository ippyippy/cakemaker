// Replaces only the existing map-marker implementation, inside its existing closure.
var stationPinById=new Map(),userLocationPin=null;
function markerProfile(){return {detailed:!!map&&map.getZoom()>=12,width:60,height:66}}
function clearMapMarkers(){
 if(Array.isArray(mapLayer))mapLayer.forEach(function(m){try{m.remove()}catch(e){}});
 mapLayer=[];individualPins=[];stationPinById.clear();userLocationPin=null;
 if(pinLeaders){pinLeaders.remove();pinLeaders=null}
}
function syncMapStationCount(){
 var e=$("mapStationCount");if(!e)return;
 e.textContent=!loc?"Choose area":ranked.length+" station"+(ranked.length===1?"":"s")+" · View all";
 e.setAttribute("role","button");e.tabIndex=0;e.setAttribute("aria-label",!loc?"Choose a search area":"View all "+ranked.length+" nearby stations");
 e.onclick=function(){if(loc)showPage("options");else openArea()};
 e.onkeydown=function(event){if(event.key==="Enter"||event.key===" "){event.preventDefault();e.click()}};
}
function renderMapMarkers(){
 syncMapStationCount();if(!map||!window.maplibregl)return;
 if(!loc){clearMapMarkers();return}
 if(!userLocationPin){var user=document.createElement("div");user.className="user-map-marker";user.setAttribute("aria-label","Your selected location");userLocationPin=new maplibregl.Marker({element:user,anchor:"center"}).setLngLat([+loc.lng,+loc.lat]).addTo(map)}
 else userLocationPin.setLngLat([+loc.lng,+loc.lat]);
 var seen=new Set(),profile=markerProfile();
 ranked.forEach(function(x){
  if(x.latitude==null||x.longitude==null||!Number.isFinite(+x.latitude)||!Number.isFinite(+x.longitude))return;
  var id=String(x.station_id);if(seen.has(id))return;seen.add(id);
  var pin=stationPinById.get(id),el;
  if(!pin){
   el=document.createElement("button");el.type="button";el.className="price-marker station-pin";el.dataset.stationId=id;el.dataset.stationCount="1";
   // Arrow extends 8px below the tile. Its tip, not the tile centre, owns the coordinate.
   var marker=new maplibregl.Marker({element:el,anchor:"bottom",offset:[0,-8],subpixelPositioning:true}).setLngLat([+x.longitude,+x.latitude]).addTo(map);
   pin={marker:marker,element:el,station:x,signature:""};stationPinById.set(id,pin);
   el.onclick=function(e){e.preventDefault();e.stopPropagation();openExactPin(id)};
  }
  el=pin.element;
  var sig=[x.brand,x.station_name,x.price,x.fuel_type].join("|");
  if(sig!==pin.signature){el.innerHTML=brandMark(x.brand,x.station_name)+'<span class="pin-price">'+(+x.price).toFixed(1)+'<small>¢</small></span>';pin.signature=sig}
  if(+pin.station.longitude!==+x.longitude||+pin.station.latitude!==+x.latitude)pin.marker.setLngLat([+x.longitude,+x.latitude]);
  pin.station=x;el.classList.toggle("best",x===ranked[0]);el.classList.toggle("pin-detail",profile.detailed);el.classList.toggle("pin-compact",!profile.detailed);
  el.dataset.latitude=String(x.latitude);el.dataset.longitude=String(x.longitude);el.dataset.fuelGrade=x.fuel_type||prefs.fuel;
  el.setAttribute("aria-label",x.station_name+", "+(x.fuel_type||prefs.fuel)+", "+(+x.price).toFixed(1)+" cents per litre. Open station details.");
  el.title=(x.brand||x.station_name)+" · "+(x.fuel_type||prefs.fuel)+" · "+(+x.price).toFixed(1)+"¢/L";
 });
 stationPinById.forEach(function(pin,id){if(!seen.has(id)){pin.marker.remove();stationPinById.delete(id)}});
 individualPins=Array.from(stationPinById.values());mapLayer=[userLocationPin].concat(individualPins.map(function(p){return p.marker}));
 layoutMapLabels();if(current)highlightStationPin(current.station_id);
}
function highlightStationPin(id){individualPins.forEach(function(pin){var selected=String(pin.station.station_id)===String(id);pin.element.classList.toggle("selected",selected);pin.element.setAttribute("aria-pressed",selected?"true":"false")})}
var mapLabelFrame=0;
function scheduleMapLabelLayout(){if(mapLabelFrame)return;mapLabelFrame=requestAnimationFrame(function(){mapLabelFrame=0;layoutMapLabels()})}
function layoutMapLabels(){
 if(!map||document.body.dataset.page!=="explore")return;
 var host=$("exploreMap"),profile=markerProfile(),count=0;
 individualPins.forEach(function(pin){
  var el=pin.element;if(el.classList.contains("pin-detail")!==profile.detailed){el.classList.toggle("pin-detail",profile.detailed);el.classList.toggle("pin-compact",!profile.detailed);pin.marker.setOffset([0,-8])}
  var p=map.project(pin.marker.getLngLat());if(p.x>=0&&p.y>=0&&p.x<=host.clientWidth&&p.y<=host.clientHeight)count++;
 });
 host.dataset.visibleStations=String(count);host.dataset.pinLayout="exact-coordinates";
}
function openExactPin(id){
 var chosen=stationPinById.get(String(id));if(!chosen)return;
 var box=chosen.element.getBoundingClientRect();
 var nearby=individualPins.filter(function(pin){var r=pin.element.getBoundingClientRect();return r.left<box.right&&r.right>box.left&&r.top<box.bottom&&r.bottom>box.top});
 if(nearby.length<2){openStation(id);highlightStationPin(id);return}
 // Keep the pins anchored. A chooser makes co-located/overlapping stations accessible without fake offsets.
 var overlay=$("exactStationChooser");if(!overlay){
  overlay=document.createElement("div");overlay.id="exactStationChooser";overlay.className="modal-bg";overlay.setAttribute("role","dialog");overlay.setAttribute("aria-modal","true");overlay.setAttribute("aria-label","Choose a station");
  overlay.innerHTML='<div class="modal popup-shell"><div class="popup-scroll"><h2>Choose a station</h2><p>These pins overlap at this zoom. Each arrow stays at its actual location.</p><div id="exactStationChoices"></div></div><div class="popup-footer"><button type="button" class="popup-back">‹ Back</button></div></div>';
  document.body.appendChild(overlay);overlay.querySelector(".popup-back").onclick=function(){overlay.classList.remove("open")};overlay.onclick=function(e){if(e.target===overlay)overlay.classList.remove("open")};
  overlay.addEventListener("keydown",function(e){if(e.key==="Escape"){e.preventDefault();e.stopPropagation();overlay.classList.remove("open");chosen.element.focus()}});
 }
 var list=$("exactStationChoices");list.innerHTML="";
 nearby.sort(function(a,b){return +a.station.price-+b.station.price}).forEach(function(pin){var x=pin.station,b=document.createElement("button");b.type="button";b.className="exact-station-choice";b.dataset.stationId=String(x.station_id);b.innerHTML=brandMark(x.brand,x.station_name)+'<span><b>'+esc(x.station_name)+'</b><small>'+esc(x.fuel_type||prefs.fuel)+' · '+(+x.price).toFixed(1)+'¢/L</small></span>';b.onclick=function(){overlay.classList.remove("open");openStation(x.station_id);highlightStationPin(x.station_id)};list.appendChild(b)});
 overlay.classList.add("open");list.querySelector("button").focus();
}
function installPopupFooters(){
 function footer(shell,button){
  if(!shell||!button||shell.querySelector(":scope > .popup-footer"))return;
  var parent=button.parentElement;if(parent&&/head/.test(parent.className)){var gap=document.createElement("span");gap.className="head-spacer";gap.setAttribute("aria-hidden","true");parent.insertBefore(gap,button)}
  button.remove();button.classList.add("popup-back");button.innerHTML='‹ <span>Back</span>';
  var bar=document.createElement("div");bar.className="popup-footer";bar.appendChild(button);
  if(shell.classList.contains("modal")){var scroll=document.createElement("div");scroll.className="popup-scroll";while(shell.firstChild)scroll.appendChild(shell.firstChild);shell.appendChild(scroll);shell.classList.add("popup-shell")}
  shell.appendChild(bar);
 }
 footer($("stationModal").querySelector(".modal"),$("stationClose"));
 footer($("areaModal").querySelector(".modal"),$("areaClose"));
 footer($("settingsDrawer"),$("drawerBack"));
 var desktop=$("desktopDetailBack");if(desktop)footer(desktop.closest(".desktop-station-panel"),desktop);
 var options=$("optionsBack");if(options){options.classList.add("bottom-page-back");options.innerHTML='‹ <span>Back</span>'}
 var exit=$("exitDrive");if(exit){exit.classList.add("bottom-page-back");exit.innerHTML='‹ <span>Back</span>'}
}
