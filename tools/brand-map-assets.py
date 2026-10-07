"""Fetch pinned public retailer artwork once; the app serves its own logo files."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
import hashlib, json, re
ROOT=Path('web/assets/brands');ROOT.mkdir(parents=True,exist_ok=True)
ASSETS=[
('bp.svg','https://map.bp.com/fuel/assets/bp-088aaf8759de949e0de258e5f3f83e878e5f16583e0027e18c53ed3fb711acb2.svg','112caec6bcad0c52399cbf2c4235d41231017d2cd2ed7467af9f5591e90d187d'),
('shell.svg','https://www.shell.com.au/etc.clientlibs/amidala/clientlibs/theme-base/resources/favicon/favicon.svg','55bbd2451ebd8327271311ef92e65c766854602ced336d7d9677acc84607a8e7'),
('caltex.png','https://www.caltex.com/content/dam/caltex/common/icon/corporate/caltex_logo.png','b8af7d6634f644ca7beb624900ef948dd73bbb79ca7a2c6e4503de7d4c338ece'),
('ampol.svg','https://www.ampol.com.au/stardust/logos/ampol_nav_logo.svg','624113c08036629e5d4d98a444264206bb16ce4856337706e476b26aee8a5ea2'),
('united.png','https://www.unitedpetroleum.com.au/app/uploads/2016/06/united-logo-300.png','05fe52dcbea59d150986e3a543281f6c8830cac7e2c368d4d238e7c3a666c9f3'),
('metro.png','https://metropetroleum.com.au/wp-content/uploads/2020/07/Metro-Logo-Blue.png','9a7e8d3f68dacafa1ca51feab635f56b14ebc5a82f52197cbe794fbfdd971842'),
('liberty.svg','https://cdn.sanity.io/images/klkw69zd/production/88d3d01ed1d38f34b307a54e21109db15586bbad-221x58.svg','e365ae017e81e7ee745c4172c3b434cd1816782c7c9c3af5bb04f6bc51cc5db8'),
('puma.svg','https://pumaenergy.com/wp-content/uploads/2023/04/puma-logo.svg','ff70b4b47aa1c51ebd9fda37853b818985ee414339d50e9118baefcd3752b560'),
('reddy.png','https://reddyexpresscdn-beexc8djhzdufcbj.a03.azurefd.net/strapi-uploads/media-library/Reddy_Express_logo_white_c283571e60.png','48c8bf32eba4e4250e5bd215770aceaa754d390957c0e0f1e8209fbd58ea4b3d'),
('seven.svg','https://www.7eleven.com.au/','68935f869f60b1b7e16d122e35288d6f0234985b0cf485aa3444c3f0cb4dde67')]
def fetch(asset):
 name,url,sha=asset;path=ROOT/name
 if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==sha:return
 with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as response:data=response.read(600000)
 if name=='seven.svg':
  text=data.decode('utf-8');start=text.index('class="se-header__logo"')
  data=re.search(r'<svg\b[\s\S]*?</svg>',text[start:]).group(0).encode('utf-8')
 assert hashlib.sha256(data).hexdigest()==sha,'Retailer artwork changed; review before updating '+name
 if name.endswith('.svg'):
  assert b'<svg' in data and not re.search(br'<script\b|<foreignObject\b|onload\s*=|onerror\s*=',data,re.I)
 else:assert data.startswith(b'\x89PNG\r\n\x1a\n')
 path.write_bytes(data)
with ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(fetch,ASSETS))
(ROOT/'sources.json').write_text(json.dumps({'purpose':'Station identification only. FillMeNow is independent; no retailer endorsement or affiliation is implied. Trademarks remain the property of their owners.','assets':[{'file':n,'source':u,'sha256':h} for n,u,h in ASSETS]},indent=2)+'\n')
print('Verified and bundled '+str(len(ASSETS))+' retailer logos.')
