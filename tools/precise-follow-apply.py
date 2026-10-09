"""Scoped migration for the existing foreground follower; no backend or native changes."""
from pathlib import Path

def replace(path, old, new):
 p=Path(path);s=p.read_text()
 if new in s:return
 assert s.count(old)==1,(path,old[:120],s.count(old))
 p.write_text(s.replace(old,new,1))
replace('web/sw.js','fillmenow-web-v20-live-preferences-20261009','fillmenow-web-v21-precise-follow-20261009')
p=Path('web/live-location.css');s=p.read_text();css='''
/* FMN_PRECISE_FOLLOW_20261009: coarse fixes never receive the live green state. */
body #page-explore #preciseGpsHelp{min-width:78px!important;max-width:118px!important;min-height:42px!important;height:auto!important;padding:7px 9px!important;border-radius:12px!important;font-size:13px!important;line-height:18px!important;background:#fff!important;color:#173a27!important}
body #page-explore #preciseGpsHelp[hidden]{display:none!important}
body #followStatus[data-quality=coarse],body #followStatus[data-quality=stale],body #followStatus[data-quality=denied]{border:1px solid #a76517;background:#fff8e9;color:#67400f}
body .user-map-marker.gps-last-known{filter:grayscale(1);opacity:.55}
#preciseGpsDialog footer button{min-height:44px;font-size:15px}
#preciseGpsDialog .journey-scroll{font-size:16px;line-height:1.5}
'''
if 'FMN_PRECISE_FOLLOW_20261009' not in s:p.write_text(s+css)
# Keep the existing end-to-end regressions, but test the visible GPS anchor rather than
# the geographic camera centre: the Best Stop sheet must not hide the current position.
p=Path('tools/follow-preferences-test.cjs');s=p.read_text()
if 'waitForVisibleFix' not in s:
 anchor='async function run(engine,width,height)'
 helper='''async function waitForVisibleFix(page,lat,lng){await page.waitForFunction(({lat,lng})=>{if(!window.__map||__map.isMoving())return false;const m=__map.getContainer().getBoundingClientRect(),p=__map.project([lng,lat]),sheet=document.getElementById('mobileSheet');let bottom=m.bottom;const r=sheet.getBoundingClientRect();if(!sheet.classList.contains('collapsed')&&r.height>50&&r.top>m.top&&r.top<bottom)bottom=r.top;return p.x>18&&p.x<m.width-18&&m.top+p.y>m.top+20&&m.top+p.y<bottom-12;},{lat,lng},{timeout:8000});}
'''
 assert anchor in s;s=s.replace(anchor,helper+anchor,1)
 s=s.replace('watchPosition(success,error){window.__gps.success=success;', 'watchPosition(success,error,options){window.__gps.options=options;window.__gps.success=success;',1)
 old="await page.waitForTimeout(450);assert.equal(await page.evaluate(()=>FMNJourneyApp.getLocation().lat),-27.45);check(Math.abs(await page.evaluate(()=>__map.getCenter().lat)+27.45)<.0001,'GPS centred');"
 new="await waitForVisibleFix(page,-27.45,153.03);assert.equal(await page.evaluate(()=>FMNJourneyApp.getLocation().lat),-27.45);check(await page.evaluate(()=>__map.getZoom()>=15),'street-level live follow zoom');await page.evaluate(()=>FD.sheet());await waitForVisibleFix(page,-27.45,153.03);"
 assert old in s;s=s.replace(old,new,1)
 old="await page.waitForTimeout(450);check(Math.abs(await page.evaluate(()=>__map.getCenter().lat)+27.44)<.0001,'camera follows next coordinate');"
 new="await waitForVisibleFix(page,-27.44,153.031);check((await page.evaluate(()=>FMNJourneyApp.getLocation().lat))===-27.44,'next precise position accepted and remains visible above sheet');"
 assert old in s;s=s.replace(old,new,1)
 old="await page.waitForTimeout(450);assert.equal(await page.evaluate(()=>__gps.starts),1);check(Math.abs(await page.evaluate(()=>__map.getCenter().lat)+27.43)<.0001,'resume recentre does not duplicate watch');"
 new="await waitForVisibleFix(page,-27.43,153.032);assert.equal(await page.evaluate(()=>__gps.starts),1);check(await page.evaluate(()=>FMNLiveLocation.getState().following),'resume follows without duplicate watcher');"
 assert old in s;s=s.replace(old,new,1)
 # Reproduce the 2km screenshot: never promote it to a live point or cancel a warming GPS.
 old="assert.equal(await page.evaluate(()=>__gps.starts),1);await page.evaluate(()=>__gps.success({coords:{latitude:-27.45"
 extra="""assert.equal(await page.evaluate(()=>__gps.starts),1);
 const originBefore=await page.evaluate(()=>FMNJourneyApp.getLocation().lat);const cameraBefore=await page.evaluate(()=>__map.getCenter().lat);
 await page.evaluate(()=>__gps.success({coords:{latitude:-27.3,longitude:153.2,accuracy:2000},timestamp:Date.now()}));
 assert.equal(await page.evaluate(()=>FMNJourneyApp.getLocation().lat),originBefore);assert.equal(await page.evaluate(()=>__map.getCenter().lat),cameraBefore);assert.equal(await page.evaluate(()=>FMNLiveLocation.getState().following),false);assert.match(await page.locator('#followStatus').innerText(),/2000/);assert.equal(await page.locator('#followToggle').getAttribute('aria-pressed'),'false');
 const opts=await page.evaluate(()=>__gps.options);assert.equal(opts.enableHighAccuracy,true);assert.equal(opts.maximumAge,0);assert.ok(opts.timeout>=20000);
 await page.evaluate(()=>__gps.error({code:3}));assert.deepEqual(await page.evaluate(()=>__gps.clears),[]);assert.equal(await page.evaluate(()=>FMNLiveLocation.getState().watching),true);
 await page.locator('#preciseGpsHelp').click();assert.match(await page.locator('#preciseGpsDialog').innerText(),/Use precise location/);const footer=await page.locator('#preciseGpsBack').boundingBox();assert.ok(footer.x<width/2);await page.locator('#preciseGpsBack').click();
 r.checks.push('2km coarse fix is rejected; fresh high-accuracy GPS requested; acquisition survives timeouts; precise help has bottom-left Back');
 await page.evaluate(()=>__gps.success({coords:{latitude:-27.45"""
 assert old in s;s=s.replace(old,extra,1)
 old="await page.evaluate(()=>{__map.fire('dragstart'"
 extra="""// Driving movement is accepted on every good callback, not after kilometre-sized moves.
 for(let i=1;i<=6;i++){const lat=-27.44+i*.0001;await page.evaluate(lat=>__gps.success({coords:{latitude:lat,longitude:153.031,accuracy:12},timestamp:Date.now()}),lat);await waitForVisibleFix(page,lat,153.031);assert.equal(await page.evaluate(()=>FMNJourneyApp.getLocation().lat),lat);}
 const lastGood=await page.evaluate(()=>FMNJourneyApp.getLocation().lat);await page.evaluate(()=>__gps.success({coords:{latitude:-27.2,longitude:153.3,accuracy:1000},timestamp:Date.now()}));assert.equal(await page.evaluate(()=>FMNJourneyApp.getLocation().lat),lastGood);assert.equal(await page.evaluate(()=>FMNLiveLocation.getState().following),false);
 await page.evaluate(lat=>__gps.success({coords:{latitude:lat,longitude:153.031,accuracy:10},timestamp:Date.now()}),lastGood);await waitForVisibleFix(page,lastGood,153.031);assert.equal(await page.evaluate(()=>__gps.starts),1);
 if(engine==='chromium'&&width===390){await page.waitForFunction(()=>FMNLiveLocation.getState().quality==='stale',{},{timeout:15000});assert.equal(await page.evaluate(()=>FMNLiveLocation.getState().following),false);await page.evaluate(lat=>__gps.success({coords:{latitude:lat,longitude:153.031,accuracy:10},timestamp:Date.now()}),lastGood);await waitForVisibleFix(page,lastGood,153.031);assert.equal(await page.evaluate(()=>FMNLiveLocation.getState().following),true);}
 r.checks.push('Six approximately 11m movement updates remain visible above expanded Best Stop; 1km degradation is rejected; precise recovery reuses watch; stale signal is labelled');
 await page.evaluate(()=>{__map.fire('dragstart'"""
 assert old in s;s=s.replace(old,extra,1)
 p.write_text(s)
print('Precise follower styling, service-worker update and stronger existing regressions applied.')
