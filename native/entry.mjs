import { Capacitor, registerPlugin } from '@capacitor/core';
import { Geolocation } from '@capacitor/geolocation';
import { App } from '@capacitor/app';
import { createLocationFacade } from './location-facade.mjs';
const settings=registerPlugin('FMNSettings');
let foreground=true,source='follow',shown=false,preciseSeen=false;
const facade=createLocationFacade(Geolocation,settings,()=>foreground&&!document.hidden);
window.FMNNativeLocation={...facade,settings};
document.documentElement.dataset.locationSource='android-native';
function stopAction(){window.FMNLiveLocation?.stop('Location stopped. Tap My location to resume.');window.FMNJourney?.cancelLocation();void facade.stop();}
function resume(){if(source==='search')window.FMNJourney?.requestLocation();else{window.FMNLiveLocation?.stop();window.FMNLiveLocation?.start();}}
function button(text,fn){const b=document.createElement('button');b.type='button';b.textContent=text;b.onclick=fn;return b;}
function help(reason='settings'){
 if(document.hidden||document.getElementById('nativeLocationDialog'))return;
 const d=document.createElement('dialog');d.id='nativeLocationDialog';d.className='journey-dialog';d.setAttribute('aria-labelledby','nativeLocationTitle');
 d.innerHTML='<header><h2 id="nativeLocationTitle">FillMeNow location</h2></header><div class="journey-scroll"><p id="nativeLocationMessage"></p><p>Location in this installed app comes directly from Android. Chrome and website permissions are not used.</p><p>Choose Precise and While using the app in Android’s permission request. You can also search manually without sharing location.</p><div class="native-location-actions"></div><p id="nativeLocationDetail" role="status"></p><p>Set this up while parked. Following stops when the app is hidden. Permission does not guarantee GPS reception.</p></div><footer></footer>';
 const msg=d.querySelector('#nativeLocationMessage');msg.textContent=reason==='denied'?'Precise location has not been granted to FillMeNow.':reason==='coarse'?'Android has supplied an approximate reading. Check precise permission and try outdoors.':'Allow precise location and turn on the phone’s Location setting.';
 const detail=d.querySelector('#nativeLocationDetail');
 const run=async(action)=>{try{await action();detail.textContent='Return to FillMeNow, then tap Try location.';}catch{detail.textContent='Location settings were not changed. Manual search remains available.';}};
 d.querySelector('.native-location-actions').append(button('FillMeNow app permissions',()=>run(()=>settings.openAppSettings())),button('Turn on phone Location',()=>run(()=>settings.ensureEnabled())));
 d.querySelector('footer').append(button('‹ Back',()=>{stopAction();d.close();}),button('Try location',()=>{d.close();resume();}));
 d.addEventListener('cancel',()=>stopAction());d.addEventListener('close',()=>d.remove());document.body.append(d);d.showModal();
 settings.status().then(s=>{if(d.isConnected)detail.textContent=(s.fine?'Precise permission allowed.':s.coarse?'Only approximate permission allowed.':'Location permission not granted.')+' '+(s.enabled?'Phone Location is on.':'Phone Location is off.');}).catch(()=>{});
}
window.FMNPermissionUI={
 attempt:s=>{source=s==='search'?'search':'follow';},ready:()=>{preciseSeen=true;document.getElementById('nativeLocationDialog')?.close();},
 offer:(reason,s)=>{source=s==='search'?'search':'follow';if(shown||preciseSeen)return;shown=true;setTimeout(()=>help(reason),0);},
 open:()=>help(),mount:()=>false
};
function hidden(){foreground=false;stopAction();}
document.addEventListener('visibilitychange',()=>{if(document.hidden)hidden();else foreground=true;});
window.addEventListener('pagehide',hidden);
App.addListener('appStateChange',s=>{foreground=s.isActive;if(!s.isActive)stopAction();});
// External pages never receive the native bridge. Only explicit user navigation uses Android VIEW.
window.open=(url)=>{try{const u=new URL(url,location.href);if(u.origin===location.origin)u.host='fillmenow-au.vercel.app';if(['https:','tel:'].includes(u.protocol))void settings.openExternal({url:u.href}).catch(()=>{});}catch{}return null;};
document.addEventListener('DOMContentLoaded',()=>{
 const style=document.createElement('style');style.textContent='.native-location-actions{display:grid;gap:10px}.native-location-actions button,#nativeLocationSettings{min-height:48px;padding:12px;border:1px solid #b8cbbd;border-radius:12px;background:#fff;color:#163b26;font-size:16px}#nativeBuildNote{margin:16px 0;padding:14px;border:1px solid #c9d7cc;border-radius:12px;font-size:15px;line-height:1.45}';document.head.append(style);
 const more=document.querySelector('#page-more');if(more){const note=document.createElement('section');note.id='nativeBuildNote';note.textContent='Android 1.2.0 GPS test · Direct Android location. Browser and installed-app settings are stored separately; your old browser data has not been deleted. Check Vehicle Settings and Saved. Native push alerts are not enabled in this test build.';const b=button('Location settings',()=>help());b.id='nativeLocationSettings';note.append(document.createElement('br'),b);more.append(note);}
 const install=document.getElementById('installBtn');if(install){install.textContent='Android app installed';install.disabled=true;}
});
App.addListener('backButton',()=>{
 const d=document.querySelector('dialog[open]');if(d){d.dispatchEvent(new Event('cancel'));d.close();return;}
 for(const [shell,b] of [['#settingsDrawer.open','#drawerBack'],['#stationModal.open','#stationClose'],['#areaModal.open','#areaClose']]){if(document.querySelector(shell)){document.querySelector(b)?.click();return;}}
 if(document.body.dataset.page==='options'){document.getElementById('optionsBack')?.click();return;}
 if(document.body.dataset.page!=='explore'){document.querySelector('.nav[data-page="explore"]')?.click();return;}
 stopAction();void App.exitApp();
});
if(!Capacitor.isNativePlatform())throw new Error('This bundle requires the installed Android app.');
