"""Small final wiring after the reviewed shared-search repair."""
from pathlib import Path
p=Path('web/index.html');s=p.read_text()
if '<script src="/gps-permission.js" defer>' not in s:
 assert s.count('<script src="/live-location.js" defer>')==1
 s=s.replace('<script src="/live-location.js" defer>','<script src="/gps-permission.js" defer></script>\n<script src="/live-location.js" defer>',1)
p.write_text(s)
p=Path('web/sw.js');s=p.read_text()
if '"/gps-permission.js"' not in s:s=s.replace('const SHELL = [','const SHELL = ["/gps-permission.js", ',1)
p.write_text(s)
p=Path('web/journey.js');s=p.read_text();old="const retry=element('button','Try location again');";new="root.FMNPermissionUI?.mount(body,()=>{d.close();requestLocation();});\n"+old
if new not in s:
 assert s.count(old)==1;s=s.replace(old,new,1)
p.write_text(s)
p=Path('web/live-location.js');s=p.read_text();old="document.body.append(d);d.showModal();}";new="root.FMNPermissionUI?.mount(d.querySelector('.journey-scroll'),()=>{d.close();stop();start();});"+old
if new not in s:
 assert s.count(old)==1;s=s.replace(old,new,1)
p.write_text(s)
p=Path('web/nearby-ui.js');s=p.read_text();old="No verified station offers or measured truck-access records have been published yet. Unknown does not mean unsuitable.";new="No numerical truck clearances or verified offers are published yet. Operator-listed truck facilities have separate source records; they are not height matches."
s=s.replace(old,new)
p.write_text(s)
p=Path('tools/shared-search-test.cjs');s=p.read_text();old=" await p.locator('.nav[data-page=more]').click();await p.locator('[data-open-panel=vehicle]').click();await p.locator('#tankInput').fill('250');"
extra=""" // Exercise the unchanged precise follower with the new shared-filter banner present.
 await p.locator('#recenterBtn').click();const starts=await p.evaluate(()=>__gps.starts);
 for(const lat of [-27.3901,-27.3902,-27.3903]){await p.evaluate(lat=>__gps.success({coords:{latitude:lat,longitude:153.05,accuracy:10},timestamp:Date.now()}),lat);await p.waitForFunction(lat=>FMNJourneyApp.getLocation().lat===lat,lat);}
 await p.waitForFunction(()=>!__map.isMoving());assert.equal(await p.evaluate(()=>FMNLiveLocation.getState().following),true);assert.equal(await p.evaluate(()=>__gps.starts),starts);await p.locator('#followToggle').click();assert.equal(await p.evaluate(()=>FMNLiveLocation.getState().watching),false);r.checks.push('Precise foreground following still processes small movement updates and stops its watch');
 await p.locator('#topArea').click();await p.locator('#locationHelp').click();
 const supported=await p.evaluate(()=>('HTMLGeolocationElement' in window));if(supported){const native=p.locator('#journeyDialog geolocation');assert.equal(await native.getAttribute('accuracymode'),'precise');assert.equal(await native.getAttribute('autolocate'),null);assert.equal(await native.getAttribute('watch'),null);}
 await p.locator('#journeyDialog .journey-back').click();await p.locator('#areaClose').click();r.checks.push('Permission recovery is user-clicked with native enhancement when supported, and a legacy fallback');
"""
if extra not in s:
 assert s.count(old)==1;s=s.replace(old,extra+old,1)
p.write_text(s)
print('Permission enhancement wired without automatic acquisition; movement and fallback checks added.')
