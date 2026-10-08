"""Prepare Queensland-only grade and snapshot guards. No network or database calls."""
from pathlib import Path

p = Path('backend/fueldrop/index.ts')
s = p.read_text()
marker = '// FMN_QLD_GRADE_GUARD_20261009'
if marker in s:
    print('Queensland grade guard already applied.')
    raise SystemExit(0)

def replace_once(old: str, new: str) -> None:
    global s
    if s.count(old) != 1:
        raise RuntimeError('Expected one source anchor: ' + old[:100])
    s = s.replace(old, new, 1)

start = s.index('function appFuelName(name:string){')
end = s.index('function brisbaneDate(){', start)
s = s[:start] + '''// FMN_QLD_GRADE_GUARD_20261009
function appFuelName(name:string){
 // Exact provider grades only. B20 and aggregate filter names are not ordinary diesel.
 const n=String(name||"").trim().toLowerCase().replace(/\\s+/g," ");
 switch(n){
  case "unleaded": return "U91";
  case "premium unleaded 95": return "U95";
  case "premium unleaded 98": return "U98";
  case "e10": return "E10";
  case "diesel": return "Diesel";
  case "premium diesel": return "Premium Diesel";
  case "ulsd": return "ULSD";
  default: return null;
 }
}
''' + s[end:]
replace_once('String(x.app_fuel_type||"")', 'appFuelName(String(x.name||""))||""')
replace_once('const fuelFilter=String(fuel||"Diesel")==="Diesel"?"fuel_type=in.(Diesel,Premium%20Diesel)":"fuel_type=eq."+f;',
 'const fuelFilter=String(fuel||"Diesel")==="Diesel"?(st==="QLD"?"fuel_type=in.(Diesel,Premium%20Diesel,ULSD)":"fuel_type=in.(Diesel,Premium%20Diesel)"):"fuel_type=eq."+f;')
start = s.index(' const date=brisbaneDate(),syncedAt=new Date().toISOString(),rows:any[]=[];', s.index('async function syncQueenslandFuel(){'))
end = s.index(' const written=await upsertFuelRows(rows);', start)
s = s[:start] + ''' const date=brisbaneDate(),syncedAt=new Date().toISOString();
 const rows=queenslandPriceRows(qldArray(priceRes,["SitePrices","Prices","P"]),refs,date,syncedAt);
''' + s[end:]
helper = '''function queenslandPriceRows(records:any[],refs:{fuels:Map<number,string>;sites:Map<string,any>},date:string,syncedAt:string){
 const unique=new Map<string,any>();
 const allowed=new Set(["Diesel","Premium Diesel","ULSD","U91","U95","U98","E10"]);
 for(const p of records){
  if(!p||p.Price==null||p.Price==="")continue;
  const raw=Number(p.Price);if(!Number.isFinite(raw)||raw<=0||raw===9999)continue;
  const fuelType=refs.fuels.get(Number(p.FuelId));if(!fuelType||!allowed.has(fuelType))continue;
  const site=refs.sites.get(String(p.SiteId));if(!site)continue;
  if(site.latitude==null||site.longitude==null||site.latitude===""||site.longitude==="")continue;
  const lat=Number(site.latitude),lng=Number(site.longitude);
  if(!Number.isFinite(lat)||!Number.isFinite(lng)||lat< -29.5||lat> -9||lng<137||lng>154.5)continue;
  let transaction:string|null=null;
  if(p.TransactionDateUtc!=null&&p.TransactionDateUtc!==""){
   const text=String(p.TransactionDateUtc).trim();
   if(!/^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:?\\d{2})?$/.test(text))throw new Error("qld_invalid_price_timestamp");
   const timestamp=Date.parse(/[zZ]|[+-]\\d{2}:?\\d{2}$/.test(text)?text:text+"Z");
   if(!Number.isFinite(timestamp))throw new Error("qld_invalid_price_timestamp");
   transaction=new Date(timestamp).toISOString();
  }
  const row={station_id:String(p.SiteId),state_code:"QLD",provider_code:"qld-fpqld",fuel_type:fuelType,price_date:date,station_name:String(site.station_name||"Fuel station"),brand:site.brand||null,suburb:site.suburb||null,address:String(site.address||""),postcode:site.postcode?String(site.postcode):null,latitude:lat,longitude:lng,price:raw/10,transaction_date_utc:transaction,synced_at:syncedAt};
  const key=row.station_id+"|"+fuelType,prior=unique.get(key);
  if(prior&&prior.price!==row.price&&(!prior.transaction_date_utc||!transaction||prior.transaction_date_utc===transaction))throw new Error("qld_conflicting_price_rows");
  if(!prior||(transaction||"")>(prior.transaction_date_utc||""))unique.set(key,row);
 }
 if(!unique.size)throw new Error("qld_empty_price_snapshot");
 return [...unique.values()];
}
'''
replace_once('async function syncQueenslandFuel(){', helper + 'async function syncQueenslandFuel(){')
p.write_text(s)
print('Prepared Queensland fuel-grade and duplicate-snapshot guard; no import performed.')
