"""Apply the reviewed repair once, to the existing FillMeNow page; no new app or API."""
from pathlib import Path
import json, re

p = Path('web/index.html')
s = p.read_text()
assert 'fillmenow-id-clarity-2026-10-06' in s, 'Unexpected source version; review before applying.'

def once(old, new):
    global s
    assert s.count(old) == 1, f'Expected exactly one match: {old[:80]}'
    s = s.replace(old, new, 1)

once('function showPage(p){\n Array.from', 'function showPage(p){\n if(!$("page-"+p))return;\n closeStation();closeDrawer();closeArea();\n Array.from')
once('summary=null;if(!loc||!rows.length){ranked=[];', 'summary=null;ranked=[];if(!loc||!rows.length){')
once('function openDrawer(which){var d=', 'function openDrawer(which){if(!$("page-more").classList.contains("active"))showPage("more");var d=')
once('frequency:"daily",time1:', 'alertRadius:20,frequency:"daily",time1:')
once('radius_km:prefs.radius,tank_litres:', 'radius_km:prefs.alertRadius||prefs.radius,tank_litres:')
once('$("alertRadius").value=Math.min(50,Math.max(5,prefs.radius));$("alertRadiusValue").textContent=prefs.radius+" km"', '$("alertRadius").value=Math.min(50,Math.max(5,prefs.alertRadius||prefs.radius));$("alertRadiusValue").textContent=$("alertRadius").value+" km"')
once('prefs.frequency=frequency;prefs.time1=', 'prefs.alertRadius=Math.min(50,Math.max(5,Number($("alertRadius").value)||20));prefs.frequency=frequency;prefs.time1=')
old='if($("alertRadius"))$("alertRadius").oninput=function(){var allowed=[5,10,20,30,50],v=+this.value,best=allowed.reduce(function(a,n){return Math.abs(n-v)<Math.abs(a-v)?n:a},allowed[0]);prefs.radius=best;$("alertRadiusValue").textContent=best+" km";$("radiusSelect").value=String(best);if($("mobileRadiusSelect"))$("mobileRadiusSelect").value=String(best);persist();syncSub()};'
once(old, 'if($("alertRadius"))$("alertRadius").oninput=function(){$("alertRadiusValue").textContent=this.value+" km"};')
once('<div class="app">', '<main class="app" id="appMain">')
once('</nav>\n\n<div class="modal-bg" id="areaModal">', '</nav>\n\n<div class="modal-bg" id="areaModal" role="dialog" aria-modal="true" aria-label="Choose your area">')
once('<div class="modal-bg" id="stationModal">', '<div class="modal-bg" id="stationModal" role="dialog" aria-label="Station details">')
once('<div class="settings-drawer" id="settingsDrawer">', '<div class="settings-drawer" id="settingsDrawer" role="dialog" aria-label="App settings">')
once('<div class="toast" id="toast"></div>', '<div class="toast" id="toast" role="status" aria-live="polite"></div>\n</main>')
# The original .app was never closed. The new main now has an explicit matching close.
labels = {'topArea':'Choose location','gpsBtn':'Use current location','recenterBtn':'Re-centre map','mapSettingsBtn':'Map settings','pushSwitch':'Enable notifications','drawerBack':'Back to More','stationClose':'Close station details','notifyTime':'First alert time','notifyTime2':'Second alert time','priceDrop':'Price threshold in cents per litre','alertRadius':'Alert radius in kilometres','locationSearch':'Suburb or postcode','tankInput':'Typical fill in litres','economyInput':'Fuel use in litres per 100 kilometres'}
for ident, label in labels.items():
    needle='id="'+ident+'"'
    # Some identifiers also occur inside script string selectors; only exact HTML attributes match.
    assert s.count(needle)==1, ident
    s=s.replace(needle, needle+' aria-label="'+label+'"',1)
once('id="sheetHandle" aria-label=', 'id="sheetHandle" role="button" tabindex="0" aria-controls="sheetMain" aria-label=')
once('id="sheetPeek" role="button" tabindex="0"', 'id="sheetPeek" role="button" tabindex="-1" aria-controls="sheetMain"')
once('var handle=$("sheetHandle");if(handle)handle.setAttribute("aria-expanded",collapsed?"false":"true");', 'var handle=$("sheetHandle");if(handle)handle.setAttribute("aria-expanded",collapsed?"false":"true");var peek=$("sheetPeek");if(peek)peek.tabIndex=collapsed?0:-1;')
once('installSheetGestures();$("stationClose")', '$("sheetHandle").onkeydown=function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();setSheetCollapsed(!$("mobileSheet").classList.contains("is-collapsed"))}};installSheetGestures();$("stationClose")')
once('if(e.key!=="Escape")return;', 'if(e.key!=="Escape")return;\n if($("settingsDrawer").classList.contains("open")){closeDrawer();return}')

css = r'''<style id="fillmenow-public-readiness-2026-10-07">
:root{--muted:#526057}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,[role="button"]:focus-visible{outline:3px solid #087532!important;outline-offset:3px}
button:disabled{opacity:.55;cursor:wait}
body .phone-sub,body .lead,body .drawer-panel p,body .info-copy{font-size:14px!important;line-height:1.55!important;color:#526057!important}
body .phone-page-body h1{font-size:28px!important;line-height:1.15!important}
body .phone-page-head .back-btn{color:#15241b!important;min-width:44px;min-height:44px}
body .phone-page-head .mini-wordmark span{color:#087532!important}
body .settings-drawer{overflow-y:auto;overscroll-behavior:contain}
body .drawer-head{position:sticky;top:0;z-index:2}
body .field label,body .filter-strip span{font-size:12px!important;line-height:1.3!important;color:#526057!important}
body .field input,body .field select{font-size:16px!important;min-height:48px!important}
body .drawer-choice,body .preset,body .full-btn{font-size:14px!important;min-height:48px!important}
body #page-more .menu-row b{font-size:16px!important;line-height:1.3!important}
body #page-more .menu-row small,body #page-more #installStatus{font-size:13px!important;line-height:1.45!important;color:#526057!important}
body #page-more .menu-row{min-height:78px!important}
body #page-more .reset-link{font-size:13px!important;min-height:44px}
body #page-alerts .settings-topline b,body #page-alerts .setting-line b,body #page-alerts .radio-row b{font-size:14px!important;line-height:1.3!important}
body #page-alerts .settings-topline small,body #page-alerts .setting-line small,body #page-alerts .radio-row small,body #page-alerts #pushStatus{font-size:12px!important;line-height:1.45!important;color:#526057!important}
body #page-alerts .alert-frequency-card .radio-row{grid-template-columns:24px minmax(0,1fr)!important;gap:10px!important;min-height:90px!important}
body #page-alerts .setting-line input{font-size:16px!important;max-width:132px;min-height:44px!important}
body #page-alerts .alert-actions .btn{font-size:14px!important;min-width:64px;min-height:48px!important}
body #page-alerts .alert-actions .btn-go{color:#102015!important}
body #page-saved .saved-card b{font-size:15px!important;line-height:1.35!important}
body #page-saved .saved-card span{font-size:12px!important;line-height:1.4!important}
body #page-saved .saved-card .btn,body #page-saved .add-station-btn{font-size:14px!important;min-height:48px!important}
body #page-saved .add-station-btn{color:#102015!important}
body #page-saved .saved-card{grid-template-columns:minmax(0,1fr) auto;gap:12px!important}
body #page-saved .saved-card>div>div{min-width:0;overflow-wrap:anywhere}
body[data-page="options"] .filter-strip select,body[data-page="options"] .filter-strip b{font-size:15px!important;height:auto!important;line-height:1.3!important}
body[data-page="options"] .option-row{grid-template-columns:48px minmax(0,1fr) 58px!important;gap:12px!important;padding:14px 12px!important;min-height:144px!important}
body[data-page="options"] .option-brand{width:48px!important}
body[data-page="options"] .brand-rank{width:48px!important;height:auto!important;display:flex!important;flex-direction:column!important;gap:8px!important}
body[data-page="options"] .brand-rank .brand-mark{width:40px!important;height:40px!important;flex:0 0 40px!important}
body[data-page="options"] .brand-rank-number{position:static!important;order:0!important;width:26px!important;min-width:26px!important;height:26px!important;flex:0 0 26px!important;border:0!important;line-height:1!important;font-size:13px!important}
body[data-page="options"] .option-main b{font-size:15px!important;line-height:1.3!important;overflow-wrap:anywhere}
body[data-page="options"] .option-main strong{font-size:26px!important;line-height:1.2!important;margin-top:5px!important}
body[data-page="options"] .option-main span{font-size:12px!important;line-height:1.4!important;color:#526057!important}
body[data-page="options"] .option-main .option-id{display:inline-block!important;font-size:14px!important;font-weight:750;line-height:1.4!important;padding:4px 7px;margin:5px 0!important;background:#e9f9ee;border-radius:6px;color:#087532!important;overflow-wrap:anywhere}
body[data-page="options"] .option-main .option-save{color:#087532!important}
body[data-page="options"] .option-go{width:58px!important;min-width:58px!important;min-height:48px!important;font-size:14px!important}
body #areaModal .modal p,body #areaModal .suggestion,body #areaModal .region,body #areaModal .btn{font-size:14px!important;line-height:1.4!important}
body .bottom-nav .nav{font-size:12px!important}
body .bottom-nav .nav.active{color:#087532!important}
body .bottom-nav .nav.active svg{stroke:currentColor!important}
body .toast{font-size:14px!important;max-width:calc(100vw - 24px);line-height:1.4;text-align:center}
body #stationModal .best-detail-map{display:none!important}
body #stationModal .best-detail-head{background:#fff!important;color:#15241b;border-bottom:1px solid #dfe6df}
body #stationModal .best-detail-head .mini-wordmark{color:#15241b!important}
body #stationModal .best-detail-head .mini-wordmark span{color:#087532!important}
body #stationModal .back-btn{color:#15241b!important;min-width:44px;min-height:44px}
body #stationModal .station-mini.id-mini{grid-column:1/-1!important;background:#effbf2;border:1px solid #cee9d5}
body #stationModal .station-mini span{font-size:12px!important;color:#526057!important}
body #stationModal .station-mini b{font-size:17px!important;line-height:1.3!important;overflow-wrap:anywhere}
body #stationModal .station-mini.price-mini b{display:flex!important;gap:8px!important;align-items:center}
body #stationModal .best-detail-card>p{font-size:14px!important;line-height:1.5!important}
body #stationModal .best-detail-card h2{flex-wrap:nowrap!important;align-items:flex-start!important}
body #stationModal .best-detail-card h2>span:last-child{min-width:0;overflow-wrap:anywhere;margin-left:0!important}
body #stationModal .best-detail-go,body #stationModal .detail-bottom-actions .btn{font-size:14px!important;min-height:48px!important}
@media(max-width:900px){
 :root{--fmn-nav:calc(64px + env(safe-area-inset-bottom,0px))}
 body[data-page="explore"]{height:100dvh!important;overflow:hidden!important;padding-bottom:0!important}
 body.subpage-mobile{padding-bottom:0!important}
 body #page-explore .explore{padding:0!important}
 body #page-explore .map-shell{height:calc(100dvh - 78px - var(--fmn-nav))!important;min-height:0!important}
 body #page-explore .map{height:100%!important;min-height:0!important}
 body .bottom-nav{height:var(--fmn-nav)!important;padding:4px 6px calc(4px + env(safe-area-inset-bottom,0px))!important}
 body .phone-page-body{padding-bottom:calc(88px + env(safe-area-inset-bottom,0px))!important}
 body #page-explore .mobile-sheet{bottom:var(--fmn-nav)!important;width:100%!important;max-height:calc(100dvh - 118px - var(--fmn-nav))!important}
 body #page-explore .mobile-sheet .sheet-main{min-height:0!important;padding:14px 16px!important;max-height:calc(100dvh - 142px - var(--fmn-nav));overflow-y:auto!important}
 body #page-explore .sheet-main:before{width:96px!important;height:76px!important;right:16px!important;top:-42px!important;pointer-events:none}
 body #page-explore .sheet-top{padding-right:0!important}
 body #page-explore .sheet-label{font-size:11px!important;line-height:1.2!important;margin-right:100px!important;color:#102015!important}
 body #page-explore .sheet-station{font-size:17px!important;white-space:normal!important;max-width:none!important;line-height:1.3!important;margin-top:12px!important}
 body #page-explore .sheet-price{font-size:38px!important;line-height:1.1!important;margin-top:6px!important}
 body #page-explore .sheet-meta{font-size:13px!important;line-height:1.5!important;color:#526057!important}
 body #page-explore .sheet-save b{font-size:16px!important;color:#087532!important}
 body #page-explore .sheet-save span{font-size:12px!important;color:#526057!important}
 body #page-explore .sheet-go{font-size:16px!important;min-height:48px!important;color:#102015!important}
 body #page-explore .sheet-options-link{font-size:14px!important;min-height:44px!important}
 body #page-explore .mobile-sheet.is-collapsed{width:96px!important;height:88px!important;max-height:none!important;right:8px!important;left:auto!important;bottom:var(--fmn-nav)!important;background:transparent!important;box-shadow:none!important;border:0!important}
 body #page-explore .mobile-sheet.is-collapsed .sheet-main,body #page-explore .mobile-sheet.is-collapsed .sheet-handle{display:none!important}
 body #page-explore .mobile-sheet.is-collapsed .sheet-peek>*{display:none!important}
 body #stationModal{padding:94px 8px calc(var(--fmn-nav) + 8px)!important;background:transparent!important;backdrop-filter:none!important;pointer-events:none!important;align-items:flex-end!important;justify-content:center!important}
 body #stationModal .best-detail-modal{pointer-events:auto!important;width:min(560px,100%)!important;height:auto!important;max-height:100%!important;border-radius:16px!important;overflow-y:auto!important;border:1px solid #dfe6df!important;box-shadow:0 12px 42px #15241b30}
 body #stationModal .best-detail-head{position:sticky;top:0;z-index:2}
 body #stationModal .best-detail-card{max-height:none!important;overflow:visible!important;padding:16px!important}
 body #page-alerts .alert-frequency-card{grid-template-columns:1fr!important}
 body #page-alerts .alert-frequency-card .radio-row{grid-column:1!important;border-right:0!important;min-height:76px!important}
 body .drive.open{overflow-y:auto!important}
 body .drive-body{display:block!important}
 body .drive-card:before{height:clamp(110px,24dvh,190px)!important}
}
@media(max-width:900px) and (max-height:600px){body #page-explore .sheet-main{touch-action:pan-y!important}body #page-explore .sheet-main:before{display:none!important}}
@media(min-width:901px){
 body .control span,body .mini-stat span,body .eyebrow{font-size:12px!important}
 body .control b,body .control select,body .mini-stat b{font-size:15px!important}
 body .best-meta,body .reason,body .saving span{font-size:13px!important;line-height:1.45!important}
 body .btn,body .drive-btn,body .alt-all{font-size:14px!important;min-height:44px!important}
 body .compact-alt-main b{font-size:14px!important}
 body .compact-alt-main span,body .alt-price span{font-size:12px!important}
 body .compact-alt{grid-template-columns:40px minmax(0,1fr) auto!important;min-height:70px}
 body .decision-column{display:block;max-height:calc(100dvh - 90px)!important;overflow-y:auto!important}
 body .decision-column .decision-overview{display:grid;gap:12px}
 body .decision-column.detail-open .decision-overview{display:none}
 body .top-area,body .map-search{font-size:14px!important}
 body #desktopStationAddress{font-size:13px}
 body #desktopStationMetrics .station-mini span{font-size:12px}
 body #desktopStationMetrics .station-mini b{font-size:16px;overflow-wrap:anywhere}
}
@media(prefers-reduced-motion:reduce){body .mobile-sheet,body .toast{transition:none!important}}
</style>'''
s=re.sub(r'<style id="fillmenow-id-clarity-2026-10-06">[\s\S]*?</style>',lambda _:css,s,count=1)
p.write_text(s)
# Existing service worker: cache the actual local shell dependencies, not live price responses.
p=Path('web/sw.js');t=p.read_text();t=t.replace("fillmenow-web-v4", "fillmenow-web-v5-20261007");t=t.replace("'/icons/icon-512.png'];", "'/icons/icon-512.png', '/assets/maplibre.js', '/assets/maplibre.css', '/privacy', '/terms'];");p.write_text(t)
p=Path('web/manifest.webmanifest');j=json.loads(p.read_text());j['background_color']='#ffffff';j['theme_color']='#ffffff';p.write_text(json.dumps(j,indent=2)+'\n')
print('Repaired existing web source. Original Dash image bytes and backend URL unchanged.')
