from pathlib import Path
p=Path('tools/exact-map-functions.js');s=p.read_text().replace('desktop.closest(".desktop-station-panel")','desktop.closest(".desktop-station-detail")')
s=s.replace('if(shell.classList.contains("modal")){var scroll=', 'if(shell.classList.contains("modal")){shell.style.setProperty("padding","0","important");var scroll=')
p.write_text(s)
p=Path('tools/exact-map-test.cjs');s=p.read_text().replace('center:[151.2193,-33.8688]','center:[151.2093,-33.8688]');p.write_text(s)
# Rerunnable source-anchor repair, including a previously applied local test checkout.
p=Path('web/index.html');s=p.read_text()
if 'FMN_EXACT_PINS_APPLIED_20261008' in s:
 a=s.index('function markerProfile(){');b=s.index('function renderMap(){',a)
 s=s[:a]+Path('tools/exact-map-functions.js').read_text()+s[b:]
 p.write_text(s)
