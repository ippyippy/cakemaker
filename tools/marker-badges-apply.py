"""Apply the scoped station-presentation update. No provider data or settings writes."""
from pathlib import Path
import re

def change(text, old, new):
    if old not in text:
        raise RuntimeError('Expected source missing: '+old[:100])
    return text.replace(old, new, 1)

p=Path('web/index.html');s=p.read_text()
if 'FMN_MARKER_BADGES_20261010' not in s:
    artwork=re.findall(r'data:image/[^\s\"\'\)<>]+',s)
    s=change(s,'<link rel="stylesheet" href="/journey.css">','<link rel="stylesheet" href="/journey.css">\n<link rel="stylesheet" href="/marker-badges.css">')
    s=change(s,'<script src="/nearby-core.js"></script>','<script src="/nearby-core.js"></script>\n<script src="/marker-badges.js"></script>')
    s=change(s,'function renderMapMarkers(){',"""// FMN_MARKER_BADGES_20261010: only presentation consumes the existing shared result set.
function markerBadgeContext(row){return {bestId:summary?String(summary.best.station_id):null,cheapestId:summary?String(summary.cheapest.station_id):null,truck:!!window.FMNNearbyCore&&FMNNearbyCore.truckMode(prefs),review:priceNeedsReview(row)}}
function renderMapMarkers(){""")
    old="  var offer=!priceNeedsReview(x)&&Array.isArray(x._offers)&&x._offers.length>0;el.classList.toggle('has-verified-offer',offer);var badge=el.querySelector('.pin-value-label');if(badge){badge.hidden=!el.classList.contains('best')&&!offer;badge.textContent=el.classList.contains('best')?'★ Best value':'Offer';}el.dataset.bestValue=String(el.classList.contains('best'));"
    s=change(s,old,"  var presentation=FMNMarkerBadges.updateMarker(el,x,markerBadgeContext(x)),offer=presentation.offer;\n  pin.marker.setOffset([0,-8]);")
    s=change(s,'  el.title=(priceNeedsReview(x)?',"  el.setAttribute('aria-label',el.getAttribute('aria-label')+(presentation.cheapest?' Lowest pump price in these results.':'')+(presentation.truck?' Truck information available; clearance and approach require checking.':''));\n  el.title=(priceNeedsReview(x)?")
    s=change(s,'window.FMNNearbyApp={getBestId:', 'window.FMNNearbyApp={getCheapestId:function(){return summary?String(summary.cheapest.station_id):null},getBestId:')
    # Deterministic final tie breaker only. Do not add imaginary road/detour information.
    s=change(s,'return a.effective-b.effective||a.price-b.price||a.distance-b.distance})[0];','return a.effective-b.effective||a.price-b.price||a.distance-b.distance||String(a.station_id).localeCompare(String(b.station_id))})[0];')
    s=change(s,'return a.price-b.price||a.distance-b.distance})[0],nearest:', 'return a.price-b.price||a.distance-b.distance||String(a.station_id).localeCompare(String(b.station_id))})[0],nearest:')
    s=change(s,' var list=$("exactStationChoices");list.innerHTML="";', ' overlay._returnPin=chosen.element;\n var list=$("exactStationChoices");list.innerHTML="";')
    s=change(s,'chosen.element.focus()', 'overlay._returnPin?.focus({preventScroll:true})')
    s=change(s,'nearby.sort(function(a,b){return +a.station.price-+b.station.price})', 'nearby.sort(function(a,b){return Number(b.element.dataset.markerPriority)-Number(a.element.dataset.markerPriority)||+a.station.price-+b.station.price||String(a.station.station_id).localeCompare(String(b.station.station_id))})')
    s=change(s,';b.onclick=function(){overlay.classList.remove("open");openStation(x.station_id);highlightStationPin(x.station_id)};list.appendChild(b)', ';var d=FMNMarkerBadges.describe(x,markerBadgeContext(x));b.classList.toggle("best",d.best);if(d.primary){var badge=document.createElement("span");badge.className="station-badge-traits";var label=document.createElement("span");label.className="station-trait";label.textContent=d.primary;badge.append(label);b.querySelector("span").append(badge)}b.onclick=function(){overlay.classList.remove("open");openStation(x.station_id);highlightStationPin(x.station_id)};list.appendChild(b)')
    assert artwork==re.findall(r'data:image/[^\s\"\'\)<>]+',s),'Artwork changed'
    p.write_text(s)
p=Path('web/nearby-ui.js');s=p.read_text()
if 'FMNMarkerBadges.updateCard' not in s:
    s=change(s,"if(best)main.prepend(el('span','★ Best value','value-badge'));", "if(best)main.prepend(el('span','★ Best value','value-badge'));FMNMarkerBadges.updateCard(main,x,{bestId:app.getBestId?.(),cheapestId:app.getCheapestId?.(),truck:C.truckMode(context()),review:x._review});")
    s=change(s,"function badges(row,prefs){const parts=[];", "function badges(row,prefs){const parts=[];if(!C.priceReview(row)&&app.getCheapestId?.()===String(row.station_id))parts.push('<div class=\"station-badge-traits\"><span class=\"station-trait cheapest\">'+(app.getBestId?.()===String(row.station_id)?'Cheapest too':'Cheapest')+'</span></div>');")
    p.write_text(s)
p=Path('web/sw.js');s=p.read_text()
s=re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v26-marker-hierarchy-20261010';",s,count=1)
if '"/marker-badges.js"' not in s:s=change(s,'const SHELL = [','const SHELL = ["/marker-badges.js", "/marker-badges.css", ')
p.write_text(s)
# The old regression assumed the last DOM pin was on top. Exercise a real tap on
# the visible hero, then select the covered station. No forced clicks/test bypass.
p=Path('tools/exact-map-test.cjs');s=p.read_text()
old="await p.locator('[data-station-id=\"EXACT-2\"]').first().click();await p.locator('#exactStationChooser.open').waitFor();await p.locator('#exactStationChoices [data-station-id=\"EXACT-0\"]').click();"
new="await p.locator('#exploreMap .station-pin.best').click();await p.locator('#exactStationChooser.open').waitFor();assert.equal(await p.locator('#exactStationChoices [data-station-id=\"EXACT-2\"]').count(),1);await p.locator('#exactStationChoices [data-station-id=\"EXACT-2\"]').click();assert.equal(await p.locator('#exploreMap [data-station-id=\"EXACT-2\"]').getAttribute('aria-pressed'),'true');"
if old in s:s=change(s,old,new);p.write_text(s)
else:assert new in s
print('Applied larger hero, shared badges and selected-marker priority; exact coordinates and covered-station access retained.')
