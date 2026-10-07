from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text()
if 'FMN_FINAL_VISUAL_20261007' not in s:
    marker='<style id="fillmenow-public-readiness-2026-10-07">'
    start=s.index(marker);end=s.index('</style>',start)
    css='''
/* FMN_FINAL_VISUAL_20261007 */
:root{--green:#16c94b;--green-dark:#087532;--green-soft:#e9f9ee}
body .phone-page-head{background:#fff!important;color:#15241b!important}
body .mini-wordmark:before{content:none!important}
body .mini-wordmark{display:inline-flex!important;align-items:center!important;justify-content:center!important;gap:8px!important;font-size:24px!important;letter-spacing:-1px!important;color:#0b1114!important}
body .mini-wordmark .mini-drop{width:23px;height:29px;flex:none}
body .mini-wordmark span{color:#087532!important}
body #settingsDrawer .drawer-panel p,body #settingsDrawer .info-copy{font-size:14px!important;line-height:1.6!important}
body #settingsDrawer .preset,body #settingsDrawer .drawer-choice,body #settingsDrawer .full-btn{font-size:14px!important;min-height:48px!important}
body #settingsDrawer .field label{font-size:12px!important;line-height:1.4!important}
body #settingsDrawer .field input,body #settingsDrawer .field select{font-size:16px!important;min-height:48px!important}
body #page-alerts .alert-section-label{font-size:20px!important;line-height:1.3!important;color:#15241b!important;letter-spacing:-.3px!important;text-transform:none!important}
body #page-alerts .alert-radius-card>div:nth-child(2)>div,body #page-alerts .alert-radius-card>div:nth-child(2)>div>span{font-size:12px!important;color:#526057!important}
body #page-alerts .price-input-wrap>span{font-size:12px!important;color:#526057!important}
body #page-alerts input[type="time"]{width:152px!important;min-width:152px!important;max-width:152px!important;padding:8px!important;font-size:16px!important}
body #page-alerts .radio-row small{font-size:12px!important}
body #page-saved .saved-card .brand-word,body .station-mini .brand-word{font-size:8px!important;color:#15241b!important}
body .toast{pointer-events:none}
@media(max-width:1024px){body .brand-copy strong em{color:#087532!important}}
@media(max-width:350px){body #page-alerts .alert-details .setting-line{display:grid!important;grid-template-columns:1fr!important;gap:10px!important}body #page-alerts input[type="time"]{width:100%!important;max-width:none!important}}
@media(min-width:1025px){body .bottom-nav .nav.active{color:#5eee84!important}body .bottom-nav .nav.active svg{stroke:#5eee84!important}body .desktop-detail-head .mini-wordmark{color:#fff!important}body .desktop-detail-head .mini-wordmark span{color:#5eee84!important}body .desktop-detail-head .mini-drop{filter:brightness(0) invert(1)}}
'''
    s=s[:end]+css+s[end:]
    old='<div class="mini-wordmark">Fill<span>MeNow</span></div>'
    logo='<div class="mini-wordmark"><svg class="mini-drop" viewBox="0 0 28 34" aria-hidden="true"><path fill="#0b1114" d="M14 1C10.7 7.5 3 15.2 3 23.1 3 29.2 7.9 33 14 33s11-3.8 11-9.9C25 15.2 17.3 7.5 14 1Z"/><path fill="#16c94b" d="M14 13.2c-1.8 3-5 6-5 9.1 0 2.9 2.2 5 5 5s5-2.1 5-5c0-3.1-3.2-6.1-5-9.1Z"/></svg><strong>Fill<span>MeNow</span></strong></div>'
    assert old in s;s=s.replace(old,logo)
    s=s.replace('closeStation();closeDrawer();closeArea();','closeStation();closeDrawer();closeArea();$("toast").classList.remove("show");',1)
    for ident,label in [('stateSelect','State'),('modalFuel','Fuel type')]:s=s.replace('id="'+ident+'"','id="'+ident+'" aria-label="'+label+'"',1)
if 'FMN_FINAL_REVIEW_CLOSURE_20261007' not in s:
    marker='<style id="fillmenow-public-readiness-2026-10-07">'
    end=s.index('</style>',s.index(marker))
    css='''
/* FMN_FINAL_REVIEW_CLOSURE_20261007 */
body #page-saved .add-station-btn{background:#16c94b!important;color:#102015!important}
body #page-more .phone-page-body>h1{display:block!important;font-size:28px!important;line-height:1.15!important;margin:0 0 18px!important}
'''
    s=s[:end]+css+s[end:]
    assert s.count('<h1>Notification schedule</h1>')==1
    s=s.replace('<h1>Notification schedule</h1>','<h1>Price alerts</h1>',1)
p.write_text(s)
print('Applied reviewed typography, headings and contrast; original Dash and backend unchanged.')
