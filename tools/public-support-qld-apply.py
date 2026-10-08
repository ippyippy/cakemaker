"""Prepare the existing application for the reviewed support and Queensland release.
Run from the repository root. This changes local source only: it does not publish,
read credentials, invoke production APIs, run cron jobs, or change database data.
"""
from pathlib import Path
import re

p = Path('web/index.html')
s = p.read_text()
original = s
if 'FMN_STARTUP_SUPPORT_20261008' not in s:
    def rep(old, new):
        global s
        assert s.count(old) == 1, ('missing/ambiguous source anchor', old[:100])
        s = s.replace(old, new, 1)

    head = '''<script id="fmn-entry-state">/* FMN_STARTUP_SUPPORT_20261008 */
(function(){var first=true;try{first=localStorage.getItem("fmnOnboarded")!=="1"}catch(e){}if(new URL(location.href).searchParams.get("help")==="1")first=false;document.documentElement.dataset.firstRun=String(first)})();
</script>'''
    rep('<meta charset="utf-8">', '<meta charset="utf-8">\n' + head)
    rep('</head>', '<link rel="stylesheet" href="/startup-support.css">\n<script defer src="/support-chat.js"></script>\n</head>')
    body = re.search(r'<body[^>]*>', s).group(0)
    if 'data-page=' not in body:
        rep(body, body[:-1] + ' data-page="explore">')
    a = s.index('<div class="fmn-onboard"')
    b = s.index('<div class="toast"', a)
    onboarding = s[a:b]
    s = s[:a] + s[b:]
    b = s.index('>', s.index('<body')) + 1
    s = s[:b] + '\n' + onboarding + s[b:]
    rep('var STATES=["NSW","WA","TAS"],FUELS={', 'var STATES=["NSW","WA","TAS","QLD"],FUELS={QLD:["Diesel","U91","E10","U95","U98"],')
    # Preserve the existing accessible name rather than assuming an attribute-free select.
    tag = re.search(r'<select\b[^>]*\bid="stateSelect"[^>]*>', s).group(0)
    rep(tag, tag + '<option value="QLD" disabled>Queensland — connecting</option>')
    s = s.replace('Choose NSW, WA or Tasmania, then use your location or search a suburb/postcode.', 'Choose an available state, then use your location or search a suburb/postcode.')
    rep('center:[151.2,-33.8],', 'center:loc?[+loc.lng,+loc.lat]:[151.2,-33.8],')
    rep('function showInfo(kind){', 'function showInfo(kind){if(kind==="help"&&window.FMNHelp){window.FMNHelp.open();return;}')
    s = s.replace('<b>Help & FAQ</b><small>How FillMeNow works</small>', '<b>Ask Dash / Report a problem</b><small>App help, glitches and suggestions</small>')
    rep('function launchStateForCoords(lat,lng){', '''var qldReady=false,coverageRequest=null;
async function refreshCoverage(){
 if(coverageRequest)return coverageRequest;
 coverageRequest=(async function(){try{var r=await fetch(api({api:"status"}),{cache:"no-store",signal:AbortSignal.timeout(10000)}),j=await r.json();qldReady=r.ok&&j.ok===true&&Array.isArray(j.launchStates)&&j.launchStates.indexOf("QLD")>=0;}catch(e){qldReady=false}
 var select=$("stateSelect"),option=select?select.querySelector('option[value="QLD"]'):null;if(option){option.disabled=!qldReady;option.textContent=qldReady?"Queensland":"Queensland — connecting";}window.FMNCoverage={qldReady:qldReady};return qldReady;})();
 try{return await coverageRequest}finally{coverageRequest=null}
}
function launchStateForCoords(lat,lng){
 if(lat>=-28.10&&lat<=-9.0&&lng>=138&&lng<=154)return "QLD";
 if(lat>=-29&&lat< -28.10&&lng>=138&&lng<=151.35)return "QLD";
 if(lat>=-29&&lat< -28.10&&lng>151.35&&lng<=154)return null;
''')
    s = s.replace('Current location is outside NSW, WA and Tasmania', 'Choose your state manually for this location')
    rep('prefs.state=detected;syncFuel();persist();setLoc(', 'if(detected==="QLD"&&!qldReady){toast("Queensland is connecting. Please choose an available state.");openArea();return}prefs.state=detected;syncFuel();persist();setLoc(')
    rep('function openArea(){', 'function openArea(){refreshCoverage();')
    rep('if(loc)load();else{render();openArea()}}', '''refreshCoverage();if(document.documentElement.dataset.firstRun!=="true"){if(loc)load();else{render();if(new URL(location.href).searchParams.get("help")!=="1")openArea()}}}''')
    rep('localStorage.setItem("fmnOnboarded","1");o.classList.remove("open");blocked.forEach(function(el){el.inert=false});', '''try{localStorage.setItem("fmnOnboarded","1")}catch(e){}document.documentElement.dataset.firstRun="false";o.classList.remove("open");blocked.forEach(function(el){el.inert=false});if(loc)load();else{render();openArea();}''')
    rep('if(localStorage.getItem("fmnOnboarded")!=="1"){o.classList.add("open")', 'if(document.documentElement.dataset.firstRun==="true"){o.classList.add("open")')
    s = s.replace('Launch coverage is NSW, WA and Tasmania.', 'Available coverage is shown in the state selector, including Queensland when its production feed is connected.')
    s = s.replace('NSW and Tasmania: NSW Government FuelCheck.', 'Queensland: Fuel Prices QLD when connected. NSW and Tasmania: NSW Government FuelCheck.')
    rep('["fdPrefs","fdLoc","fdSaved","fmnOnboarded","fmnDashPosition"].forEach', '["fdPrefs","fdLoc","fdSaved","fmnOnboarded","fmnDashPosition","fmnSupportDevice","fmnSupportReceipt"].forEach')
    assert sorted(re.findall(r'data:image/[^\s\"\)]+', s)) == sorted(re.findall(r'data:image/[^\s\"\)]+', original)), 'Original artwork must be preserved'
    p.write_text(s)
    for name in ['web/privacy.html', 'web/terms.html']:
        q = Path(name)
        t = q.read_text()
        t = re.sub(r'<a href="mailto:[^"]+">[^<]+</a>', '<a href="/?help=1">Ask Dash / send a private support report</a>', t)
        t = t.replace('Effective: 5 October 2026', 'Effective: 8 October 2026')
        if name.endswith('privacy.html'):
            extra = '''<h2>Help chat and support reports</h2><p>Ask Dash uses built-in app guidance. Questions typed into this helper are kept only in the current page and are not sent to a chatbot provider. When you explicitly submit a report, the report text, selected category, app version, browser family, screen size and current app screen are stored privately for investigation. A random device token is stored locally; only its hash is stored with the report. Do not include names, email addresses, passwords or exact addresses. Reports do not attach GPS coordinates or saved stations.</p><p>Reports are retained for up to 90 days. You can delete your last report from the same device using the support panel. Weekly investigation tasks may be added to the repository after removing personal information; private report text is not automatically published. Resetting local app data does not itself delete server reports and removes this device’s report-deletion token.</p>'''
            t = t.replace('<h2>Contact</h2>', extra + '\n<h2>Contact</h2>')
            t = t.replace('and FuelWatch, Government of Western Australia, for Western Australia.', 'FuelWatch, Government of Western Australia, for Western Australia, and the approved Fuel Prices QLD feed when connected.')
        q.write_text(t)
    q = Path('android/PLAY_STORE_LISTING.md')
    t = q.read_text()
    t = re.sub(r'^Support / privacy email:.*$', 'Support / privacy: https://fillmenow.vercel.app/?help=1\nStore-console contact details require a separate FillMeNow support contact before native submission.', t, flags=re.M)
    q.write_text(t)
    sw = Path('web/sw.js')
    w = re.sub(r"const CACHE = '[^']+';", "const CACHE = 'fillmenow-web-v17-support-qld-20261008';", sw.read_text(), count=1)
    w = w.replace('const SHELL = [', 'const SHELL = ["/startup-support.css", "/support-chat.js", ', 1)
    sw.write_text(w)

p = Path('backend/fueldrop/index.ts')
s = p.read_text()
if 'FMN_QLD_SUPPORT_20261008' not in s:
    s = '// FMN_QLD_SUPPORT_20261008\nimport { supportAPI } from "./support.ts";\n' + s
    s = s.replace('["NSW","WA","TAS"]', '["NSW","WA","TAS","QLD"]')
    i = s.index('async function latestFuelRows(')
    s = s[:i] + '''async function qldCoverageReady(){
 if(!(Deno.env.get("QLD_FUEL_API_TOKEN")||"").trim())return false;
 try{const base=Deno.env.get("SUPABASE_URL")||"";const r=await fetch(base+"/rest/v1/fuel_price_daily?select=synced_at&state_code=eq.QLD&provider_code=eq.qld-fpqld&order=synced_at.desc&limit=1",{headers:adminHeaders(),signal:AbortSignal.timeout(8000)});if(!r.ok)return false;const rows=await r.json();const age=Array.isArray(rows)&&rows.length?Date.now()-Date.parse(rows[0].synced_at):NaN;return Number.isFinite(age)&&age>=0&&age<86400000;}catch{return false}
}
''' + s[i:]
    s = s.replace('launchStates:["NSW","WA","TAS","QLD"]', 'launchStates:["NSW","WA","TAS",...(await qldCoverageReady()?["QLD"]:[])]')
    i = s.index(' const nativeDeps=')
    s = s[:i] + ''' if(["support-report","support-delete"].includes(url.searchParams.get("api")||"")){const a=await supportAPI(url.searchParams.get("api")!,req,{base:()=>Deno.env.get("SUPABASE_URL")||"",headers:adminHeaders});return json(a!.body,a!.status)}
''' + s[i:]
    s = s.replace('"GET,POST,OPTIONS"', '"GET,POST,DELETE,OPTIONS"')
    s = s.replace('if(n.includes("diesel")&&!n.includes("premium"))return "Diesel";', 'if(n.includes("diesel"))return n.includes("premium")?"Premium Diesel":"Diesel";')
    s = s.replace('await removeOlderRows("fuel_site_reference",syncedAt);', 'await removeOlderRows("fuel_site_reference",syncedAt,"state_code=eq.QLD&provider_code=eq.qld-fpqld");')
    s = s.replace('async function readAllRows(table:string,select:string){', 'async function readAllRows(table:string,select:string,filter=""){')
    s = s.replace('+select+"&limit=1000&offset="+offset', '+select+(filter?"&"+filter:"")+"&order="+(table==="fuel_site_reference"?"station_id.asc":"fuel_id.asc")+"&limit=1000&offset="+offset')
    s = s.replace('const page=await r.json();if(!Array.isArray(page))break;out.push(...page);if(page.length<1000)break;offset+=1000;', 'const page=await r.json();if(!Array.isArray(page))throw new Error("invalid_reference_response");out.push(...page);if(page.length<1000)break;offset+=1000;')
    s = s.replace('readAllRows("fuel_site_reference","station_id,station_name,brand,suburb,address,postcode,latitude,longitude")', 'readAllRows("fuel_site_reference","station_id,station_name,brand,suburb,address,postcode,latitude,longitude","state_code=eq.QLD&provider_code=eq.qld-fpqld")')
    s = s.replace('const fuelsWritten=await upsertRows(', 'if(!fuelRows.length||!siteRows.length)throw new Error("qld_empty_reference_snapshot");\n const fuelsWritten=await upsertRows(')
    s = s.replace('if(!Number.isFinite(raw)||raw===9999)continue;', 'if(!Number.isFinite(raw)||raw<=0||raw===9999)continue;')
    s = s.replace('const written=await upsertFuelRows(rows);', 'if(!rows.length)throw new Error("qld_empty_price_snapshot");\n const written=await upsertFuelRows(rows);')
    s = s.replace('if(url.searchParams.get("api")==="prices"){try{', 'if(url.searchParams.get("api")==="prices"){try{if(url.searchParams.get("state")==="QLD"&&!await qldCoverageReady())return json({ok:false,rows:[],error:"coverage_pending"},503);')
    assert 'await removeOlderRows("fuel_site_reference",syncedAt);' not in s
    assert 'qld_empty_reference_snapshot' in s and 'qld_empty_price_snapshot' in s
    p.write_text(s)
    p = Path('backend/fueldrop/native-push.ts')
    n = p.read_text().replace('["NSW", "WA", "TAS"]', '["NSW", "WA", "TAS", "QLD"]')
    n = n.replace('const tz = state === "WA" ?', 'const tz = state === "QLD" ? "Australia/Brisbane" : state === "WA" ?')
    p.write_text(n)
print('Prepared local startup, private support and scoped Queensland integration; no deployment performed.')
