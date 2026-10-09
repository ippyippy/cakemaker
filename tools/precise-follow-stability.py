"""Keep a pending initial zoom until reached; explicit user zoom takes priority."""
from pathlib import Path
p=Path('web/live-location.js');s=p.read_text()
old='if(streetZoom){options.zoom=Math.max(map.getZoom(),15);streetZoom=false;}'
new='if(streetZoom){options.zoom=Math.max(map.getZoom(),15);if(map.getZoom()>=14.999999)streetZoom=false;}'
if old in s:s=s.replace(old,new,1)
assert new in s
old="map.on('resize',layout);"
new="map.on('zoomstart',e=>{if(e.originalEvent)streetZoom=false;});map.on('resize',layout);"
if new not in s:
 assert s.count(old)==1;s=s.replace(old,new,1)
p.write_text(s)
p=Path('tools/follow-preferences-test.cjs');s=p.read_text()
old="check(await page.evaluate(()=>__map.getZoom()>=15),'street-level live follow zoom');"
new="await page.waitForFunction(()=>!__map.isMoving()&&__map.getZoom()>=14.999999,{},{timeout:8000});check(await page.evaluate(()=>__map.getZoom()>=14.999999),'street-level live follow zoom');"
if new not in s:
 assert s.count(old)==1;s=s.replace(old,new,1)
p.write_text(s)
print('Pending street zoom preserved; explicit user zoom remains in control.')
