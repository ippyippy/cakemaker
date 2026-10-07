"""Preserve v61 public asset bytes as build-time constants, never runtime fetches."""
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib, json
BASE='https://psytztnkeeymavzmpomv.supabase.co/functions/v1/fueldrop'
ASSETS=[
 ('HTML','','215e2fb824b1546ee3904cddbcbf1b6c1865b8ba48c462ea535c135639157e3d'),
 ('ICON','?asset=icon','cc9fce6903f6f88ea105fca1293228dbe9b0da27e75cede5bb111720751b0ce7'),
 ('MANIFEST','?asset=manifest','06a5f3897adc6cca79e84a270f451ec345d72cdf815b9c02b14d880fa4088f10'),
 ('SW','?asset=sw','f7bc4a6286f47d9226786e70735f45087424dbb81ea08307980b5357c2494113')
]
def capture(row):
 name,query,digest=row
 with urlopen(BASE+query,timeout=20) as response:
  assert response.status==200, name+' HTTP status'
  raw=response.read()
 assert hashlib.sha256(raw).hexdigest()==digest, name+' changed; stop for review rather than replacing blindly'
 return name,raw.decode('utf-8')
path=Path('backend/fueldrop/legacy-assets.ts')
if path.exists():
 print('Existing immutable legacy snapshot retained.')
else:
 with ThreadPoolExecutor(max_workers=4) as pool: assets=list(pool.map(capture,ASSETS))
 text='// Build-time snapshot of the existing v61 public assets. Do not fetch these at runtime.\n'
 for name,value in assets:text+='export const '+name+' = '+json.dumps(value,ensure_ascii=True)+';\n'
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
 print('Snapshotted four hash-verified existing assets; no UI redesign or runtime network dependency.')
