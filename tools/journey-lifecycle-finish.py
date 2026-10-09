"""Finalize lifecycle ordering and visibility in the reviewed journey source."""
from pathlib import Path

def once(s,old,new):
 if old in s:
  assert s.count(old)==1,old[:100]
  return s.replace(old,new,1)
 assert new in s,old[:100]
 return s

p=Path('web/journey.js');s=p.read_text()
changes=[
 ('document.addEventListener(\'DOMContentLoaded\',()=>queueMicrotask(init));','document.addEventListener(\'DOMContentLoaded\',()=>setTimeout(init,0));'),
 ('for(const x of j.candidates){const clean=', 'for(const x of j.candidates){if(x.state&&x.state!==state)continue;const clean='),
 ("$('stateSelect').addEventListener('change',()=>cancelLocation(true));", "$('stateSelect').addEventListener('change',()=>{if(controller)cancelLocation(true);});"),
]
for old,new in changes:s=once(s,old,new)
p.write_text(s)
p=Path('web/journey.css');s=p.read_text()
rule='\nbody #optionsWiden[hidden]{display:none!important}\n'
if rule not in s:s+=rule
p.write_text(s)

# A delayed page-return redraw was overriding the user's zoom with the radius default.
# Keep MapLibre camera state unless the actual search changes or Recenter is pressed.
p=Path('web/index.html');s=p.read_text()
s=once(s,'function renderMap(){\n syncMapStationCount();','var lastSearchCameraKey="";\nfunction renderMap(forceCamera){\n syncMapStationCount();')
s=once(s,' if(!map)return;\n if(!loc)return;\n var r=+prefs.radius||20,w=window.innerWidth||1440;',' if(!map)return;\n if(!loc){lastSearchCameraKey="";return}\n var r=+prefs.radius||20,w=window.innerWidth||1440;')
s=once(s,' map.jumpTo({center:[+loc.lng,+loc.lat],zoom:targetZoom});\n renderMapMarkers();',' var cameraKey=[+loc.lat,+loc.lng,r].join("|");\n if(forceCamera===true||cameraKey!==lastSearchCameraKey){lastSearchCameraKey=cameraKey;map.jumpTo({center:[+loc.lng,+loc.lat],zoom:targetZoom})}\n renderMapMarkers();')
s=once(s,'if($("recenterBtn"))$("recenterBtn").onclick=function(){if(loc)renderMap();else openArea()};','if($("recenterBtn"))$("recenterBtn").onclick=function(){if(loc)renderMap(true);else openArea()};')
p.write_text(s)

# Browser evidence confirmed the option has disabled="", while locator.isDisabled()
# does not report OPTION state in this harness. Assert the native property directly.
for name in ['tools/journey-fix-test.cjs','tools/nearby-browser-test.cjs']:
 p=Path(name);s=p.read_text();s=s.replace("p.locator('[name=access] option[value=matches]').isDisabled()", "p.locator('[name=access] option[value=matches]').evaluate(e=>e.disabled)");p.write_text(s)
p=Path('tools/journey-fix-test.cjs');s=p.read_text()
s=once(s,"await p.screenshot({path:path.join(out,engine+'-'+width+'-map-prices.png')});", "await p.evaluate(()=>FD.options());await p.locator('#optionsBack').click();await p.waitForTimeout(200);assert.equal(await p.evaluate(()=>window.__testMap.getZoom()),11);result.checks.push('returning from options does not reset user zoom');await p.screenshot({path:path.join(out,engine+'-'+width+'-map-prices.png')});")
p.write_text(s)
print('Journey mount order, state confirmation, camera preservation and native disabled option state verified.')
