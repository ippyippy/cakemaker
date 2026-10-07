"""Repair the existing Dash handle: complete rounded tile and saved free positioning."""
from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text();marker='FMN_MOVABLE_DASH_20261008'
if marker in s:
    print('Movable Dash already applied.');raise SystemExit(0)
original=s
assets=re.findall(r'data:image/[^\s\"\)]+',s)
def replace(old,new):
    global s
    assert s.count(old)==1,f'Expected one source anchor: {old[:100]}'
    s=s.replace(old,new,1)
# The square surface owns the corners. Original artwork stays contained inside it.
replace('body #page-explore .mobile-sheet.is-collapsed{width:96px!important;height:88px!important;max-height:none!important;right:8px!important;left:auto!important;bottom:var(--fmn-nav)!important;background:transparent!important;box-shadow:none!important;border:0!important}', '''/* FMN_MOVABLE_DASH_20261008 */
 body #page-explore .mobile-sheet.is-collapsed{width:80px!important;height:80px!important;max-height:none!important;right:auto!important;left:var(--fmn-dash-x,calc(100% - 92px))!important;top:var(--fmn-dash-y,calc(100dvh - var(--fmn-nav) - 92px))!important;bottom:auto!important;background:transparent!important;box-shadow:none!important;border:0!important;transform:none!important;transition:none!important;overflow:visible!important}
 body #page-explore .mobile-sheet.is-collapsed .sheet-peek{inset:0!important;width:80px!important;height:80px!important;padding:0!important;background:#fff!important;border:1px solid #d5dfd7!important;border-radius:18px!important;box-shadow:0 3px 14px #10201530!important;overflow:hidden!important;cursor:grab!important;touch-action:none!important;user-select:none!important;-webkit-user-select:none!important;-webkit-touch-callout:none!important;transition:none!important}
 body #page-explore .mobile-sheet.is-collapsed .sheet-peek:after{inset:3px!important;width:auto!important;height:auto!important;background-size:contain!important;background-position:center!important;background-repeat:no-repeat!important;border-radius:14px!important;filter:none!important;transform:none!important;transition:none!important;opacity:1!important}
 body #page-explore .mobile-sheet.is-collapsed.is-dragging .sheet-peek{cursor:grabbing!important;box-shadow:0 5px 20px #10201545!important}
 body #page-explore .mobile-sheet.is-collapsed .sheet-peek:focus-visible{outline:3px solid #087532!important;outline-offset:3px!important}''')
a=s.index('$("sheetHandle").onclick=function(){if(this.dataset.skipClick')
b=s.index(';installSheetGestures();',a)+len(';installSheetGestures();')
s=s[:a]+'installSheetGestures();'+s[b:]
a=s.index('function setSheetCollapsed(collapsed){');b=s.index('\nwindow.FD=',a)
s=s[:a]+r'''// FMN_MOVABLE_DASH_20261008: one gesture owner; drag moves, tap opens.
var dashPosition=read("fmnDashPosition",null),dashLayoutFrame=0;
if(!dashPosition||dashPosition.version!==1||!Number.isFinite(dashPosition.x)||!Number.isFinite(dashPosition.y)||dashPosition.x<0||dashPosition.x>1||dashPosition.y<0||dashPosition.y>1)dashPosition=null;
function dashBounds(){
 var host=$("exploreMap"),sheet=$("mobileSheet"),viewport=window.visualViewport;
 if(!host||!sheet||!window.matchMedia("(max-width:1024px)").matches||!$("page-explore").classList.contains("active"))return null;
 var r=host.getBoundingClientRect();if(r.width<80||r.height<80)return null;
 var left=viewport?viewport.offsetLeft:0,top=viewport?viewport.offsetTop:0;
 var right=left+(viewport?viewport.width:innerWidth),bottom=top+(viewport?viewport.height:innerHeight);
 var nav=document.querySelector(".bottom-nav"),n=nav?nav.getBoundingClientRect():null;
 if(n&&n.height>0&&n.top>top)bottom=Math.min(bottom,n.top);
 var minX=Math.max(r.left,left)+12,minY=Math.max(r.top,top)+12;
 return {minX:minX,minY:minY,maxX:Math.max(minX,Math.min(r.right,right)-92),maxY:Math.max(minY,Math.min(r.bottom,bottom)-92)};
}
function placeDash(x,y,remember){
 var bounds=dashBounds(),sheet=$("mobileSheet");if(!bounds||!sheet)return;
 x=Math.max(bounds.minX,Math.min(bounds.maxX,x));y=Math.max(bounds.minY,Math.min(bounds.maxY,y));
 sheet.style.setProperty("--fmn-dash-x",Math.round(x)+"px");sheet.style.setProperty("--fmn-dash-y",Math.round(y)+"px");
 if(remember){
  dashPosition={version:1,x:bounds.maxX>bounds.minX?(x-bounds.minX)/(bounds.maxX-bounds.minX):0,y:bounds.maxY>bounds.minY?(y-bounds.minY)/(bounds.maxY-bounds.minY):0};
  try{localStorage.setItem("fmnDashPosition",JSON.stringify(dashPosition))}catch(e){}
 }
}
function positionCollapsedDash(){
 var sheet=$("mobileSheet"),bounds=dashBounds();if(!sheet||!bounds||!sheet.classList.contains("is-collapsed")||sheet.classList.contains("is-dragging"))return;
 var pos=dashPosition||{x:1,y:1};placeDash(bounds.minX+pos.x*(bounds.maxX-bounds.minX),bounds.minY+pos.y*(bounds.maxY-bounds.minY),false);
}
function queueDashLayout(){cancelAnimationFrame(dashLayoutFrame);dashLayoutFrame=requestAnimationFrame(positionCollapsedDash)}
function setSheetCollapsed(collapsed){
 var sheet=$("mobileSheet");if(!sheet)return;
 sheet.style.setProperty("--sheet-drag-y","0px");sheet.classList.toggle("is-collapsed",!!collapsed);positionCollapsedDash();
 setTimeout(function(){try{if(map){map.resize();renderMapMarkers()}positionCollapsedDash()}catch(e){}},280);
 var handle=$("sheetHandle");if(handle)handle.setAttribute("aria-expanded",collapsed?"false":"true");
 var peek=$("sheetPeek");if(peek){peek.tabIndex=collapsed?0:-1;peek.setAttribute("aria-expanded",collapsed?"false":"true")}
}
function installSheetGestures(){
 var sheet=$("mobileSheet"),handle=$("sheetHandle"),main=$("sheetMain"),peek=$("sheetPeek");if(!sheet||!peek||sheet.dataset.gestureReady==="1")return;
 sheet.dataset.gestureReady="1";var active=null,suppressClick=false,suppressTimer=0;
 peek.setAttribute("aria-label","Dash. Tap to open Best Stop. Drag to move.");
 peek.setAttribute("aria-description","Arrow keys move Dash. Home restores the bottom-right position.");
 function suppress(){suppressClick=true;clearTimeout(suppressTimer);suppressTimer=setTimeout(function(){suppressClick=false},450)}
 sheet.addEventListener("click",function(e){if(suppressClick&&e.detail!==0){suppressClick=false;e.preventDefault();e.stopImmediatePropagation()}},true);
 function start(e){
  if(active||e.isPrimary===false||(e.pointerType==="mouse"&&e.button!==0)||!window.matchMedia("(max-width:1024px)").matches)return;
  var collapsed=sheet.classList.contains("is-collapsed"),target=e.target;
  if(collapsed&&!peek.contains(target))return;
  if(!collapsed&&target.closest("button,a,input,select,textarea"))return;
  if(!collapsed&&e.currentTarget===main&&main.scrollHeight>main.clientHeight+2)return;
  suppressClick=false;clearTimeout(suppressTimer);
  var rect=sheet.getBoundingClientRect();active={id:e.pointerId,mode:collapsed?"move":"sheet",x:e.clientX,y:e.clientY,lastX:e.clientX,lastY:e.clientY,left:rect.left,top:rect.top,moved:false,capture:e.currentTarget};
  if(collapsed){e.preventDefault();e.stopPropagation();try{peek.setPointerCapture(e.pointerId)}catch(err){}}
 }
 function move(e){
  if(!active||e.pointerId!==active.id)return;
  active.lastX=e.clientX;active.lastY=e.clientY;var dx=e.clientX-active.x,dy=e.clientY-active.y;
  if(!active.moved&&Math.hypot(dx,dy)<8)return;
  active.moved=true;sheet.classList.add("is-dragging");
  if(active.mode==="move")placeDash(active.left+dx,active.top+dy,false);
  else sheet.style.setProperty("--sheet-drag-y",Math.max(0,Math.min(170,dy))+"px");
  if(e.cancelable)e.preventDefault();
 }
 function end(e,cancelled){
  if(!active||(e&&e.pointerId!==undefined&&e.pointerId!==active.id))return;
  var done=active;active=null;sheet.classList.remove("is-dragging");sheet.style.setProperty("--sheet-drag-y","0px");
  if(done.moved)suppress();
  if(done.mode==="move"){
   if(!cancelled&&done.moved)placeDash(done.left+done.lastX-done.x,done.top+done.lastY-done.y,true);
   else positionCollapsedDash();
  }else if(!cancelled&&done.moved&&done.lastY-done.y>42)setSheetCollapsed(true);
  try{if(done.capture.hasPointerCapture(done.id))done.capture.releasePointerCapture(done.id)}catch(err){}
 }
 [handle,main,peek].filter(Boolean).forEach(function(el){el.addEventListener("pointerdown",start)});
 window.addEventListener("pointermove",move,{passive:false});window.addEventListener("pointerup",function(e){end(e,false)});
 window.addEventListener("pointercancel",function(e){end(e,true)});peek.addEventListener("lostpointercapture",function(e){end(e,true)});
 window.addEventListener("blur",function(){end(null,true)});
 document.addEventListener("visibilitychange",function(){if(document.hidden)end(null,true)});
 peek.addEventListener("contextmenu",function(e){e.preventDefault()});peek.addEventListener("dragstart",function(e){e.preventDefault()});
 peek.onclick=function(){setSheetCollapsed(false)};
 peek.onkeydown=function(e){
  if(e.key==="Enter"||e.key===" "){e.preventDefault();setSheetCollapsed(false);return}
  if(e.key==="Home"){e.preventDefault();dashPosition=null;try{localStorage.removeItem("fmnDashPosition")}catch(err){}positionCollapsedDash();return}
  var directions={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]},d=directions[e.key];
  if(d){e.preventDefault();var r=sheet.getBoundingClientRect(),step=e.shiftKey?32:16;placeDash(r.left+d[0]*step,r.top+d[1]*step,true)}
 };
 if(handle){handle.onclick=function(){setSheetCollapsed(!sheet.classList.contains("is-collapsed"))};handle.onkeydown=function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();setSheetCollapsed(!sheet.classList.contains("is-collapsed"))}}}
 function resized(){end(null,true);queueDashLayout()}
 window.addEventListener("resize",resized);window.addEventListener("orientationchange",resized);
 if(window.visualViewport){window.visualViewport.addEventListener("resize",resized);window.visualViewport.addEventListener("scroll",queueDashLayout)}
}
''' +s[b:]
replace('if(p==="explore")setTimeout(renderMap,70);','if(p==="explore")setTimeout(function(){renderMap();positionCollapsedDash()},70);')
replace('["fdPrefs","fdLoc","fdSaved","fmnOnboarded"].forEach','["fdPrefs","fdLoc","fdSaved","fmnOnboarded","fmnDashPosition"].forEach')
assert re.findall(r'data:image/[^\s\"\)]+',s)==assets,'Original embedded images must stay byte-identical'
assert re.search(r'const BACKEND=([^;]+);',s).group(0)==re.search(r'const BACKEND=([^;]+);',original).group(0)
p.write_text(s)
sw=Path('web/sw.js');w=sw.read_text();w,n=re.subn(r"const CACHE = '[^']+';","const CACHE = 'fillmenow-web-v14-movable-dash-20261008';",w,count=1);assert n==1;sw.write_text(w)
print('Applied rounded, freely draggable Dash. Original artwork and backend preserved.')
