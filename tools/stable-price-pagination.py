"""Apply the narrow pagination repair in the existing API; no network or data writes."""
from pathlib import Path
p = Path('backend/fueldrop/index.ts')
s = p.read_text()
old = '+"&order=price.asc&limit="+pageSize+"&offset="+offset'
new = '+"&order=price.asc,station_id.asc,fuel_type.asc&limit="+pageSize+"&offset="+offset'
if new not in s:
    assert s.count(old) == 1, 'Expected exactly one existing paginated price query'
    s = s.replace(old, new, 1)
    p.write_text(s)
assert new in p.read_text()
print('Prepared stable price/station/grade ordering; public UI and provider imports unchanged.')
