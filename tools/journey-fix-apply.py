"""Apply focused edits to the existing app. No network, credentials or production data writes."""
from pathlib import Path
import re

def replace(text, old, new):
    if new in text and old not in text:
        return text
    assert text.count(old) == 1, 'Source anchor changed: ' + old[:100]
    return text.replace(old, new, 1)

p = Path('web/index.html')
s = p.read_text()
if 'FMN_JOURNEY_FIX_20261009' not in s:
    s = replace(s, '<link rel="stylesheet" href="/nearby.css">', '<link rel="stylesheet" href="/nearby.css">\n<link rel="stylesheet" href="/journey.css">')
    s = replace(s, '<script src="/nearby-ui.js"></script>', '<script src="/nearby-ui.js"></script>\n<script src="/journey.js"></script>')
    s = replace(s, 'function markerProfile(){return {detailed:!!map&&map.getZoom()>=12,width:60,height:66}}', '''// FMN_JOURNEY_FIX_20261009: show prices at neighbourhood zoom; hysteresis prevents threshold flashing.
var markerPricesVisible=false;
function markerProfile(){if(map){var z=map.getZoom();if(z>=10)markerPricesVisible=true;else if(z<9.5)markerPricesVisible=false}return {detailed:!!map&&markerPricesVisible,width:60,height:66}}''')
    start = s.index('function gps(){')
    end = s.index('async function search(q){', start)
    s = s[:start] + '''function gps(){if(window.FMNJourney)FMNJourney.requestLocation();else{toast("Location controls could not load. Search a suburb instead.");openArea()}}
''' + s[end:]
    s = replace(s, 'document.body.classList.add("modal-open");loadRegions()} function closeArea(){', 'document.body.classList.add("modal-open");loadRegions();if(window.FMNJourney)FMNJourney.onOpen()} function closeArea(){if(window.FMNJourney)FMNJourney.onClose();')
    start = s.index('function navigate(x){')
    end = s.index('\nfunction ', start + 10)
    s = s[:start] + '''function navigate(x){if(!x)return;var next=function(url){var proceed=function(){window.open(url,"_blank","noopener")};if(window.FMNNearbyUI)FMNNearbyUI.navigate(x,proceed);else if(!["truck","heavy"].includes(prefs.vehicle)||confirm("Truck dimensions are not checked by these standard directions. Continue?"))proceed()};if(window.FMNJourney)FMNJourney.chooseNavigation(x,next);else next("https://www.google.com/maps/dir/?api=1&destination="+encodeURIComponent(x.latitude+","+x.longitude))}''' + s[end:]
    s = replace(s, 'window.FMNNearbyApp={', '''window.FMNJourneyApp={api:api,getPrefs:function(){return prefs},getLocation:function(){return loc},openArea:openArea,toast:toast,
 acceptGPS:function(point,selectedState){
  var detected=selectedState&&STATES.indexOf(selectedState)>=0?selectedState:launchStateForCoords(point.lat,point.lng);
  if(!detected)return {ok:false,reason:"border"};
  if(detected==="QLD"&&!qldReady)return {ok:false,reason:"coverage"};
  prefs.state=detected;syncFuel();setLoc({lat:point.lat,lng:point.lng,label:"Current location · "+detected});return {ok:true,state:detected};
 }
};
window.FMNNearbyApp={''')
    s = replace(s, 'if($("areaModal").classList.contains("open"))$("locationSearch").focus();', 'if($("areaModal").classList.contains("open")){$("areaTitle")?.focus({preventScroll:true});}')
    s = replace(s, '"fmnNearbyFilters","fmnOfferEligibility"].forEach', '"fmnNearbyFilters","fmnOfferEligibility","fmnJourney"].forEach')
    p.write_text(s)

p = Path('web/nearby-ui.js')
s = p.read_text()
if 'FMN_TRUCK_DISCOVERABILITY_20261009' not in s:
    s = replace(s, 'function useFilters(){filters=C.normaliseFilters(filters,context().radius);return filters}', '''// FMN_TRUCK_DISCOVERABILITY_20261009: absent measurements are not evidence of absent stations.
function hasMeasurements(){const now=Date.now();return catalogState==='ready'&&catalog.access.some(r=>r&&r.state===context().state&&r.status==='verified'&&Date.parse(r.expires_at)>now&&Date.parse(r.verified_at)<=now&&now-Date.parse(r.verified_at)<=90*86400000&&r.turning_access_verified===true&&Array.isArray(r.configurations)&&['height','width','length','weight'].every(k=>Number(r[k])>0));}
function useFilters(){filters=C.normaliseFilters(filters,context().radius);if(catalogState==='ready'&&!hasMeasurements()&&filters.access==='matches'){filters.access='all';write('fmnNearbyFilters',filters);}return filters}''')
    s = replace(s, 'const form=d.querySelector(\'form\');for(const k', 'const form=d.querySelector(\'form\');const strict=form.querySelector(\'option[value="matches"]\');strict.disabled=!hasMeasurements();if(strict.disabled)strict.textContent="Recorded-dimension matches — measurements unavailable";for(const k')
    s = replace(s, 'lastList=C.select(rows,prefs,useFilters(),catalog,accepted);', 'lastList=C.select(rows,prefs,{...useFilters(),...(!hasMeasurements()?{access:"all"}:{})},catalog,accepted);')
    s = replace(s, 'function afterRender(){toolbar();', '''function afterRender(){toolbar();
let note=document.getElementById('truckAccessNotice');if(!note){note=el('p');note.id='truckAccessNotice';document.getElementById('optionsList').before(note);}note.hidden=!C.truckMode(context())||hasMeasurements();note.textContent=catalogState==='error'?'Truck access records could not load. Nearby stations remain visible; confirm access before travelling.':'Truck stations may be available here even without recorded measurements. Stations remain visible; check entrance, canopy and turning access with the operator.';
if(!lastList.length&&lastCount>0){const wider=document.getElementById('optionsWiden');if(wider)wider.hidden=true;const actions=document.querySelector('#optionsList .empty-actions');if(actions&&!document.getElementById('optionsClearFilters')){const clear=el('button','Show all nearby stations','btn btn-go');clear.id='optionsClearFilters';clear.type='button';clear.onclick=reset;actions.prepend(clear);}}
''')
    p.write_text(s)

p=Path('web/sw.js');s=p.read_text();s=s.replace("fillmenow-web-v18-nearby-20261009", "fillmenow-web-v19-journey-20261009")
if '"/journey.js"' not in s:s=replace(s, 'const SHELL = [', 'const SHELL = ["/journey.js", "/journey.css", ')
p.write_text(s)
p=Path('web/privacy.html');s=p.read_text()
if 'fmnJourney' not in s:
    s=replace(s, '</body>', '<section style="max-width:760px;margin:24px auto;padding:0 20px"><h2>Optional destinations</h2><p>Your optional destination (fmnJourney) is saved on this device and can be cleared in the location panel or by resetting FillMeNow. Destination searches use the existing area lookup service. Your destination and chosen station are passed to Google Maps only when you choose directions via that station. They are not automatically attached to support reports. Location is requested only when you select Use current location; you may refuse permission and search manually.</p></section></body>')
    p.write_text(s)

# The previous browser expectation deliberately selected an empty strict catalogue.
# Replace it with the new regression: that unavailable selector cannot erase real stations.
p=Path('tools/nearby-browser-test.cjs');s=p.read_text()
old="await p.locator('[name=access]').selectOption('matches');await p.getByRole('button',{name:'Apply filters',exact:true}).click();assert.equal(await p.locator('#optionsList .option-row').count(),0);assert.match(await p.locator('#optionsList').innerText(),/No stations have current access records/);"
new="assert.equal(await p.locator('[name=access] option[value=matches]').isDisabled(),true);await p.getByRole('button',{name:'Apply filters',exact:true}).click();assert.equal(await p.locator('#optionsList .option-row').count(),5);assert.match(await p.locator('#truckAccessNotice').innerText(),/Stations remain visible/);"
if old in s:s=replace(s,old,new);p.write_text(s)
print('Applied screenshot fixes to existing web app. No backend, imports or station coordinates changed.')
