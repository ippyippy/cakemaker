"""Small, guarded follow-up from actual desktop screenshots."""
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
    assert s.count(old)==1
    s=s.replace(old,new,1)
    assert re.findall(r'data:image/[^\s"\')]+',s)==images
    p.write_text(s)
    sw=Path('web/sw.js');sw.write_text(re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v7-20261007';",sw.read_text(),count=1))
print('Desktop metadata separation and unavailable-snapshot guard applied; images untouched.')
