"""Scoped, idempotent permission-UI wiring. Never changes coordinates or accuracy rules."""
from pathlib import Path

def patch(path, pairs):
    p=Path(path); s=p.read_text()
    for old,new in pairs:
        if new in s: continue
        assert s.count(old)==1, (path,old[:90],s.count(old))
        s=s.replace(old,new,1)
    p.write_text(s)

patch('web/live-location.js',[
("function start(){if(!app)return;", "function start(){if(!app)return;root.FMNPermissionUI?.attempt('follow');"),
("function fail(code){if(code===1)", "function fail(code){root.FMNPermissionUI?.offer(code===1?'denied':code===3?'timeout':'unavailable','follow');if(code===1)"),
("if(result.kind!=='precise'){if(result.kind==='coarse')", "if(result.kind==='coarse')root.FMNPermissionUI?.offer('coarse','follow',result.accuracy);\n if(result.kind!=='precise'){if(result.kind==='coarse')"),
("lastTimestamp=p.timestamp;lastPoint=p;quality='precise';", "lastTimestamp=p.timestamp;lastPoint=p;quality='precise';root.FMNPermissionUI?.ready();")
])
patch('web/journey.js',[
("async function requestLocation(){if(!app)return;", "async function requestLocation(){if(!app)return;root.FMNPermissionUI?.attempt('search');"),
("onQuality:info=>{if(id===sequence)status(", "onQuality:info=>{if(id===sequence&&info.code==='precision')root.FMNPermissionUI?.offer('coarse','search',info.accuracy);if(id===sequence)status("),
("status('Precise location found (reported ±'", "root.FMNPermissionUI?.ready();status('Precise location found (reported ±'"),
("busy(false);controller=null;\nconst messages={precision:", "busy(false);controller=null;\nroot.FMNPermissionUI?.offer(e?.code===1?'denied':e?.code==='precision'?'coarse':e?.code===3?'timeout':'unavailable','search');\nconst messages={precision:")
])
p=Path('web/journey.css');s=p.read_text()
if 'FMN_LOCATION_PROMPT_20261009' not in s:
 s+='''\n/* FMN_LOCATION_PROMPT_20261009: readable, non-flashing permission prompt; native button owns its action. */
#locationEnableDialog{width:min(480px,calc(100% - 24px));max-height:calc(100dvh - 32px);border:1px solid #c9d5cc;border-radius:22px;background:#fff;color:#102218;padding:0;box-sizing:border-box}
#locationEnableDialog header{padding:20px 20px 12px;border-bottom:1px solid #e1e8e3}
#locationEnableDialog h2{font-size:24px;line-height:1.2;margin:0}
#locationEnableDialog .journey-scroll{padding:16px 20px;min-height:0;overflow-y:auto;overscroll-behavior:contain}
#locationEnableDialog p{font-size:16px;line-height:1.5;margin:0 0 12px}
#locationEnableDialog .location-prompt-safety{font-size:14px;color:#526159}
#locationEnableDialog .gps-permission-recovery{margin:12px 0;padding:0;border:0;background:#fff}
#locationEnableDialog .gps-permission-recovery h3{display:none}
#locationEnableDialog .gps-permission-recovery>p:first-of-type{font-size:14px}
#locationEnableDialog geolocation{font-size:16px;color:#fff;background-color:#087532;border-radius:8px;margin:4px 0;min-height:44px}
#locationEnableDialog details{border:1px solid #d9e3dc;border-radius:12px;padding:12px;margin:12px 0 0}
#locationEnableDialog summary{font-size:16px;font-weight:700;cursor:pointer;line-height:1.4;min-height:32px}
#locationEnableDialog details p{font-size:14px;margin:12px 0 0}
#locationEnableDialog footer{display:flex;align-items:stretch;justify-content:space-between;gap:10px;flex-shrink:0;padding:12px 16px max(12px,env(safe-area-inset-bottom));border-top:1px solid #dce5df;background:white}
#locationEnableDialog footer button{min-height:48px;border:1px solid #bbc9c0;border-radius:12px;font-size:16px;line-height:1.25;font-weight:700;padding:12px 14px;white-space:normal;background:white;color:#183d28}
#locationEnableDialog #locationPromptEnable{background:#087532;color:white;border-color:#087532;max-width:66%}
#locationEnableDialog #locationPromptLater{margin-right:auto}
#locationEnableDialog::backdrop{background:#0b1d1866}
#locationEnableDialog :focus-visible{outline:3px solid #b98500;outline-offset:3px}
@media(max-height:500px){#locationEnableDialog{max-height:calc(100dvh - 12px)}#locationEnableDialog header{padding:10px 16px}#locationEnableDialog .journey-scroll{padding:10px 16px}}
'''
 p.write_text(s)
p=Path('web/sw.js');s=p.read_text();lines=s.splitlines();lines[0]="const CACHE = 'fillmenow-web-v25-location-prompt-20261009';";p.write_text('\n'.join(lines)+'\n')
print('Location prompt connected to existing GPS; numerical accuracy, preferences, prices and station data unchanged.')
