"""Scoped repair of the existing preference store; no GPS or provider changes."""
from pathlib import Path
import re

path = Path('web/index.html')
s = path.read_text()
if '// FMN_SESSION_PREFS_20261009' in s:
    print('Session preference guard already applied.')
    raise SystemExit(0)
old = 'function persist(){localStorage.setItem("fdPrefs",JSON.stringify(prefs));if(loc)localStorage.setItem("fdLoc",JSON.stringify(loc));else localStorage.removeItem("fdLoc");localStorage.setItem("fdSaved",JSON.stringify(saved))}'
assert s.count(old) == 1
helper = r'''
// FMN_SESSION_PREFS_20261009: same-origin sessions must not restore stale vehicle defaults.
// FMN_PREF_MERGE_BEGIN
function mergeStoredPreferences(base,local,remote){
 function record(v){return !!v&&typeof v==='object'&&!Array.isArray(v)}
 function own(o,k){return Object.prototype.hasOwnProperty.call(o,k)}
 function same(a,b){return JSON.stringify(a)===JSON.stringify(b)}
 function safe(k){return k!=='__proto__'&&k!=='constructor'&&k!=='prototype'}
 base=record(base)?base:{};local=record(local)?local:{};remote=record(remote)?remote:{};
 var result={},keys=new Set(Object.keys(local).concat(Object.keys(remote)));
 keys.forEach(function(k){if(!safe(k))return;var changed=!same(local[k],base[k]);var value=changed||!own(remote,k)?local[k]:remote[k];if(value!==undefined)result[k]=value});
 // Vehicle kind and physical/fill settings are one unit, avoiding mixed car/truck profiles.
 var vehicleKeys=['vehicle','tank','economy','truck'];
 if(vehicleKeys.some(function(k){return !same(local[k],base[k])}))vehicleKeys.forEach(function(k){if(own(local,k))result[k]=local[k];else delete result[k]});
 // Retain other remembered vehicles when this session changes just one profile.
 var profiles={},bp=record(base.vehicleProfiles)?base.vehicleProfiles:{},lp=record(local.vehicleProfiles)?local.vehicleProfiles:{},rp=record(remote.vehicleProfiles)?remote.vehicleProfiles:{};
 new Set(Object.keys(lp).concat(Object.keys(rp))).forEach(function(k){if(!safe(k))return;var value=!same(lp[k],bp[k])||!own(rp,k)?lp[k]:rp[k];if(value!==undefined)profiles[k]=value});
 if(Object.keys(profiles).length)result.vehicleProfiles=profiles;
 return JSON.parse(JSON.stringify(result));
}
// FMN_PREF_MERGE_END
function syncStoredPreferences(){
 if(!window.FMNNearbyApp)return;
 var latest=read('fdPrefs',null);if(!latest||typeof latest!=='object'||Array.isArray(latest))return;
 var next=mergeStoredPreferences(preferenceBaseline,prefs,latest);
 if(JSON.stringify(next)===JSON.stringify(prefs))return;
 var sourceChanged=next.state!==prefs.state||next.fuel!==prefs.fuel||next.radius!==prefs.radius;
 prefs=next;preferenceBaseline=JSON.parse(JSON.stringify(prefs));
 syncFuel();render();
 if(document.body.dataset.page==='options')renderOptions();
 if(document.body.dataset.page==='more')moreUI();
 if(sourceChanged&&loc)load();
}
window.addEventListener('storage',function(e){if(e.key==='fdPrefs')syncStoredPreferences()});
window.addEventListener('focus',syncStoredPreferences);
document.addEventListener('visibilitychange',function(){if(!document.hidden)syncStoredPreferences()});
'''
new = '''function persist(){
 prefs=mergeStoredPreferences(preferenceBaseline,prefs,read("fdPrefs",{}));
 localStorage.setItem("fdPrefs",JSON.stringify(prefs));preferenceBaseline=JSON.parse(JSON.stringify(prefs));
 if(loc)localStorage.setItem("fdLoc",JSON.stringify(loc));else localStorage.removeItem("fdLoc");
 localStorage.setItem("fdSaved",JSON.stringify(saved));
}'''
s = s.replace(old, new + '\n' + helper)
needle = 'var loc=read("fdLoc",null)'
assert s.count(needle) == 1
s = s.replace(needle, 'var preferenceBaseline=JSON.parse(JSON.stringify(prefs));\n' + needle)
# Original artwork must be byte-identical.
pattern = r'data:image/[^\s\"\'\)<>]+'
assert re.findall(pattern, s) == re.findall(pattern, path.read_text())
path.write_text(s)
sw = Path('web/sw.js')
t = sw.read_text()
t, n = re.subn(r"const CACHE = '[^']+';", "const CACHE = 'fillmenow-web-v24-session-preferences-20261009';", t, count=1)
assert n == 1
sw.write_text(t)
print('Applied same-origin stale-session preference guard; GPS, ranking, artwork and provider data unchanged.')
