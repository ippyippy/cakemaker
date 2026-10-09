"""Apply reviewed changes to existing web files. No backend, secrets or provider records are modified."""
from pathlib import Path
import json
ROOT=Path('.')
def edit(file,old,new):
 p=ROOT/file;s=p.read_text();assert s.count(old)==1,(file,old[:140],s.count(old));p.write_text(s.replace(old,new,1))
def func(file,name,new):
 p=ROOT/file;s=p.read_text();a=s.index('function '+name+'(');b=s.find('\nfunction ',a+10);assert b>a;p.write_text(s[:a]+new+'\n'+s[b:])
func('web/index.html','setPreset',r'''function setPreset(k,applyValues){
 var previous=prefs.vehicle,profiles=prefs.vehicleProfiles||{};
 if(applyValues!==false&&k!==previous){profiles[previous]={tank:prefs.tank,economy:prefs.economy,truck:prefs.truck};var remembered=profiles[k];if(remembered){prefs.tank=remembered.tank;prefs.economy=remembered.economy;if(remembered.truck)prefs.truck=remembered.truck}else if(PRESETS[k]){prefs.tank=PRESETS[k].tank;prefs.economy=PRESETS[k].economy}prefs.vehicleProfiles=profiles;}
 prefs.vehicle=k;$('tankInput').value=prefs.tank;$('economyInput').value=prefs.economy;
 Array.from(document.querySelectorAll('.preset')).forEach(function(b){b.classList.toggle('active',b.dataset.preset===k)});syncVehicleLabel();
 if(applyValues!==false){try{persist()}catch(e){toast('Settings changed for this session, but device storage is unavailable.')}}
 if(window.FMNNearbyUI)FMNNearbyUI.syncVehicle();
}''')
edit('web/index.html','prefs.state=this.value;prefs.fuel=FUELS[prefs.state][0];loc=null;', 'if(prefs.state===this.value)return;prefs.state=this.value;if(FUELS[prefs.state].indexOf(prefs.fuel)<0)prefs.fuel=FUELS[prefs.state][0];loc=null;')
edit('web/index.html','$("modalFuel").onchange=function(){prefs.fuel=this.value;persist();syncFuel()}', '$("modalFuel").onchange=function(){prefs.fuel=this.value;persist();syncFuel();if(loc)load()}')
edit('web/index.html','function setLoc(x){','function setLoc(x){document.dispatchEvent(new Event("fmn:manual-area"));')
# Continuous movement updates the search, not subscriptions; only latest location is retained.
edit('web/index.html','window.FMNJourneyApp={api:api,',r'''window.FMNJourneyApp={
 getMap:function(){return map},prepareLiveMap:function(){ensureMap()},
 locationState:function(p){var st=launchStateForCoords(p.lat,p.lng);return st==='QLD'&&!qldReady?null:st},
 centreLive:function(p){if(map)map.easeTo({center:[p.lng,p.lat],duration:300})},
 applyLiveLocation:function(p,state,options){
  prefs.state=state;syncFuel();loc={lat:p.lat,lng:p.lng,label:'Current location · '+state,state:state,accuracy:p.accuracy};
  lastSearchCameraKey=[+loc.lat,+loc.lng,+prefs.radius].join('|');
  if(options.follow&&map)map.easeTo({center:[p.lng,p.lat],duration:300});
  if(options.reload){try{persist()}catch(e){}load()}else{render();if(document.body.dataset.page==='options')renderOptions()}
 },api:api,''')
edit('web/index.html','map.addControl(new maplibregl.NavigationControl', 'document.dispatchEvent(new Event("fmn:map-ready"));\n map.addControl(new maplibregl.NavigationControl')
edit('web/index.html','window.FMNNearbyApp={getPrefs:', 'window.FMNNearbyApp={getLocation:function(){return loc},getPrefs:')
edit('web/index.html',' saveVehicle:function(value){Object.assign(prefs,value);persist();setPreset(prefs.vehicle,false);render();moreUI();syncSub();}',r''' saveVehicleQuiet:function(value){Object.assign(prefs,value);prefs.vehicleProfiles=prefs.vehicleProfiles||{};prefs.vehicleProfiles[prefs.vehicle]={tank:prefs.tank,economy:prefs.economy,truck:prefs.truck};try{persist();return true}catch(e){return false}},
 saveVehicle:function(value){return this.saveVehicleQuiet(value)}''')
edit('web/index.html','function closeDrawer(){$("settingsDrawer").classList.remove("open")}', 'function closeDrawer(){if(window.FMNNearbyUI&&$("settingsDrawer").classList.contains("open")&&$("drawer-vehicle").classList.contains("active"))FMNNearbyUI.flushVehicle();$("settingsDrawer").classList.remove("open")}')
edit('web/index.html','"fmnOfferEligibility","fmnJourney"','"fmnOfferEligibility","fmnJourney","fmnVehicleDraft"')
edit('web/index.html','<script src="/nearby-core.js"','<link rel="stylesheet" href="/live-location.css">\n<script src="/live-location.js" defer></script>\n<script src="/nearby-core.js"')
edit('web/journey.js',"function renderDestination(){if(!$('journeySelected'))return;", "function renderDestination(){document.dispatchEvent(new Event('fmn:destination'));if(!$('journeySelected'))return;")
edit('web/journey.js','root.FMNJourney={requestLocation,cancelLocation,onOpen,onClose,chooseNavigation};',r'''function openDestination(){app.openArea();$('journeyMode').value='destination';$('journeyDestination').hidden=false;$('journeyInput').focus();$('journeyDestination').scrollIntoView({block:'nearest'});}
root.FMNJourney={requestLocation,cancelLocation,onOpen,onClose,chooseNavigation,getDestination:()=>destination,openDestination};''')
edit('web/journey.js','This does not filter stations along a route or verify truck access.', 'Use Nearby Filters → Destination direction to narrow the list approximately toward this destination. This is not road-route or truck-access verification.')
edit('web/nearby-core.js',"access:raw.access==='matches'?'matches':'all'", "access:['matches','height','truckstops','unknown'].includes(raw.access)?raw.access:'all',travel:raw.travel==='towards'?'towards':'all'")
p=ROOT/'web/nearby-core.js';s=p.read_text();a=s.index('function select(')
extra=r'''function facilityFor(row,ctx,catalog,now=Date.now()){
 return (catalog?.facilities||[]).find(r=>r&&r.state===ctx.state&&String(r.station_id)===String(row.station_id)&&r.kind==='operator_listed_truck_stop'&&https(r.source_url)&&typeof r.note==='string'&&Number.isFinite(Date.parse(r.checked_at))&&Date.parse(r.checked_at)<=now&&now-Date.parse(r.checked_at)<90*86400000)||null;
}
function heightAccess(row,ctx,catalog,now=Date.now()){
 const height=number(ctx.truck?.height),r=(catalog?.access||[]).find(r=>r&&r.state===ctx.state&&String(r.station_id)===String(row.station_id));
 if(height===null||!r||r.status!=='verified'||!https(r.source_url)||!Number.isFinite(Date.parse(r.verified_at))||Date.parse(r.verified_at)>now||now-Date.parse(r.verified_at)>90*86400000||!Number.isFinite(Date.parse(r.expires_at))||Date.parse(r.expires_at)<=now||number(r.height)===null)return 'unknown';
 return height+.1<=Number(r.height)+1e-9?'height-match':height>Number(r.height)?'mismatch':'limited';
}
'''
s=s[:a]+extra+s[a:];s=s.replace("_review:priceReview(r),_dealSaving:best?.saving||0", "_review:priceReview(r),_dealSaving:best?.saving||0,_facility:facilityFor(r,ctx,catalog,now),_height:heightAccess(r,ctx,catalog,now)")
s=s.replace("(!truckMode(ctx)||f.access!=='matches'||r._access.status==='match')", "(!truckMode(ctx)||f.access==='all'||(f.access==='matches'&&r._access.status==='match')||(f.access==='height'&&r._height==='height-match')||(f.access==='truckstops'&&r._facility)||(f.access==='unknown'&&r._access.status==='unknown'))")
s=s.replace('truckAccess,select','truckAccess,heightAccess,facilityFor,select');p.write_text(s)
func('web/nearby-ui.js','useFilters',"function useFilters(){filters=C.normaliseFilters(filters,context().radius);return filters}")
edit('web/nearby-ui.js','const strict=form.querySelector(\'option[value="matches"]\');strict.disabled=!hasMeasurements();if(strict.disabled)strict.textContent="Recorded-dimension matches — measurements unavailable";', 'const strict=form.querySelector(\'option[value="matches"]\');strict.disabled=false;')
edit('web/nearby-ui.js',"['sort','deals','minKm','maxKm','access']", "['sort','deals','minKm','maxKm','access','travel']")
edit('web/nearby-ui.js', '<option value="matches">Matches recorded dimensions only</option>', '<option value="truckstops">Operator-listed truck stops · clearance unknown</option><option value="height">Recorded height clearance only</option><option value="matches">Matches all recorded dimensions only</option><option value="unknown">Clearance not recorded</option>')
edit('web/nearby-ui.js','<label class="nearby-field nearby-access-field">Truck access', '<label class="nearby-field nearby-destination-field">Destination filter<select name="travel"><option value="all">All directions</option><option value="towards">Toward saved destination · approximate</option></select></label><p class="nearby-direction-help">Uses direction and straight-line progress, not roads. It cannot guarantee no backtracking or a truck-safe approach.</p><label class="nearby-field nearby-access-field">Truck access')
edit('web/nearby-ui.js', "access:form.elements.access.value},context().radius)", "access:form.elements.access.value,travel:form.elements.travel.value},context().radius)")
edit('web/nearby-ui.js',"const saved=write('fmnNearbyFilters',filters);d.close();", "if(filters.travel==='towards'&&(!window.FMNJourney?.getDestination()||window.FMNJourney.getDestination().manual)){d.querySelector('.truck-error').textContent='Choose a destination suggestion with coordinates first. Use the Destination button on Nearby Options.';return;}const saved=write('fmnNearbyFilters',filters);d.close();")
func('web/nearby-ui.js','select',r'''function select(rows,prefs){lastCount=rows.length;const ctx={...prefs},f=useFilters();lastList=C.select(rows,ctx,f,catalog,accepted);if(f.travel==='towards'){const dest=window.FMNJourney?.getDestination(),origin=app.getLocation();lastList=lastList.filter(r=>window.FMNLiveCore?.toward(r,origin,dest)===true);}return lastList}''')
edit('web/nearby-ui.js',"sorted by '+sort+'.'", "sorted by '+sort+(f.travel==='towards'?' · toward destination (approximate)':'')+'.'")
edit('web/nearby-ui.js','host.append(button,clear,text);',r'''const destination=el('button','Destination');destination.type='button';destination.id='nearbyDestination';destination.onclick=()=>window.FMNJourney?.openDestination();host.append(button,destination,clear,text);''')
a=(ROOT/'web/nearby-ui.js').read_text();start=a.index("note.hidden=!C.truckMode");end=a.index('\nif(!lastList.length',start)
a=a[:start]+r'''note.hidden=!C.truckMode(context());note.className='nearby-truck-summary';
const vehicle=context().truck||{};const known=hasMeasurements();
note.textContent='Your truck: '+(vehicle.height||'—')+' m high · '+(vehicle.width||'—')+' m wide · '+(vehicle.length||'—')+' m long · '+(vehicle.weight||'—')+' t. '+(known?'Recorded limits are checked where available.':'No verified numerical clearance measurements are published here yet. Operator-listed truck facilities are separate from a confirmed fit.');
''' + a[end:];(ROOT/'web/nearby-ui.js').write_text(a)
edit('web/nearby-ui.js',"const clear=el('button','Show all nearby stations','btn btn-go');", "const clear=el('button','Show all · clearance unknown','btn btn-go');")
edit('web/nearby-ui.js','actions.prepend(clear);',r'''actions.prepend(clear);if(C.truckMode(context())){const trucks=el('button','Show operator-listed truck stops','btn btn-soft');trucks.type='button';trucks.id='showListedTruckStops';trucks.onclick=()=>{filters={...useFilters(),access:'truckstops'};write('fmnNearbyFilters',filters);app.renderOptions();};actions.append(trucks);}''')
edit('web/nearby-ui.js',"if(C.truckMode(context()))main.appendChild(el('span',x._access.label,'nearby-badge '+x._access.status));", r'''if(C.truckMode(context())){main.appendChild(el('span',x._access.label,'nearby-badge '+x._access.status));if(x._facility){const n=el('span','Operator lists truck facilities · numeric clearance unconfirmed. ','nearby-facility');const a=el('a','Operator details');a.href=x._facility.source_url;a.target='_blank';a.rel='noopener noreferrer';n.append(a);main.append(n);}}''')
edit('web/nearby-ui.js',"function emptyMessage(){const f=useFilters();", "function emptyMessage(){const f=useFilters();if(f.travel==='towards'&&(!window.FMNJourney?.getDestination()||window.FMNJourney.getDestination().manual))return 'Choose a destination suggestion to apply the direction filter.';if(C.truckMode(context())&&f.access==='height')return 'No verified height records match your '+(context().truck?.height||'selected')+' m truck with a 0.1 m allowance. This does not mean there are no truck stops. Check operator-listed facilities or show unknown clearance.';if(C.truckMode(context())&&f.access==='truckstops')return 'No operator-listed truck facilities are in this filtered search yet. Our checked list is incomplete; unknown does not mean absent.';")
old="document.getElementById('truckSaveError').textContent='';}\nfunction saveVehicle()"
new=r'''document.getElementById('truckSaveError').textContent='';const draft=read('fmnVehicleDraft',null);if(draft?.vehicle===p.vehicle){for(const [id,value] of Object.entries(draft.values||{})){const n=document.getElementById(id);if(n)n.value=value;}}installVehicleAutosave();}
function saveVehicle()'''
edit('web/nearby-ui.js',old,new)
s=(ROOT/'web/nearby-ui.js').read_text();start=s.index('function saveVehicle()');end=s.index('\nfunction navigate(',start)
s=s[:start]+r'''function installVehicleAutosave(){
const panel=document.getElementById('drawer-vehicle');if(!document.getElementById('vehicleSaveStatus')){const n=el('p','Valid changes save automatically on this device.','vehicle-save-status');n.id='vehicleSaveStatus';n.role='status';document.getElementById('saveVehicle').after(n);}
if(panel.dataset.autosave)return;panel.dataset.autosave='1';panel.addEventListener('input',e=>{if(e.target.matches('input[type=number],select'))flushVehicle();});panel.addEventListener('change',e=>{if(e.target.matches('input[type=number],select'))flushVehicle();});}
function flushVehicle(){
const p=context(),ids=['tankInput','economyInput','truckHeight','truckWidth','truckLength','truckWeight','truckConfiguration'],values={};
for(const id of ids){const n=document.getElementById(id);if(n)values[id]=n.value;}
const draftSaved=write('fmnVehicleDraft',{vehicle:p.vehicle,values});const tank=document.getElementById('tankInput'),economy=document.getElementById('economyInput'),status=document.getElementById('vehicleSaveStatus');
let error='';if(!tank.value||!economy.value||!tank.checkValidity()||!economy.checkValidity())error='Enter a valid fill size and fuel use.';
const t={configuration:values.truckConfiguration};for(const k of ['height','width','length','weight'])t[k]=values['truck'+k[0].toUpperCase()+k.slice(1)];const validation=C.validateTruck(t);if(C.truckMode(p)&&!validation.ok)error='Complete a valid '+validation.field+' to apply the truck profile.';
if(error){if(status){status.textContent=(draftSaved?'Draft kept. ':'Draft not saved. ')+error;status.dataset.error='true';}return false;}
const saved=app.saveVehicleQuiet({tank:+tank.value,economy:+economy.value,vehicle:p.vehicle,truck:C.truckMode(p)?validation.truck:p.truck});
if(saved){try{localStorage.removeItem('fmnVehicleDraft')}catch{}}
if(status){status.textContent=saved?'Saved on this device.':'Not saved: device storage is unavailable. Keep the app open and retry.';status.dataset.error=String(!saved);}return saved;
}
function saveVehicle(){const ok=flushVehicle();document.getElementById('truckSaveError').textContent=ok?'':'Check the fields and save status below.';if(ok)app.toast('Vehicle saved on this device');return ok;}
''' +s[end:];s=s.replace('radiusChanged,select,afterRender','flushVehicle,radiusChanged,select,afterRender');s=s.replace("toolbar();syncVehicle();loadCatalogue();", "toolbar();syncVehicle();loadCatalogue();document.addEventListener('fmn:destination',reloadList);")
(ROOT/'web/nearby-ui.js').write_text(s)
p=ROOT/'web/sw.js';s=p.read_text().replace("fillmenow-web-v19-journey-20261009","fillmenow-web-v20-live-preferences-20261009");assert 'v20-live' in s;s=s.replace('const SHELL = [','const SHELL = ["/live-location.js", "/live-location.css", ');p.write_text(s)
p=ROOT/'web/privacy.html';s=p.read_text();s=s.replace('</body>','<section><h2>Live location and settings</h2><p>My location and Follow me request GPS only after you tap them and grant permission. Following stops when you switch away from the app. No location trail is stored; the latest search point is used to request nearby fuel data. Panning pauses camera following. Vehicle settings and unfinished field drafts stay in this browser or installed app, not in a shared account. A destination direction filter uses approximate geometry, not a road route or clearance guarantee.</p></section></body>');p.write_text(s)
p=ROOT/'web/data/station-information.json';j=json.loads(p.read_text());j['facilities']=[
{'state':'QLD','station_id':'61402436','kind':'operator_listed_truck_stop','name':'Shell Reddy Express Nudgee','source_url':'https://find.shell.com/au/fuel/10111406-shell-reddy-express-nudgee/en_AU','checked_at':'2026-10-09T01:00:00Z','note':'Shell lists Truck Friendly, high-flow diesel, truck parking and truck AdBlue at 1097 Nudgee Road. No numeric canopy or entrance clearance published.'},
{'state':'QLD','station_id':'61478108','kind':'operator_listed_truck_stop','name':'IOR Eagle Farm','source_url':'https://www.ior.com.au/new-diesel-stop-eagle-farm-brisbane/','checked_at':'2026-10-09T01:00:00Z','source_published_at':'2020-06-08','note':'Operator identifies 1105 Kingsford Smith Drive as a diesel stop accessible to large heavy vehicles. No numeric clearance published. Confirm current access.'},
{'state':'QLD','station_id':'61478247','kind':'operator_listed_truck_stop','name':'IOR Lytton','source_url':'https://www.ior.com.au/ior-lytton-is-now-open/','checked_at':'2026-10-09T01:00:00Z','source_published_at':'2024-09-16','note':'Operator identifies the diesel stop at 6 Radar Street and heavy-transport driveways. Wash-bay dimensions are not fuel-bay clearance. No numeric fuel-bay clearance published.'}]
p.write_text(json.dumps(j,indent=2)+'\n')
print('Patched existing preferences, clearance, destination filters and live map bridge.')
