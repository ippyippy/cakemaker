/* FillMeNow location permission UI. No acquisition until a user clicks a location control. */
(function(root){'use strict';
const KEY='fmnLocationPromptDismissed';
let dialog=null,source='follow',noticeShown=false,everPrecise=false,attempted=false,startupTimer=null,permission=null;
let dismissed=false;try{dismissed=sessionStorage.getItem(KEY)==='1';}catch{}
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
function mount(host,onPrecise){
 if(!host||!('HTMLGeolocationElement' in root)||host.querySelector('.gps-permission-recovery'))return false;
 const section=el('section');section.className='gps-permission-recovery';
 const title=el('h3','Review this site’s location permission');
 const text=el('p','Tap the browser-controlled button below to allow precise location for this site. Your phone’s Location and precise app permission must also be enabled. This will not clear your saved settings.');
 const control=el('geolocation');control.setAttribute('accuracymode','precise');
 // No autolocate/watch and no synthetic clicks. The browser owns this permission button.
 const status=el('p');status.role='status';status.setAttribute('aria-live','polite');
 control.addEventListener('location',()=>{if(!section.isConnected)return;const result=root.FMNLiveCore?.assessPosition(control.position,Date.now());
  if(result?.kind==='precise'){status.textContent='Precise position received. Restarting the selected location action.';onPrecise(result.position);}
  else if(result?.kind==='coarse')status.textContent='Your device still reports ±'+Math.round(result.accuracy)+' m. Turn on precise location for the browser in phone Settings, then retry outdoors.';
  else if(control.error)status.textContent='Location could not be obtained. Check the phone and site permissions described below.';
  else status.textContent='A fresh precise GPS fix has not arrived. Retry with a clear view of the sky.';
 });
 control.addEventListener('promptaction',()=>{if(section.isConnected&&control.permissionStatus==='denied')status.textContent='Location is still blocked. You can review this permission again or use the phone settings steps below.';});
 section.append(title,text,control,status);host.prepend(section);return true;
}
function attempt(which){source=which==='search'?'search':'follow';attempted=true;clearTimeout(startupTimer);}
function ready(){everPrecise=true;noticeShown=true;clearTimeout(startupTimer);if(dialog?.open)dialog.close('resolved');}
function stopAction(){if(source==='search')root.FMNJourney?.cancelLocation();else root.FMNLiveLocation?.stop('Location is optional. Search an area manually or tap My location when ready.');}
function later(){dismissed=true;try{sessionStorage.setItem(KEY,'1');}catch{}stopAction();dialog?.close('later');}
function copy(reason,accuracy){
 if(reason==='coarse')return ['Turn on precise location','Your phone is sharing only an approximate position'+(Number.isFinite(accuracy)?' (±'+Math.round(accuracy)+' m)':'')+'. Allow Precise location for FillMeNow and your browser so the map can follow you.'];
 if(reason==='denied')return ['Allow location for FillMeNow','Location access is blocked. Use the permission button below. If it stays blocked, turn on Location and precise access in your phone or browser settings.'];
 if(reason==='unavailable'||reason==='timeout')return ['Check your location settings','A precise position is not available yet. Turn on phone Location, allow precise access, then retry. Poor reception can also cause this; a failed lookup does not prove Location is switched off.'];
 return ['Turn on location','Enable precise location to find fuel near you and follow your position while FillMeNow is open. You can also search a suburb without sharing your location.'];
}
function update(reason,accuracy){if(!dialog)return;const [title,message]=copy(reason,accuracy);dialog.querySelector('h2').textContent=title;dialog.querySelector('#locationPromptMessage').textContent=message;dialog.dataset.reason=reason;const button=dialog.querySelector('#locationPromptEnable');if(button)button.disabled=false;if(reason!=='prompt')dialog.querySelector('details').open=true;}
function resume(){
 if(!dialog?.open)return;const status=dialog.querySelector('#locationPromptStatus');status.textContent='Waiting for your permission and a fresh precise position…';
 // These existing actions retain their accuracy validation, cancellation and foreground-only rules.
 if(source==='search')root.FMNJourney?.requestLocation();else{root.FMNLiveLocation?.stop();root.FMNLiveLocation?.start();}
}
function open(reason='prompt',which='follow',accuracy,explicit=false){
 if(document.hidden)return false;
 if(dialog?.open){update(reason,accuracy);return true;}
 if(!explicit&&(dismissed||noticeShown||everPrecise))return false;
 // Never stack this automatically over another dialog/onboarding or interrupt a different task.
 if(document.querySelector('dialog[open],#fmnOnboard.open,#settingsDrawer.open'))return false;
 source=which==='search'?'search':'follow';noticeShown=true;
 const opener=document.activeElement,d=el('dialog');dialog=d;d.id='locationEnableDialog';d.className='journey-dialog location-enable-dialog';d.setAttribute('aria-labelledby','locationPromptTitle');d.setAttribute('aria-describedby','locationPromptMessage');
 d.innerHTML='<header><h2 id="locationPromptTitle"></h2></header><div class="journey-scroll"><p id="locationPromptMessage"></p><p class="location-prompt-safety">Set this up while parked. Nothing is enabled without your permission.</p><div id="locationPromptControl"></div><p id="locationPromptStatus" role="status" aria-live="polite"></p><details id="locationPromptSettings"><summary>Phone &amp; browser location settings</summary><p><strong>Android:</strong> Turn on Location in the phone’s quick settings. Then Settings → Apps → Chrome (or the browser hosting FillMeNow) → Permissions → Location → Allow while using the app, with <strong>Use precise location</strong> on.</p><p><strong>This website:</strong> Open this same FillMeNow address in your browser → site information → Permissions → Location → Allow. Choose Precise if offered.</p><p><strong>iPhone:</strong> Settings → Privacy &amp; Security → Location Services → your browser, allow access while using it and turn on Precise Location.</p><p>Return here and tap Retry after changing settings. FillMeNow cannot switch on the phone’s Location setting itself. Your saved vehicle and stations are not reset.</p></details></div><footer><button type="button" id="locationPromptLater">Not now</button><button type="button" id="locationPromptEnable">Enable location</button></footer>';
 d.querySelector('#locationPromptLater').onclick=later;
 d.querySelector('#locationPromptEnable').onclick=resume;
 const modern=mount(d.querySelector('#locationPromptControl'),()=>{if(d.isConnected&&d.open)resume();});
 if(modern){d.dataset.nativeControl='true';d.querySelector('#locationPromptEnable').textContent='Retry after changing settings';}
 d.addEventListener('cancel',e=>{e.preventDefault();e.stopPropagation();later();});
 d.addEventListener('keydown',e=>{if(e.key==='Escape')e.stopPropagation();});
 d.addEventListener('close',()=>{d.remove();if(dialog===d)dialog=null;if(opener?.isConnected)opener.focus({preventScroll:true});});
 document.body.append(d);update(reason,accuracy);d.showModal();return true;
}
function offer(reason,which='follow',accuracy){
 if(dialog?.open){update(reason,accuracy);return;}
 // Queue once after the existing location callback finishes; never start another GPS watch.
 if(dismissed||noticeShown||everPrecise||document.hidden)return;
 setTimeout(()=>open(reason,which,accuracy),0);
}
function startup(){
 if(attempted||dismissed||noticeShown||everPrecise||document.hidden)return;
 const first=document.getElementById('fmnOnboard'),area=document.getElementById('areaModal');
 if(!root.FMNLiveLocation||first?.classList.contains('open')||area?.classList.contains('open')||document.querySelector('dialog[open],#settingsDrawer.open')||document.body.dataset.page!=='explore'){startupTimer=setTimeout(startup,1200);return;}
 if(permission!=='granted')open(permission==='denied'?'denied':'prompt','follow');
}
async function checkPermission(){
 try{const p=await Promise.race([navigator.permissions.query({name:'geolocation'}),new Promise(resolve=>setTimeout(()=>resolve(null),1500))]);permission=p?.state||'unknown';}
 catch{permission='unknown';}
 if(!attempted&&!dismissed&&!noticeShown){clearTimeout(startupTimer);startupTimer=setTimeout(startup,900);}
}
root.FMNPermissionUI={mount,attempt,ready,offer,open:()=>open(permission==='denied'?'denied':'prompt','follow',undefined,true)};
root.addEventListener('pagehide',()=>clearTimeout(startupTimer));
document.addEventListener('visibilitychange',()=>{if(document.hidden)clearTimeout(startupTimer);else if(!attempted&&!dismissed&&!noticeShown)checkPermission();});
document.addEventListener('DOMContentLoaded',()=>{checkPermission();});
})(window);
