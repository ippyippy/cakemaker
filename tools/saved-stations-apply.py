"""Apply the requested public-ID cleanup and local saved-station controls.
Only changes source files in this working copy. No API calls or data migration.
"""
from pathlib import Path
import re
p=Path('web/index.html')
s=p.read_text()
if 'FMN_SAVED_CONTROLS_20261008' not in s:
    original=s
    # Internal provider IDs remain untouched for pricing, markers and navigation.
    old='if(sid)m.push(["Station ID",sid,"id-mini"]);'
    assert s.count(old)==1
    s=s.replace(old,'',1)
    old='+(sid?\'<span class="option-id">ID \'+esc(sid)+\'</span>\':"")'
    assert s.count(old)==1
    s=s.replace(old,'',1)
    marker='function renderSaved(){'
    assert s.count(marker)==1
    s=s.replace(marker,'''// FMN_SAVED_CONTROLS_20261008
function removeSavedStation(id){
 var index=saved.findIndex(function(x){return String(x.station_id)===String(id)});
 if(index<0)return;
 saved.splice(index,1);persist();renderSaved();
 if(current&&String(current.station_id)===String(id)){
  if($("stationSave"))$("stationSave").textContent="Save";
  if($("desktopStationSave"))$("desktopStationSave").textContent="Save";
 }
 toast("Station removed from Saved");
 var next=$("savedList").querySelector(".saved-remove")||$("addStationBtn");
 if(next)next.focus({preventScroll:true});
}
function renderSaved(){''',1)
    a=s.index(' $("savedList").innerHTML=\'<div class="saved-list">\'')
    b=s.index('\n}',a)
    s=s[:a]+''' $("savedList").innerHTML='<div class="saved-list">'+saved.map(function(x){
  var live=find(x.station_id)||x,p=Number(live.price);
  return '<article class="saved-card"><div class="saved-station-info">'+brandMark(live.brand,live.station_name)+'<div><b>'+esc(live.station_name)+'</b><span>'+esc(live.suburb||"")+(Number.isFinite(p)&&p>0?" · "+p.toFixed(1)+"¢/L":"")+'</span></div></div><div class="saved-actions"><button type="button" class="btn btn-soft saved-navigate" data-saved-id="'+esc(x.station_id)+'">Navigate</button><button type="button" class="btn btn-outline saved-remove" data-saved-id="'+esc(x.station_id)+'" aria-label="Remove '+esc(live.station_name)+' from Saved">Remove</button></div></article>';
 }).join("")+'</div>';
 Array.from($("savedList").querySelectorAll(".saved-remove")).forEach(function(button){button.onclick=function(){removeSavedStation(button.dataset.savedId)}});
 Array.from($("savedList").querySelectorAll(".saved-navigate")).forEach(function(button){button.onclick=function(){navigate(saved.find(function(x){return String(x.station_id)===String(button.dataset.savedId)}))}});
''' +s[b:]
    assert sorted(re.findall(r'data:image/[^\s\"\)]+',s))==sorted(re.findall(r'data:image/[^\s\"\)]+',original))
    p.write_text(s)
p=Path('web/startup-support.css')
s=p.read_text()
if 'FMN_SAVED_CONTROLS_20261008' not in s:
    s+='''
/* FMN_SAVED_CONTROLS_20261008: explicit local removal, separate from navigation. */
body #savedList .saved-card{display:flex;flex-direction:column;align-items:stretch;gap:14px;padding:16px;min-width:0}
body #savedList .saved-station-info{display:flex;align-items:center;gap:12px;min-width:0}
body #savedList .saved-station-info>div{min-width:0;flex:1}
body #savedList .saved-station-info b{display:block;font-size:17px;line-height:1.35;overflow-wrap:anywhere}
body #savedList .saved-station-info span{display:block;font-size:14px;line-height:1.45;margin-top:4px}
body #savedList .saved-actions{display:flex;flex-wrap:wrap;gap:10px}
body #savedList .saved-actions button{flex:1;min-width:100px;min-height:46px;font-size:15px;line-height:1.3;margin:0}
body #savedList .saved-remove{background:#fff;color:#304638;border:1px solid #a9bcae}
@media (min-width:1025px){body #savedList .saved-card{flex-direction:row;align-items:center}body #savedList .saved-station-info{flex:1}body #savedList .saved-actions{flex:0 0 auto}}
/* Short landscape phone screens keep the back control at the screen edge too. */
@media(max-width:900px) and (max-height:500px){.fmn-help{top:var(--help-top,0);bottom:auto;height:var(--help-height,100dvh);align-items:stretch}.fmn-help .help-shell{width:100%;height:100%;border-radius:0;border:0}.fmn-help .help-header{padding:10px 14px}.fmn-help .help-header h2{font-size:20px}.fmn-help .help-header p{margin-top:2px}.fmn-help .help-composer{padding:8px 14px}.fmn-help .help-footer{padding-top:6px;padding-bottom:max(6px,env(safe-area-inset-bottom))}}
'''
    p.write_text(s)
print('Prepared public station-ID removal, explicit saved-station deletion and landscape help layout.')
