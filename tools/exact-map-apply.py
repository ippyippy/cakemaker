"""Guarded in-place repair; preserve all artwork, credentials and native source."""
from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text();before=s
if 'FMN_EXACT_PINS_APPLIED_20261008' not in s:
 a=s.index('function markerProfile(){');b=s.index('function renderMap(){',a)
 s=s[:a]+'// FMN_EXACT_PINS_APPLIED_20261008\n'+Path('tools/exact-map-functions.js').read_text()+'\n'+s[b:]
 s=s.replace('function bind(){','function bind(){installPopupFooters();',1)
 s=s.replace('if(map&&loc){map.resize();renderMap();}','if(map&&loc){map.resize();renderMapMarkers();}',1)
 for start,end in [('function bestHtml(','function altRows('),('function render(){','async function load('),('function renderDrive(){','function installState(')]:
  a=s.index(start);b=s.index(end,a);s=s[:a]+s[a:b].replace('esc(prefs.fuel)','esc(b.fuel_type||prefs.fuel)')+s[b:]
 s=s.replace('if(sid)m.push(["Station ID",sid,"id-mini"]);','m.push(["Fuel",x.fuel_type||prefs.fuel,""]);if(sid)m.push(["Station ID",sid,"id-mini"]);',1)
 a=s.index('function renderOptions(');b=s.index('function openDrawer(',a)
 section=s[a:b];section=section.replace("'<strong>'+x.price.toFixed(1)","'<span class=\"option-fuel\">'+esc(x.fuel_type||prefs.fuel)+'</span><strong>'+x.price.toFixed(1)")
 # The visible grade must be present in options even when the ID fragment is concatenated differently.
 if 'class="option-fuel"' not in section:
  section=section.replace("+'<strong>'+x.price.toFixed(1)","+'<span class=\"option-fuel\">'+esc(x.fuel_type||prefs.fuel)+'</span><strong>'+x.price.toFixed(1)")
 assert 'class="option-fuel"' in section,'Missing option grade anchor'
 s=s[:a]+section+s[b:]
 s=s.replace('Launch coverage is NSW, WA and Tasmania.','Launch coverage is NSW, WA and Tasmania. Diesel comparisons include standard and premium diesel; each result shows its grade.',1)
 s=s.replace('</head>','<link rel="stylesheet" href="/interaction-polish.css">\n</head>',1)
 assert re.findall(r'data:image/[^\s\"\)]+',s)==re.findall(r'data:image/[^\s\"\)]+',before),'Mascot bytes changed'
 p.write_text(s)
 w=Path('web/sw.js').read_text();w=re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v15-exact-pins-20261008';",w,count=1);w=w.replace('const SHELL = [','const SHELL = ["/interaction-polish.css", ',1);Path('web/sw.js').write_text(w)
# Diesel is an inclusive comparison category; keep the source fuel grade on every row.
p=Path('backend/fueldrop/index.ts');s=p.read_text()
if 'FMN_DIESEL_COVERAGE_20261008' not in s:
 a=s.index('async function latestFuelRows(');b=s.index('function publicPricePayload(',a);part=s[a:b]
 anchor='const stateFilter="&state_code=eq."+encodeURIComponent(st);'
 assert part.count(anchor)==1
 part=part.replace(anchor,anchor+'\n const fuelFilter=String(fuel||"Diesel")==="Diesel"?"fuel_type=in.(Diesel,Premium%20Diesel)":"fuel_type=eq."+f;',1)
 assert part.count('fuel_type=eq.")+f')==0
 part=part.replace('fuel_type=eq."+f+stateFilter','"+fuelFilter+stateFilter')
 old='return {connected:true,rows,price_date:date,snapshot_synced_at:snapshotSyncedAt,state_code:st,provider,source:provider?.provider_name||"FillMeNow government data cache"};'
 assert part.count(old)==1
 part=part.replace(old,'return {connected:true,rows:selectComparableFuelRows(rows),price_date:date,snapshot_synced_at:snapshotSyncedAt,state_code:st,provider,source:provider?.provider_name||"FillMeNow government data cache"};')
 helper='''// FMN_DIESEL_COVERAGE_20261008
function selectComparableFuelRows(rows:any[]){
 const stations=new Map<string,any>();
 for(const row of rows){
  const id=String(row.station_id),prior=stations.get(id);
  if(!prior||Number(row.price)<Number(prior.price)||(Number(row.price)===Number(prior.price)&&row.fuel_type==="Diesel"&&prior.fuel_type!=="Diesel"))stations.set(id,row);
 }
 return [...stations.values()].sort((a,b)=>Number(a.price)-Number(b.price)||String(a.station_id).localeCompare(String(b.station_id)));
}
'''
 s=s[:a]+helper+part+s[b:];p.write_text(s)
print('Applied exact pins, matching rounded Dash, popup footers and inclusive diesel reads.')
