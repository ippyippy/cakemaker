"""Small, guarded follow-up from actual screenshots and control inspection."""
from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text()
images=re.findall(r'data:image/[^\s"\')]+',s)
if 'FMN_DESKTOP_META_SPACING_20261007' not in s:
    start=s.index('<style id="fillmenow-public-readiness-2026-10-07">');end=s.index('</style>',start)
    css='''
/* FMN_DESKTOP_META_SPACING_20261007 */
body #page-options .option-main{display:flex!important;flex-direction:column!important;align-items:flex-start!important;min-width:0!important}
body #page-options .option-main .option-id{margin:6px 0 0!important}
body #page-options .option-main strong{display:block!important;margin:7px 0 0!important}
body #page-options #optionsVehicle{display:flex!important;flex-direction:column!important;justify-content:center!important;align-items:flex-start!important;gap:4px!important;padding:8px 12px!important}
body #page-options #optionsVehicle>span{display:block!important;font-size:12px!important;line-height:1.2!important;color:#526057!important}
body #page-options #optionsVehicle>b{display:block!important;font-size:16px!important;line-height:1.2!important;color:#15241b!important;margin:0!important}
'''
    s=s[:end]+css+s[end:]
    old='if(!j||j.ok!==true||j.error||j.connected===false||!Array.isArray(j.rows))throw Error("bad prices response");'
    new='''if(!j||j.ok!==true||j.error||j.connected===false||!Array.isArray(j.rows))throw Error("bad prices response");
  // A missing state-wide snapshot is unavailable data, not zero nearby stations.
  // This also catches the legacy server's masked database-read failure response.
  if(j.rows.length===0&&!j.price_date)throw Error("fuel snapshot unavailable");'''
    assert s.count(old)==1;s=s.replace(old,new,1)
if 'FMN_MAP_COUNT_INTERACTION_20261007' not in s:
    helper='''function syncMapStationCount(){
 var e=$("mapStationCount");if(!e)return;
 e.textContent=!loc?"Choose area":ranked.length+" station"+(ranked.length===1?"":"s")+" · View all";
 e.setAttribute("role","button");e.tabIndex=0;
 e.setAttribute("aria-label",!loc?"Choose a search area":"View all "+ranked.length+" nearby stations");
 e.onclick=function(){if(loc)showPage("options");else openArea()};
 e.onkeydown=function(event){if(event.key==="Enter"||event.key===" "){event.preventDefault();e.click()}};
}
'''
    assert 'function renderMapMarkers(){\n if(!map||!loc||!window.maplibregl)return;' in s
    s=s.replace('function renderMapMarkers(){\n if(!map||!loc||!window.maplibregl)return;',helper+'function renderMapMarkers(){\n syncMapStationCount();\n if(!map||!loc||!window.maplibregl)return;',1)
    start=s.index(' var groups=clusterStations(ranked,0),countEl=$("mapStationCount");');end=s.index(' groups.forEach(function(g){',start)
    s=s[:start]+' var groups=clusterStations(ranked,0);\n'+s[end:]
    old='function renderMap(){\n ensureMap();';assert old in s;s=s.replace(old,'function renderMap(){\n syncMapStationCount();\n ensureMap();',1)
    old='if(!map){var count=$("mapStationCount");if(count)count.textContent=ranked.length+" station"+(ranked.length===1?"":"s")+" in "+prefs.radius+" km";return}'
    assert old in s;s=s.replace(old,'if(!map)return;',1)
    start=s.index('<style id="fillmenow-public-readiness-2026-10-07">');end=s.index('</style>',start)
    s=s[:end]+'\n/* FMN_MAP_COUNT_INTERACTION_20261007 */\nbody .map-station-count{pointer-events:auto!important;touch-action:manipulation}\n'+s[end:]
if 'FMN_DETACHED_LOGO_GUARD_20261007' not in s:
    # A delayed image error may run after a marker/card was removed or replaced.
    # Disable the handler first and retain the host before replacing its children.
    old='onerror="this.parentElement.classList.add('
    new='onerror="this.onerror=null;var host=this.parentElement;if(!host)return;host.classList.add('
    assert s.count(old)==1;s=s.replace(old,new,1)
    old='this.parentElement.innerHTML=';assert s.count(old)==1;s=s.replace(old,'host.innerHTML=',1)
    s=s.replace('function brandMark(brand,name){','function brandMark(brand,name){\n // FMN_DETACHED_LOGO_GUARD_20261007',1)
assert re.findall(r'data:image/[^\s"\')]+',s)==images
p.write_text(s)
sw=Path('web/sw.js');sw.write_text(re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v9-20261007';",sw.read_text(),count=1))
print('Desktop spacing, unavailable-snapshot guard, map counter and detached-logo fallback applied; images untouched.')
