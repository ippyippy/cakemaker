"""Repair the existing app's inconsistent search paths. No backend or native changes."""
from pathlib import Path
import hashlib, json, re
root=Path('web')
files={n:(root/n).read_text() for n in ['index.html','journey.js','nearby-ui.js','journey.css','live-location.js','sw.js','data/station-information.json']}
if 'FMN_SHARED_SEARCH_20261009' in files['index.html']:
    print('Shared search repair already applied');raise SystemExit(0)
expected={'index.html':'08ca1e0131855d40c53244c83ac790ccbc5e0679','journey.js':'bcb3cfa65f63c469140a81513cb43698f6bf24a1','nearby-ui.js':'7b710877a7c22e0302c82cc71bf41a6dfd5135fd','live-location.js':'3fdfcea8cf27b7efd2e2454fa3c4b60132ef3371'}
for n,sha in expected.items():
    b=files[n].encode();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==sha, 'Review newer source before applying: '+n
original_assets=re.findall(r'data:image/[^\s\"\'\)<>]+',files['index.html'])
def replace(n,old,new):
    assert files[n].count(old)==1, 'Expected exactly one source anchor: '+n+' '+old[:100]
    files[n]=files[n].replace(old,new,1)
# Retain a complete nearby pool, but share the selected pool across map/list/Best Stop.
start=files['index.html'].index('function areaText(){');end=files['index.html'].index('\nfunction ',start+10)
files['index.html']=files['index.html'][:start]+'''// FMN_SHARED_SEARCH_20261009: filtering is a view, never deletion of provider records.
var allRanked=[];
function areaText(){
 var text=loc?(loc.label||"Selected area"):"Choose location";
 ["areaLabel","topArea","mapArea"].forEach(function(id){if($(id))$(id).textContent=text});
 summary=null;ranked=[];allRanked=[];
 if(!loc||!rows.length){if(!loc)clearMapMarkers();return null}
 var pool=rows.map(function(x){
  var distance=dkm(+loc.lat,+loc.lng,+x.latitude,+x.longitude),price=+x.price;
  if(!Number.isFinite(distance)||!Number.isFinite(price)||distance>prefs.radius||price<=0)return null;
  var road=distance*1.18,travel=road*2*prefs.economy/100*(price/100);
  return Object.assign({},x,{distance:distance,road:road,travel:travel,effective:((prefs.tank*price/100)+travel)/prefs.tank*100,etaMin:Math.max(2,Math.round(road/45*60))});
 }).filter(Boolean);
 var comparable=pool.filter(function(x){return !priceNeedsReview(x)}),prices=comparable.map(function(x){return +x.price}).sort(function(a,b){return a-b}),median=prices.length?prices[Math.floor(prices.length/2)]:null;
 pool.forEach(function(x){x.saving=median===null||priceNeedsReview(x)?0:prefs.tank*(median-x.price)/100-x.travel});
 allRanked=pool.sort(function(a,b){return Number(priceNeedsReview(a))-Number(priceNeedsReview(b))||a.effective-b.effective||a.price-b.price||a.distance-b.distance});
 ranked=window.FMNNearbyUI?FMNNearbyUI.select(allRanked,prefs):allRanked;
 var eligible=ranked.filter(function(x){return !priceNeedsReview(x)});
 if(!eligible.length)return null;
 var best=eligible.slice().sort(function(a,b){return a.effective-b.effective||a.price-b.price||a.distance-b.distance})[0];
 summary={best:best,cheapest:eligible.slice().sort(function(a,b){return a.price-b.price||a.distance-b.distance})[0],nearest:ranked.slice().sort(function(a,b){return a.distance-b.distance})[0],count:ranked.length,median:median};return summary;
}'''+files['index.html'][end:]
replace('index.html','function renderOptions(group){var source=Array.isArray(group)?group:ranked;','function renderOptions(group){var source=Array.isArray(group)?group:allRanked;')
replace('index.html','var message=ranked.length?"Nearby prices need checking.','var message=allRanked.length&&!ranked.length&&window.FMNNearbyUI?FMNNearbyUI.emptyMessage():ranked.length?"Nearby prices need checking.')
replace('index.html','$("sheetAlts").innerHTML=ranked.length?', '''if(allRanked.length&&!ranked.length&&window.FMNNearbyUI){var action=$("sheetMain").querySelector('button');if(action){action.removeAttribute('onclick');action.disabled=false;action.textContent='Review filters';action.onclick=FMNNearbyUI.openFilters;}}
  $("sheetAlts").innerHTML=ranked.length?''')
replace('index.html','el.classList.toggle("best",x===ranked[0]&&!priceNeedsReview(x));','el.classList.toggle("best",!!summary&&String(x.station_id)===String(summary.best.station_id)&&!priceNeedsReview(x));')
replace('index.html','window.FMNNearbyApp={getLocation:', '''window.FMNNearbyApp={refreshResults:function(){render();if(document.body.dataset.page==='options')renderOptions()},getLocation:''')
# More explicit map counter; sources remain unchanged in rows/allRanked.
replace('index.html','ranked.length+" station"+(ranked.length===1?"":"s")+" · View all"','ranked.length+" station"+(ranked.length===1?"":"s")+(allRanked.length!==ranked.length?" · filtered":"")+" · View all"')
# A destination change event must not be confused with reopening or rendering the modal.
replace('journey.js',"function renderDestination(){document.dispatchEvent(new Event('fmn:destination'));", "function renderDestination(reason){document.dispatchEvent(new CustomEvent('fmn:destination',{detail:{reason:reason||'display'}}));")
replace('journey.js',"const saved=writeDestination();renderDestination();", "const saved=writeDestination();renderDestination('selected');")
replace('journey.js',"app.toast(saved?'Destination saved. Choose your search location below.':'Destination set for this session; device storage is unavailable.');", "app.toast(!saved?'Destination set for this session; device storage is unavailable.':destination.manual?'Saved for Maps directions only. Choose a coordinate suggestion to filter stations.':'Destination selected. Map and results now filter towards it by direction, not a road route.');")
# Two clear actions intentionally remove the direction constraint, but keep access/deal preferences.
files['journey.js']=files['journey.js'].replace("destination=null;writeDestination();renderDestination();", "destination=null;writeDestination();renderDestination('cleared');").replace("destination=null;writeDestination();stopSearch();renderDestination();", "destination=null;writeDestination();stopSearch();renderDestination('cleared');")
replace('journey.js','Directions can continue via your chosen fuel stop. Use Nearby Filters → Destination direction to narrow the list approximately toward this destination. This is not road-route or truck-access verification.','Choosing an area suggestion turns on the same destination-direction filter for the map, Nearby list and Best Stop. This uses geography, not road-route or truck-access verification. You can turn it off in Filters.')
replace('journey.js','const p=await core.locate(navigator.geolocation,{signal});', '''root.FMNLiveLocation?.stop();
const p=await core.locate(navigator.geolocation,{signal,onQuality:info=>{if(id===sequence)status(info.code==='precision'?'Your phone is returning approximate location (±'+Math.round(info.accuracy)+' m). Waiting for precise GPS. Check Location permission help.':'Waiting for a fresh precise GPS position…','pending');}});''')
replace('journey.js',"status('Location found.','ready');if(p.accuracy>1000)app.toast('Approximate location. Search a suburb for a more specific area.');", "status('Precise location found (reported ±'+Math.round(p.accuracy)+' m).','ready');")
replace('journey.js',"const messages={1:'Location is blocked.", "const messages={precision:'Only approximate location was supplied. Enable Precise location for both this site and your browser, then retry. Your search location has not been moved.',1:'Location is blocked.")
replace('journey.js','Android: turn on Location in phone Settings. Allow location for Chrome or your browser under app permissions. In Chrome, open Settings → Site settings → Location and allow this FillMeNow address.', 'Android: turn on phone Location. In Settings → Apps → Chrome (or your browser) → Permissions → Location, enable Use precise location. Also open this same FillMeNow address → site information → Permissions → Location, allow it and choose Precise if offered. Both permissions matter.')
a=files['journey.js'].index('function locate(geo,options={})');b=files['journey.js'].index('\nreturn Object.freeze(',a)
files['journey.js']=files['journey.js'][:a]+'''function locate(geo,options={}){return new Promise((resolve,reject)=>{
 let done=false,timer,watch=null,watchAssigned=false,lastIssue=null;
 const signal=options.signal,set=options.setTimeout||setTimeout,clear=options.clearTimeout||clearTimeout,now=options.now||Date.now;
 function finish(error,point){if(done)return;done=true;clear(timer);signal?.removeEventListener('abort',abort);if(watchAssigned)geo.clearWatch(watch);if(error)reject(error);else resolve(point);}
 function abort(){finish({name:'AbortError'});}
 function quality(issue){lastIssue=issue;if(typeof options.onQuality==='function')options.onQuality(issue);}
 function received(position){if(done)return;const c=position?.coords,t=position?.timestamp;
  if(!c||!Number.isFinite(c.latitude)||!Number.isFinite(c.longitude)||Math.abs(c.latitude)>90||Math.abs(c.longitude)>180||!Number.isFinite(c.accuracy)||c.accuracy<0||!Number.isFinite(t)){quality({code:2});return;}
  if(now()-t>10000||t-now()>5000){quality({code:3});return;}
  if(c.accuracy>50){quality({code:'precision',accuracy:c.accuracy});return;}
  finish(null,{lat:c.latitude,lng:c.longitude,accuracy:c.accuracy,timestamp:t});
 }
 function failed(e){if(done)return;if(e?.code===1)finish({code:1});else quality({code:e?.code===3?3:2});}
 if(signal?.aborted){abort();return;}signal?.addEventListener('abort',abort,{once:true});
 timer=set(()=>finish(lastIssue||{code:3}),options.timeout||25000);
 try{const settings={enableHighAccuracy:true,timeout:20000,maximumAge:0};
  if(typeof geo?.watchPosition==='function'){watch=geo.watchPosition(received,failed,settings);watchAssigned=true;if(done)geo.clearWatch(watch);}
  else if(typeof geo?.getCurrentPosition==='function')geo.getCurrentPosition(received,failed,settings);
  else finish({code:2});
 }catch{finish({code:2});}
});}'''+files['journey.js'][b:]
# One refresh function so filters cannot update one screen and leave another misleadingly unfiltered.
replace('nearby-ui.js',"function reloadList(){if(document.body.dataset.page==='options')app.renderOptions();}", "function reloadList(){if(!app)return;if(app.refreshResults)app.refreshResults();else if(document.body.dataset.page==='options')app.renderOptions();}")
files['nearby-ui.js']=files['nearby-ui.js'].replace('app.renderOptions();','reloadList();').replace('app.renderOptions()}','reloadList()}')
# Undo accidental self recursion in the fallback above.
replace('nearby-ui.js',"else if(document.body.dataset.page==='options')reloadList();}","else if(document.body.dataset.page==='options')app.renderOptions();}")
replace('nearby-ui.js',"function select(rows,prefs){lastCount=rows.length;", "function select(rows,prefs){lastCount=rows.length;if(!app){lastList=rows;return rows;}")
replace('nearby-ui.js',"return lastList}\n", "updateScope();return lastList}\n")
replace('nearby-ui.js','These filters apply to the Nearby list; the map still shows the full search radius.','These filters apply together to map pins, the Nearby list and Best Stop. Filtered-out stations are not deleted.')
replace('nearby-ui.js',"baseSummary.textContent='Nearby list filters · map search remains '+context().radius+' km.'", "baseSummary.textContent='Map, Nearby list and Best Stop share these filters · search radius '+context().radius+' km.'")
replace('nearby-ui.js',"const n=el('span','Operator lists truck facilities · numeric clearance unconfirmed. ','nearby-facility');", "const n=el('span',x._facility.note+' ','nearby-facility');")
replace('nearby-ui.js',"parts.push('<div class=\"station-mini price-review\">'+a.label+'. Truck routing is not connected; confirm the approach, clearance and turning space before travel.</div>')", "parts.push('<div class=\"station-mini price-review\">'+a.label+'. Truck routing is not connected; confirm the approach, clearance and turning space before travel.</div>');const facility=C.facilityFor(row,prefs,catalog);if(facility){const n=el('div',facility.note+' ','station-mini nearby-facility'),link=el('a','Operator details');link.href=facility.source_url;link.target='_blank';link.rel='noopener noreferrer';n.append(link);parts.push(n.outerHTML)}")
extra='''
// Destination selection, not passive dialog rendering, activates the shared direction filter.
function destinationChanged(event){const d=window.FMNJourney?.getDestination(),reason=event?.detail?.reason;let changed=false;
 if(reason==='selected'){filters={...useFilters(),travel:d&&!d.manual?'towards':'all'};changed=true;write('fmnDestinationFilterV2',true);}
 else if(reason==='cleared'){filters={...useFilters(),travel:'all'};changed=true;write('fmnDestinationFilterV2',true);}
 else if(!read('fmnDestinationFilterV2',false)&&d&&!d.manual){filters={...useFilters(),travel:'towards'};changed=true;write('fmnDestinationFilterV2',true);}
 if(changed)write('fmnNearbyFilters',filters);reloadList();
}
function setAccess(value){filters={...useFilters(),access:value};write('fmnNearbyFilters',filters);reloadList();}
function activeText(){const f=useFilters(),d=window.FMNJourney?.getDestination(),parts=[];
 if(f.travel==='towards')parts.push(d&&!d.manual?'Towards '+d.label+' · direction only':'Choose a coordinate destination');
 else if(d)parts.push('Destination saved · direction filter off');
 if(C.truckMode(context()))parts.push(({height:'Recorded height '+(context().truck?.height||'—')+' m + allowance',matches:'Recorded full truck fit only',truckstops:'Operator-listed truck facilities',unknown:'Unrecorded clearance only',all:'All access · truck fit not confirmed'})[f.access]);
 if(f.minKm>0||f.maxKm!==context().radius)parts.push(f.minKm+'–'+f.maxKm+' km');if(f.deals!=='all')parts.push('Verified offer filter');
 return parts.join(' · ');
}
function positionScope(){const n=document.getElementById('mapFilterScope'),host=document.querySelector('#page-explore .map-shell'),gps=document.getElementById('followStatus');if(!n||!host)return;
 const box=host.getBoundingClientRect(),r=gps&&!gps.hidden?gps.getBoundingClientRect():null;n.style.top=(r&&r.height?Math.max(12,r.bottom-box.top+8):12)+'px';
}
function updateScope(){if(!app)return;const host=document.querySelector('#page-explore .map-shell');if(!host)return;let n=document.getElementById('mapFilterScope');
 if(!n){n=el('button',undefined,'map-filter-scope');n.id='mapFilterScope';n.type='button';n.onclick=openFilters;host.append(n);}
 const text=activeText();n.hidden=!text;n.textContent=text+' · '+lastList.length+' shown · Filters';n.setAttribute('aria-label',n.textContent);positionScope();
}
function truckActions(){let actions=document.getElementById('truckFilterActions');if(!actions){actions=el('div',undefined,'nearby-toolbar');actions.id='truckFilterActions';const facilities=el('button','Operator-listed truck facilities');facilities.type='button';facilities.id='filterTruckFacilities';facilities.onclick=()=>setAccess('truckstops');const height=el('button','Filter by recorded height');height.type='button';height.id='filterTruckHeight';height.onclick=()=>setAccess('height');actions.append(facilities,height);document.getElementById('truckAccessNotice').after(actions);}actions.hidden=!C.truckMode(context());}
'''
replace('nearby-ui.js','function afterRender(){toolbar();','function afterRender(){toolbar();') if False else None
replace('nearby-ui.js',"if(!lastList.length&&lastCount>0){", "truckActions();updateScope();\nif(!lastList.length&&lastCount>0){")
replace('nearby-ui.js','window.FMNNearbyUI={flushVehicle,',extra+'\nwindow.FMNNearbyUI={getFilters:useFilters,refresh:reloadList,flushVehicle,')
replace('nearby-ui.js',"document.addEventListener('fmn:destination',reloadList);", "document.addEventListener('fmn:destination',destinationChanged);window.addEventListener('resize',positionScope);setTimeout(()=>{const gps=document.getElementById('followStatus');if(gps)new MutationObserver(positionScope).observe(gps,{attributes:true,attributeFilter:['hidden'],childList:true,subtree:true});destinationChanged();},0);")
# Keep GPS target below the active filter scope as well as the GPS quality banner.
replace('live-location.js',"const y=bottom-top>=60?", "const scope=$('mapFilterScope');if(scope&&!scope.hidden){const sr=scope.getBoundingClientRect();top=Math.min(Math.max(top,sr.bottom+8),box.top+box.height*.45);}\n const y=bottom-top>=60?")
files['journey.css']+='''\n/* Shared filter state stays above markers, clear of right-hand map controls. */
body #page-explore .map-filter-scope{position:absolute;top:12px;left:10px;right:110px;z-index:1000;max-width:310px;border:1px solid #bfd4c5;border-radius:12px;background:#fff;color:#173e27;font-size:12px;line-height:1.4;text-align:left;padding:8px 10px;box-shadow:0 2px 7px #0002;overflow-wrap:anywhere;cursor:pointer}
body #mapFilterScope[hidden],body #truckFilterActions[hidden]{display:none!important}
body .nearby-facility{display:block;line-height:1.5;margin-top:8px;font-size:13px}body .nearby-facility a{display:inline-block;text-decoration:underline;margin-left:4px}
body #truckFilterActions{margin-top:0}body #truckFilterActions button{font-size:14px}
'''
replace('sw.js','fillmenow-web-v21-precise-follow-20261009','fillmenow-web-v22-shared-search-20261009')
# Exact existing station IDs matched against the public provider response and operator street address.
cat=json.loads(files['data/station-information.json'])
new=[('61477767','Shell Reddy Express Brendale','https://find.shell.com/au/fuel/10111160-shell-reddy-express-brendale/en_AU','Shell lists Truck Friendly, truck AdBlue and high-flow diesel at 2 Linkfield Road. Numerical canopy clearance is not published; confirm your loaded height with the operator.','+61734486837'),('61477703','Ampol Pinkenba Diesel Stop','https://locations.ampol.com.au/en/ampol-pinkenba-diesel-stop','Ampol identifies 19–27 Orient Avenue as National Truck Network and NatRoad Network. Numerical fuel-bay clearance is not published; this is not a dimension-match certificate.','1800240398'),('61401924','Ampol Foodary Strathpine','https://locations.ampol.com.au/en/ampol-foodary-strathpine','Ampol identifies 321 South Pine Road as National Truck Network and NatRoad Network. Numerical fuel-bay clearance is not published; confirm access for your vehicle.','+61732052783')]
for sid,name,url,note,phone in new:
 assert not any(str(r['station_id'])==sid for r in cat.get('facilities',[]))
 cat.setdefault('facilities',[]).append(dict(state='QLD',station_id=sid,kind='operator_listed_truck_stop',name=name,source_url=url,checked_at='2026-10-09T03:35:00Z',note=note,phone=phone))
assert cat['access']==[] and cat['offers']==[]
files['data/station-information.json']=json.dumps(cat,indent=2,ensure_ascii=False)+'\n'
assert re.findall(r'data:image/[^\s\"\'\)<>]+',files['index.html'])==original_assets
for n,text in files.items():(root/n).write_text(text)
print('Applied shared map/list/Best Stop filters, automatic destination selection, precise Search acquisition and three source-backed facilities. No numeric clearances fabricated.')
