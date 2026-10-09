"""Apply reviewed UI changes without changing prices, GPS, records or routing."""
from pathlib import Path
import re
marker='FMN_VALUE_TRUCK_ACTIONS_20261009'
p=Path('web/index.html'); html=p.read_text()
if marker in html:
 print('Value and truck actions already applied.'); raise SystemExit(0)
def once(s,old,new):
 assert s.count(old)==1,(old[:90],s.count(old))
 return s.replace(old,new,1)
original_art=re.findall(r'data:image/[^\s\"\'\)<>]+',html)
html=once(html,'window.FMNNearbyApp={refreshResults:',"// "+marker+"\nwindow.FMNNearbyApp={getBestId:function(){return summary?String(summary.best.station_id):null},getStation:find,refreshResults:")
html=once(html,'summary=areaText();\n if(!summary){','summary=areaText();$("mobileSheet").classList.toggle("has-best-value",!!summary);\n if(!summary){')
html=once(html,"+'<span class=\"pin-price\">'+(+x.price).toFixed(1)+'<small>¢</small></span>';pin.signature=sig}","+'<span class=\"pin-price\">'+(+x.price).toFixed(1)+'<small>¢</small></span><span class=\"pin-value-label\" hidden></span>';pin.signature=sig}")
needle='el.dataset.latitude=String(x.latitude);'
html=once(html,needle,"var offer=!priceNeedsReview(x)&&Array.isArray(x._offers)&&x._offers.length>0;el.classList.toggle('has-verified-offer',offer);var badge=el.querySelector('.pin-value-label');if(badge){badge.hidden=!el.classList.contains('best')&&!offer;badge.textContent=el.classList.contains('best')?'★ Best value':'Offer';}el.dataset.bestValue=String(el.classList.contains('best'));\n  "+needle)
html=once(html,'el.setAttribute("aria-label",x.station_name+', 'el.setAttribute("aria-label",(el.classList.contains("best")?"Best estimated value. ":offer?"Active offer; check conditions. ":"")+x.station_name+')
html=once(html,"return '<div class=\"best-price fuel-price\">'+brandMark(b.brand,b.station_name)","return '<span class=\"value-badge\">★ Best value</span><div class=\"best-price fuel-price\">'+brandMark(b.brand,b.station_name)")
html=once(html,"+' km · est. '+b.etaMin+' min · '+esc(b.fuel_type||prefs.fuel)+'</div></div><div class=\"sheet-save\">", "+' km · est. '+b.etaMin+' min · '+esc(b.fuel_type||prefs.fuel)+'</div>'+(['truck','heavy'].includes(prefs.vehicle)?'<div class=\"best-truck-caution\">Value comparison only · truck access needs checking</div>':'')+'</div><div class=\"sheet-save\">")
ui_path=Path('web/nearby-ui.js'); ui=ui_path.read_text()
ui=once(ui,"row.classList.toggle('best',i===0&&!x._review&&useFilters().sort==='value');const main=row.querySelector('.option-main');", "const best=!x._review&&app.getBestId?.()===String(x.station_id);row.classList.toggle('best',best);const main=row.querySelector('.option-main');if(best)main.prepend(el('span','★ Best value','value-badge'));row.classList.toggle('has-verified-offer',!x._review&&x._offers.length>0);")
ui=once(ui,"if(C.truckMode(context())){main.appendChild(el('span',x._access.label,'nearby-badge '+x._access.status));", "if(C.truckMode(context())){main.appendChild(el('span',x._access.label,'nearby-badge '+x._access.status));const check=el('button','Check truck access','truck-check-button');check.type='button';check.onclick=()=>showAccessCheck(x);main.append(check);")
ui=once(ui,"function badges(row,prefs){const parts=[];", "function badges(row,prefs){const parts=[];if(!C.priceReview(row)&&app.getBestId?.()===String(row.station_id)){parts.push('<div class=\"value-badge\">★ Best value · estimated trip cost</div>');}")
ui=once(ui,"const facility=C.facilityFor(row,prefs,catalog);if(facility){", "const control=el('button','Check truck access','truck-check-button');control.type='button';control.dataset.stationAccess=String(row.station_id);parts.push(control.outerHTML);const facility=C.facilityFor(row,prefs,catalog);if(facility){")
ui=once(ui,"Station access is not verified until measured, dated records are available. Standard directions do not use these truck dimensions.","Truck-stop listings do not confirm your dimensions. Check the entrance, fuel-bay clearance and exit with the operator before travel. Standard directions are not truck routing.")
ui=once(ui,"installVehicleAutosave();}","installVehicleAutosave();buildVehicleSearch();}")
ui=once(ui,"window.FMNNearbyUI={getFilters:","""// FMN_VALUE_TRUCK_ACTIONS_20261009
function buildVehicleSearch(){
 const panel=document.getElementById('drawer-vehicle');if(!panel)return;
 let section=document.getElementById('vehicleStationSearch');
 if(!section){section=el('section',undefined,'vehicle-station-search');section.id='vehicleStationSearch';section.append(el('h3','Find fuel for your truck'),el('p','Choose operator-listed truck stops, or only stations with recorded height clearance. Your destination and distance filters stay active.'));
  const facilities=el('button','Find truck stops','truck-search-primary');facilities.type='button';facilities.id='vehicleFindTruckStops';facilities.onclick=()=>vehicleSearch('truckstops');
  const height=el('button','Check recorded height','truck-search-secondary');height.type='button';height.id='vehicleFindHeight';height.onclick=()=>vehicleSearch('height');section.append(facilities,height);
  document.getElementById('vehicleSaveStatus').after(section);
 }section.hidden=!C.truckMode(context());
}
function vehicleSearch(mode){if(!saveVehicle()){const n=document.getElementById('truckSaveError');n.scrollIntoView({block:'nearest'});return;}setAccess(mode);window.FD.options();}
function showAccessCheck(row){
 if(!row||!C.truckMode(context()))return;
 const d=modal('Check truck access'),body=d.querySelector('.nearby-scroll'),ctx=context(),t=ctx.truck||{},facility=C.facilityFor(row,ctx,catalog),status=C.truckAccess(row,ctx,catalog);
 body.append(el('h3',row.station_name),el('p',(t.height||'—')+' m high · '+(t.width||'—')+' m wide · '+(t.length||'—')+' m long · '+(t.weight||'—')+' t','truck-check-profile'),el('div',status.label+'. A green price badge means value, not truck clearance.','nearby-warning'));
 if(facility){body.append(el('p',facility.note));const source=el('a','Open operator details','truck-contact-link');source.href=facility.source_url;source.target='_blank';source.rel='noopener noreferrer';body.append(source);const phone=String(facility.phone||'').replace(/[ ()-]/g,'');if(/^\\+?[0-9]{8,15}$/.test(phone)){const call=el('a','Call operator to confirm','truck-contact-link');call.href='tel:'+phone;body.append(call);}body.append(el('p','Operator listing checked '+new Date(facility.checked_at).toLocaleDateString('en-AU')+'. Not a measured-clearance certificate.','truck-source-date'));}
 else body.append(el('p','No checked operator contact or access measurements are published for this station yet. Do not assume your truck fits.'));
 body.append(el('h3','Ask before you travel'),el('p','Can a '+(t.height||'specified-height')+' m high, '+(t.width||'specified-width')+' m wide, '+(t.length||'specified-length')+' m long vehicle at '+(t.weight||'specified')+' tonnes enter, use the diesel bay and exit? Confirm the lowest signed clearance, the correct truck entrance and enough turning room.'));
 body.append(el('p','Check while parked. This app does not verify the approach road or record a phone call as a verified measurement.'));
}
function installOptionsFooter(){const back=document.getElementById('optionsBack'),page=document.getElementById('page-options');if(!back||!page||document.getElementById('optionsFooter'))return;const gap=el('span',undefined,'head-spacer');gap.setAttribute('aria-hidden','true');back.before(gap);const footer=el('div',undefined,'options-footer');footer.id='optionsFooter';footer.append(back);page.append(footer);}
window.FMNNearbyUI={getFilters:""")
ui=once(ui,"toolbar();syncVehicle();loadCatalogue();", "toolbar();syncVehicle();installOptionsFooter();document.addEventListener('click',e=>{const n=e.target.closest?.('[data-station-access]');if(n){e.preventDefault();const row=app.getStation?.(n.dataset.stationAccess);if(row)showAccessCheck(row);}});loadCatalogue();")
css_path=Path('web/nearby.css'); css=css_path.read_text()+r'''
/* FMN_VALUE_TRUCK_ACTIONS_20261009: green means financial value, never a clearance approval. Existing marker stacking is retained. */
body .value-badge{display:inline-flex!important;align-items:center;gap:5px;width:fit-content;max-width:100%;padding:5px 9px;margin:0 0 9px;border-radius:8px;background:#087532;color:#fff!important;font-size:13px!important;font-weight:800!important;line-height:1.3!important;letter-spacing:0;box-sizing:border-box}
body #optionsList .option-row.best{background:#effbf3!important;border:2px solid #087532!important;box-shadow:0 2px 10px #0875321f!important}
body #optionsList .option-row.best .option-main>strong{color:#087532!important}
body #optionsList .option-row.has-verified-offer .nearby-offer-button,body .offer-card h3{background:#087532!important;color:#fff!important;border-color:#087532!important}
body #page-explore .price-marker.station-pin.best{background:#effbf3!important;border-color:#087532!important}
body #page-explore .price-marker.station-pin.best.selected{border-color:#184ece!important}
body #page-explore .price-marker.station-pin.best .pin-price,body #page-explore .price-marker.station-pin.has-verified-offer .pin-price{background:#087532!important;color:#fff!important;border-radius:5px;padding:0 3px!important;box-sizing:border-box}
body #page-explore .price-marker.station-pin .pin-value-label{position:absolute!important;left:50%!important;top:-18px!important;transform:translateX(-50%)!important;background:#087532!important;color:#fff!important;border:1px solid white!important;border-radius:6px!important;font-size:11px!important;font-weight:800!important;line-height:15px!important;padding:1px 5px!important;white-space:nowrap!important;pointer-events:none!important}
body #page-explore .pin-value-label[hidden]{display:none!important}
body #page-explore .mobile-sheet.has-best-value .sheet-label{background:#087532!important;color:#fff!important}
body #page-explore .mobile-sheet.has-best-value .sheet-price,body #desktopBest .best-price{color:#087532!important}
body .best-truck-caution{font-size:13px!important;line-height:1.4!important;color:#624512!important;background:#fff5df;border-radius:8px;padding:7px 9px;margin-top:8px;max-width:100%}
body .truck-check-button,body .truck-contact-link{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:9px 12px;margin:8px 6px 0 0;box-sizing:border-box;border:1px solid #aebeb4;border-radius:10px;background:#fff;color:#193f2a;font-size:14px;line-height:1.4;font-weight:750;text-decoration:underline;cursor:pointer}
body .vehicle-station-search{margin:18px 0 10px;padding:16px;border:1px solid #c7d6cd;border-radius:12px;background:#f5f9f6}
body .vehicle-station-search h3{font-size:18px!important;line-height:1.3;margin:0 0 8px}
body .vehicle-station-search p{font-size:14px!important;line-height:1.5!important;margin:0 0 12px}
body .vehicle-station-search button{display:block;width:100%;min-height:46px;padding:11px 12px;margin-top:10px;white-space:normal;line-height:1.4;border:1px solid #087532;border-radius:10px;font-size:15px;font-weight:800;cursor:pointer}
body .truck-search-primary{background:#087532;color:white}body .truck-search-secondary{background:white;color:#193f2a}
body #vehicleStationSearch[hidden]{display:none!important}
body .truck-check-profile{font-size:16px!important;font-weight:750;line-height:1.5}body .truck-source-date{font-size:13px!important;line-height:1.5;color:#506258}
body #page-options{padding-bottom:calc(var(--fmn-nav,64px) + 90px)!important}
body #page-options #optionsFooter{position:fixed;bottom:var(--fmn-nav,64px);left:0;right:0;background:#fff;border-top:1px solid #dfe6df;padding:10px 14px;z-index:1010;box-sizing:border-box}
body #page-options #optionsFooter #optionsBack.bottom-page-back{position:static!important;box-shadow:none!important;font-size:16px!important}
@media(min-width:1025px){body #page-options #optionsFooter{left:78px;bottom:0}body #page-options{padding-bottom:90px!important}}
'''
sw_path=Path('web/sw.js');sw=once(sw_path.read_text(),'fillmenow-web-v22-shared-search-20261009','fillmenow-web-v23-value-truck-20261009')
assert original_art==re.findall(r'data:image/[^\s\"\'\)<>]+',html),'Mascot/brand artwork must not change'
for path,content in [(p,html),(ui_path,ui),(css_path,css),(sw_path,sw)]:path.write_text(content)
print('Applied green financial highlights and explicit truck search/contact actions; all embedded artwork preserved.')
