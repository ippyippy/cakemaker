"""Repair existing app wiring: shared filtered results and fresh GPS everywhere.
No backend, source-coordinate, credential, native binary, or user data changes.
"""
from pathlib import Path
import json
ROOT=Path('web')
def one(s,old,new):
    if new in s and old not in s:return s
    assert s.count(old)==1, ('expected one replacement',old[:100],s.count(old))
    return s.replace(old,new,1)
p=ROOT/'index.html';s=p.read_text()
s=one(s,'function areaText(){','var nearbyTotal=0;\nfunction areaText(){')
s=one(s,'summary=null;ranked=[];if(!loc||!rows.length)', 'summary=null;ranked=[];nearbyTotal=0;if(!loc||!rows.length)')
s=one(s,'}).filter(Boolean);if(!a.length)return null;var eligible=a.filter(function(x){return !priceNeedsReview(x)});ranked=a;', '}).filter(Boolean);nearbyTotal=a.length;if(window.FMNNearbyUI)a=FMNNearbyUI.select(a,prefs);ranked=a;if(!a.length)return null;var eligible=a.filter(function(x){return !priceNeedsReview(x)});')
s=one(s,'ranked=a.sort(function(x,y){return Number(priceNeedsReview(x))-Number(priceNeedsReview(y))||x.effective-y.effective||x.price-y.price||x.distance-y.distance});var cheapest=', 'ranked=a;var best=eligible.slice().sort(function(x,y){return (x.effective-(x._dealSaving||0)/prefs.tank*100)-(y.effective-(y._dealSaving||0)/prefs.tank*100)||x.distance-y.distance})[0];var cheapest=')
s=one(s,'summary={best:ranked[0],cheapest:cheapest,nearest:nearest,count:a.length,median:med}', 'summary={best:best,cheapest:cheapest,nearest:nearest,count:a.length,median:med}')
s=one(s,'var list=window.FMNNearbyUI?FMNNearbyUI.select(source,prefs):source;var grouped=Array.isArray(group);', 'var list=source;var grouped=Array.isArray(group);if(window.FMNNearbyUI)FMNNearbyUI.describe(list,grouped?source.length:nearbyTotal);')
s=one(s,'if(!loading&&!failed&&loc&&source.length&&window.FMNNearbyUI)', 'if(!loading&&!failed&&loc&&nearbyTotal>0&&window.FMNNearbyUI)')
s=one(s,'var message=ranked.length?"Nearby prices need checking.', 'var message=nearbyTotal>0&&!ranked.length&&window.FMNNearbyUI?FMNNearbyUI.emptyMessage():ranked.length?"Nearby prices need checking.')
s=one(s,'$("sheetAlts").innerHTML=ranked.length?', '$("sheetAlts").innerHTML=(ranked.length||nearbyTotal)?')
s=one(s,'getPrefs:function(){return prefs},renderOptions:renderOptions,toast:toast,', 'getPrefs:function(){return prefs},renderOptions:function(){render();renderOptions()},toast:toast,')
s=one(s,'e.textContent=!loc?"Choose area":ranked.length+" station"+(ranked.length===1?"":"s")+" · View all";', 'e.textContent=!loc?"Choose area":ranked.length+" station"+(ranked.length===1?"":"s")+" · View all";if(loc&&window.FMNNearbyUI){var caption=FMNNearbyUI.mapCaption();if(caption){var sub=document.createElement("small");sub.className="map-filter-caption";sub.textContent=caption;e.appendChild(sub)}}')
s=one(s,'postcode:x.postcode||null,state:prefs.state};persist();closeArea();load();syncSub()}', 'postcode:x.postcode||null,state:prefs.state,accuracy:Number.isFinite(x.accuracy)?x.accuracy:null,locationSource:x.locationSource||"selected-area"};persist();closeArea();load();syncSub()}')
s=one(s,'setLoc({lat:point.lat,lng:point.lng,label:"Current location · "+detected});', 'setLoc({lat:point.lat,lng:point.lng,accuracy:point.accuracy,locationSource:"gps",label:"Current location · "+detected});')
s=one(s,'getLocation:function(){return loc},openArea:openArea,toast:toast,', 'getLocation:function(){return loc},openArea:openArea,closeArea:closeArea,toast:toast,')
p.write_text(s)
p=ROOT/'nearby-ui.js';s=p.read_text()
s=one(s,"function reloadList(){if(document.body.dataset.page==='options')app.renderOptions();}", "function reloadList(){if(app)app.renderOptions();}")
s=one(s,"function summary(n,total){", "function destinationLabel(){const d=window.FMNJourney?.getDestination();return d?d.label.replace(/ · area centre$/,''):''}\nfunction mapCaption(){const f=useFilters();return (f.travel==='towards'?'Toward '+destinationLabel()+' · direction only':C.truckMode(context())&&f.access!=='all'?accessLabel():'')}\nfunction accessLabel(){return ({all:'All stations · truck fit unchecked',truckstops:'Operator-listed truck-friendly',height:'Recorded height matches only',matches:'All recorded dimensions match',unknown:'Clearance not recorded'})[useFilters().access]}\nfunction describe(list,total){lastList=list;lastCount=total}\nfunction destinationChanged(){if(!app)return;const d=window.FMNJourney?.getDestination(),key=d?JSON.stringify([d.label,d.lat,d.lng,d.manual]):'';if(read('fmnDestinationFilterKey',null)!==key){filters={...useFilters(),travel:d&&!d.manual?'towards':'all'};write('fmnNearbyFilters',filters);write('fmnDestinationFilterKey',key);}reloadList()}\nfunction summary(n,total){")
s=s.replace("(f.travel==='towards'?' · toward destination (approximate)':'')", "(f.travel==='towards'?' · toward '+destinationLabel()+' (direction only)':' · all directions')")
s=s.replace('These filters apply to the Nearby list; the map still shows the full search radius.','The map, Nearby list, station count and Best Stop use these same filters within the search radius.')
s=s.replace('Use the Destination button on Nearby Options.', 'Use Destination and choose an area suggestion; a typed Maps-only address cannot filter these results.')
s=one(s,"function select(rows,prefs){lastCount=rows.length;", "function select(rows,prefs){if(!app)return rows;lastCount=rows.length;")
s=one(s,"baseSummary.textContent='Nearby list filters · map search remains '+context().radius+' km.'", "baseSummary.textContent='Same filtered stations on the map, in this list and in Best Stop · '+context().radius+' km search.'")
s=one(s,"note.textContent='Your truck: '", "note.textContent=accessLabel()+'. Your truck: '")
s=one(s,"if(!lastList.length&&lastCount>0){", "let shortcuts=document.getElementById('truckSearchChoices');if(!shortcuts){shortcuts=el('div',undefined,'truck-search-choices');shortcuts.id='truckSearchChoices';for(const [value,label]of [['truckstops','Truck-friendly facilities'],['height','Verified height matches']]){const b=el('button',label,'nearby-offer-button');b.type='button';b.dataset.access=value;b.onclick=()=>{filters={...useFilters(),access:value};write('fmnNearbyFilters',filters);reloadList()};shortcuts.append(b);}note.after(shortcuts);}shortcuts.hidden=!C.truckMode(context());shortcuts.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.access===useFilters().access)));\nif(!lastList.length&&lastCount>0){")
s=one(s,"const s=document.getElementById('nearbyFilterSummary');s.textContent=summary(lastList.length,lastCount);", "const s=document.getElementById('nearbyFilterSummary');s.textContent=summary(lastList.length,lastCount);const destButton=document.getElementById('nearbyDestination');if(destButton)destButton.textContent=destinationLabel()?'Destination: '+destinationLabel():'Destination';")
s=one(s,"main.append(n);}}if(x._offers.length)", "main.append(n);n.append(el('span',x._facility.note,'facility-evidence'));if(/^\\+?[0-9]{7,15}$/.test(x._facility.phone||'')){const phone=el('a','Call to confirm clearance','facility-phone');phone.href='tel:'+x._facility.phone;n.append(phone);}}}if(x._offers.length)")
s=one(s,"function badges(row,prefs){", "function escaped(value){const n=el('span',String(value||''));return n.innerHTML}\nfunction badges(row,prefs){")
s=one(s,"if(C.truckMode(prefs)){const a=C.truckAccess(row,prefs,catalog);", "if(C.truckMode(prefs)){const f=C.facilityFor(row,prefs,catalog);if(f){parts.push('<div class=\"station-mini operator-evidence\"><b>Operator lists truck-friendly facilities</b><p>'+escaped(f.note)+'</p><a href=\"'+escaped(f.source_url)+'\" target=\"_blank\" rel=\"noopener noreferrer\">Operator details</a>'+(/^\\+?[0-9]{7,15}$/.test(f.phone||'')?' · <a href=\"tel:'+escaped(f.phone)+'\">Call to confirm clearance</a>':'')+'</div>')}const a=C.truckAccess(row,prefs,catalog);")
s=one(s,"window.FMNNearbyUI={flushVehicle", "window.FMNNearbyUI={describe,mapCaption,destinationChanged,flushVehicle")
s=one(s,"document.addEventListener('fmn:destination',reloadList);", "document.addEventListener('fmn:destination',destinationChanged);setTimeout(destinationChanged,0);")
s=one(s,"return 'No stations match this distance range. Adjust or reset the Nearby filters.'", "if(f.travel==='towards')return 'No stations match the current filters toward '+destinationLabel()+'. This is direction-only filtering, not a checked road route. Change the filters or destination.';return 'No stations match this distance range. Adjust or reset the filters.'")
p.write_text(s)
p=ROOT/'journey.js';s=p.read_text()
s=s.replace("'Destination saved. Choose your search location below.'", "destination.manual?'Saved for external Maps only; choose a suggestion to filter stations.':'Destination saved. Map, Nearby and Best Stop now filter toward it by direction, not roads.'")
s=one(s,'Use Nearby Filters → Destination direction to narrow the list approximately toward this destination.', 'Choosing an area suggestion automatically filters the map, Nearby and Best Stop toward it. You can choose All directions in Filters. This uses approximate direction, not roads.')
s=one(s,"status('Location found.','ready');if(p.accuracy>1000)app.toast('Approximate location. Search a suburb for a more specific area.');", "status('Precise location found.','ready');")
s=one(s,"3:'Location took too long. Check the permission prompt and your phone Location setting, or search manually.',", "3:'A fresh precise location was not received. Check phone and site permissions or search manually.',coarse:'Your phone returned only an approximate location. The search area was not changed. Allow Precise for this site and your browser, then retry or start live GPS.',")
s=one(s,"{enableHighAccuracy:false,timeout:10000,maximumAge:60000}", "{enableHighAccuracy:true,timeout:10000,maximumAge:0}")
s=one(s,"finish(null,{lat:c.latitude,lng:c.longitude,accuracy:Number(c.accuracy)||0});", "const now=options.now?options.now():Date.now();if(!Number.isFinite(c.accuracy)||c.accuracy<0){finish({code:2});return;}if(c.accuracy>50){finish({code:'coarse',accuracy:c.accuracy});return;}if(!Number.isFinite(p.timestamp)||now-p.timestamp>10000||p.timestamp>now+5000){finish({code:3});return;}finish(null,{lat:c.latitude,lng:c.longitude,accuracy:c.accuracy,timestamp:p.timestamp});")
s=one(s,"function help(){const d=dialog('Allow location')", "function help(){if(root.FMNLiveLocation?.help){root.FMNLiveLocation.help();return;}const d=dialog('Allow location')")
s=one(s,"$('locationCancel').onclick=()=>cancelLocation(true);", "const follow=element('button','Start precise live GPS','journey-result');follow.type='button';follow.id='searchStartLiveGps';follow.onclick=()=>{cancelLocation();app.closeArea();root.FMNLiveLocation?.start();};controls.append(follow);$('locationCancel').onclick=()=>cancelLocation(true);")
p.write_text(s)
p=ROOT/'nearby.css';s=p.read_text();marker='/* Shared search result scope — 20261009 */'
if marker not in s:s+='\n'+marker+'\n.map-filter-caption{display:block;font-size:12px;line-height:1.35;font-weight:600;max-width:220px;white-space:normal;margin-top:3px}.truck-search-choices{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}.truck-search-choices[hidden]{display:none!important}.truck-search-choices button[aria-pressed=true]{background:#087532;color:white}.facility-evidence{display:block;font-size:13px;line-height:1.45;margin:6px 0}.facility-phone{display:block;min-height:36px;padding-top:8px}.operator-evidence p{margin:6px 0}#nearbyDestination{max-width:100%;overflow-wrap:anywhere}\n'
p.write_text(s)
p=ROOT/'sw.js';s=p.read_text();s=one(s,"fillmenow-web-v21-precise-follow-20261009","fillmenow-web-v22-unified-destination-20261009");p.write_text(s)
# Published operator descriptions, never numeric clearance measurements.
p=ROOT/'data/station-information.json';j=json.loads(p.read_text());records={str(x['station_id']):x for x in j.get('facilities',[])}
for sid,slug,phone,note in [
 ('61401537','10111462-shell-reddy-express-virginia','+61736388708','Shell lists Truck Friendly and High Flow Diesel at 1890 Sandgate Road, Virginia. Fuel-bay height is not published; confirm your full vehicle with the operator.'),
 ('61402436','10111406-shell-reddy-express-nudgee','+61737417815','Shell lists truck-friendly access, high-flow diesel, truck AdBlue and truck parking at 1097 Nudgee Road. No numerical fuel-bay clearance is published.'),
 ('61401428','10111437-shell-reddy-express-rocklea','+61735684612','Shell lists truck-friendly access, high-flow diesel, truck AdBlue, parking and showers at 1728 Ipswich Road. Confirm your full vehicle; no numerical canopy height is published.'),
 ('61401753','10111290-shell-reddy-express-goodna','+61734476814','Shell lists truck-friendly access, high-flow diesel and truck parking at 2 Railway Terrace, Goodna. Numerical fuel-bay clearance is not published.'),
 ('61401929','10111169-shell-reddy-express-belmont-qld','+61735693633','Shell lists Truck Friendly and High Flow Diesel at 11 London Road, Belmont. Numerical fuel-bay clearance is not published.'),
 ('61477774','10111234-shell-reddy-express-coomera-truck-stop','+61728105615','Shell lists truck-friendly access, high-flow diesel, truck AdBlue, parking and showers at 487 Old Pacific Highway. Numerical fuel-bay clearance is not published.'),
 ('61478190','10120869-shell-reddy-express-currumbin','+61756016754','Shell lists truck-friendly access, high-flow diesel, truck AdBlue, parking and showers at 1 Stewart Road, Currumbin Waters. Numerical fuel-bay clearance is not published.')]:
 records[sid]={'station_id':sid,'state':'QLD','kind':'operator_listed_truck_stop','source_url':'https://find.shell.com/au/fuel/'+slug+'/en_AU','checked_at':'2026-10-09T02:20:00Z','note':note,'phone':phone}
j['facilities']=list(records.values());assert not j['access'];p.write_text(json.dumps(j,indent=2)+'\n')
print('Unified map/list/Best Stop filters, automatic destination activation, fresh precise Search and operator evidence applied.')
