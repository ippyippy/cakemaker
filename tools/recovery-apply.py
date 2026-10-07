"""Repair async location selection and actionable empty states in the existing app."""
from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text();marker='FMN_RECOVERY_20261008'
if marker not in s:
    original_images=re.findall(r'data:image/[^\s\"\)]+',s)
    original_backend=re.search(r'const BACKEND=([^;]+);',s).group(0)
    def replace(old,new):
        global s
        assert s.count(old)==1, f'Expected one guarded source anchor: {old[:80]}'
        s=s.replace(old,new,1)
    def replace_function(start,end,new):
        global s
        a=s.index(start);b=s.index(end,a);s=s[:a]+new+'\n'+s[b:]
    regions=r'''// FMN_RECOVERY_20261008: stale area requests cannot change the selected state.
var regionRequest=0,regionAbort=null,searchAbort=null;
function locationFeedback(box,message,retry){
 box.innerHTML='<div class="location-feedback"><div role="status">'+esc(message)+'</div>'+(retry?'<button type="button" class="btn btn-soft">Try again</button>':'')+'</div>';
 var button=box.querySelector('button');if(button)button.onclick=retry;
}
async function loadRegions(){
 var request=++regionRequest,state=prefs.state,box=$("regions");
 if(regionAbort)regionAbort.abort();var controller=regionAbort=new AbortController();
 box.setAttribute("aria-busy","true");locationFeedback(box,"Loading popular areas…");
 var timeout=setTimeout(function(){controller.abort()},12000);
 try{
  var r=await fetch(api({api:"regions",state:state}),{signal:controller.signal});if(!r.ok)throw Error("regions unavailable");
  var j=await r.json();if(request!==regionRequest||state!==prefs.state)return;
  if(!j||j.error||!Array.isArray(j.regions))throw Error("invalid regions");
  var a=j.regions.filter(function(x){return x&&String(x.region_name||"").trim()&&x.latitude!=null&&x.longitude!=null&&Number.isFinite(+x.latitude)&&Number.isFinite(+x.longitude)&&Math.abs(+x.latitude)<=90&&Math.abs(+x.longitude)<=180});
  if(!a.length){locationFeedback(box,"No popular areas available in "+state+". Search a suburb or postcode above.");return}
  box.innerHTML=a.map(function(x,i){return '<button type="button" class="region" data-i="'+i+'">'+esc(x.region_name)+'</button>'}).join("");
  Array.from(box.children).forEach(function(b){b.onclick=function(){if(request!==regionRequest||state!==prefs.state)return;var x=a[+b.dataset.i];setLoc({lat:x.latitude,lng:x.longitude,label:x.region_name+" "+state,suburb:x.region_name})}});
 }catch(e){if(request===regionRequest&&state===prefs.state)locationFeedback(box,"Popular areas could not load. Try again or search a suburb above.",loadRegions)}
 finally{clearTimeout(timeout);if(request===regionRequest)box.removeAttribute("aria-busy")}
}'''
    replace_function('async function loadRegions(){','function setLoc(',regions)
    search=r'''async function search(q){
 var query=String(q||"").trim(),request=++searchRequest,state=prefs.state,box=$("suggestions");
 if(searchAbort)searchAbort.abort();
 if(query.length<2){box.innerHTML="";box.removeAttribute("aria-busy");return}
 var controller=searchAbort=new AbortController(),timeout=setTimeout(function(){controller.abort()},12000);
 function isCurrent(){return request===searchRequest&&state===prefs.state&&query===$("locationSearch").value.trim()}
 box.setAttribute("aria-busy","true");locationFeedback(box,"Searching suburbs and postcodes…");
 try{
  var r=await fetch(api({api:"geocode",state:state,q:query}),{signal:controller.signal});if(!r.ok)throw Error("location search unavailable");
  var j=await r.json();if(!isCurrent())return;
  if(!j||j.error||!Array.isArray(j.candidates))throw Error("invalid search response");
  var a=j.candidates.filter(function(x){return x&&String(x.label||"").trim()&&(!x.state||x.state===state)&&x.lat!=null&&x.lng!=null&&Number.isFinite(+x.lat)&&Number.isFinite(+x.lng)&&Math.abs(+x.lat)<=90&&Math.abs(+x.lng)<=180});
  if(!a.length){locationFeedback(box,"No matching suburbs or postcodes in "+state+". Try another search or choose a popular area.");return}
  box.innerHTML=a.map(function(x,i){return '<button type="button" class="suggestion" data-i="'+i+'">'+esc(x.label)+'</button>'}).join("");
  Array.from(box.children).forEach(function(b){b.onclick=function(){if(isCurrent())setLoc(a[+b.dataset.i])}});
 }catch(e){if(isCurrent())locationFeedback(box,"Location search could not load. Check your connection and try again.",function(){search($("locationSearch").value)})}
 finally{clearTimeout(timeout);if(request===searchRequest)box.removeAttribute("aria-busy")}
}'''
    replace_function('async function search(q){','function find(',search)
    replace('loc=null;persist();syncFuel();loadRegions();render()',
            'loc=null;searchRequest++;clearTimeout(searchTimer);if(searchAbort)searchAbort.abort();$("locationSearch").value="";$("suggestions").innerHTML="";$("suggestions").removeAttribute("aria-busy");persist();syncFuel();loadRegions();load()')
    replace('clearTimeout(searchTimer);var q=this.value;searchTimer=setTimeout(function(){search(q)},220)',
            'clearTimeout(searchTimer);searchRequest++;if(searchAbort)searchAbort.abort();$("suggestions").innerHTML="";$("suggestions").removeAttribute("aria-busy");var q=this.value;searchTimer=setTimeout(function(){search(q)},220)')
    start=s.index('if(!list.length){',s.index('function renderOptions('));end=s.index('var reset=',start)
    replacement=r'''if(!list.length){
 var loading=priceStatus==="loading",failed=priceStatus==="error";
 var message=loading?"Loading nearby fuel prices…":failed?"Fuel prices could not be loaded. Try Refresh.":loc?"No stations found in this radius. Try a wider search.":"Choose an area to compare nearby stations.";
 var nextRadius=[5,10,20,30,50,100].find(function(value){return value>prefs.radius});
 var actions=loading?'':'<div class="empty-actions">'+(failed?'<button type="button" class="btn btn-go" id="optionsRetry">Try again</button>':loc&&nextRadius?'<button type="button" class="btn btn-go" id="optionsWiden">Search '+nextRadius+' km</button>':'')+'<button type="button" class="btn btn-soft" id="optionsChangeArea">'+(loc?'Change area':'Choose area')+'</button></div>';
 $("optionsList").innerHTML='<div class="empty" role="status">'+esc(message)+'</div>'+actions;
 if($("optionsRetry"))$("optionsRetry").onclick=load;
 if($("optionsChangeArea"))$("optionsChangeArea").onclick=openArea;
 if($("optionsWiden"))$("optionsWiden").onclick=function(){prefs.radius=nextRadius;persist();syncFuel();load();syncSub()};
 return}
'''
    s=s[:start]+replacement+s[end:]
    replace('<div style="font-size:7px;color:var(--muted);margin:13px 0 7px;font-weight:850">POPULAR AREAS</div>','<div class="region-heading">Popular areas</div>')
    css=r'''
/* FMN_RECOVERY_20261008: readable, actionable loading and failure states. */
#areaModal .location-feedback{width:100%;padding:12px;border:1px solid #d9e2db;border-radius:10px;background:#f4f7f4;color:#384b3d;font-size:14px;line-height:1.5;overflow-wrap:anywhere}
#areaModal .location-feedback .btn{min-height:44px;margin-top:10px;padding:10px 16px;font-size:14px}
#areaModal .region-heading{font-size:12px;line-height:1.5;color:#526057;margin:14px 0 8px;font-weight:800}
#optionsList .empty-actions{display:flex;flex-wrap:wrap;gap:10px;padding:0 14px 16px;background:#fff}
#optionsList .empty-actions .btn{flex:1 1 125px;min-height:48px;font-size:15px;line-height:1.3;padding:12px 16px}
#areaModal #regions{min-height:44px}
'''
    idx=s.index('</style>',s.index('<style id="fillmenow-public-readiness-2026-10-07">'))
    s=s[:idx]+css+s[idx:]
    assert re.findall(r'data:image/[^\s\"\)]+',s)==original_images,'Dash/embedded assets must remain byte-identical'
    assert re.search(r'const BACKEND=([^;]+);',s).group(0)==original_backend,'Backend endpoint must not change'
    p.write_text(s)
    sw=Path('web/sw.js');w=sw.read_text();w=re.sub(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v11-recovery-20261008';",w,count=1);sw.write_text(w)
print('Applied location-race and visible-recovery fixes to the existing web app; mascot and backend unchanged.')
