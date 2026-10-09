/* Progressive enhancement: visible user-clicked Chrome permission recovery. No automatic tracking. */
(function(root){'use strict';
function mount(host,onPrecise){
 if(!host||!('HTMLGeolocationElement' in root)||host.querySelector('.gps-permission-recovery'))return false;
 const section=document.createElement('section');section.className='gps-permission-recovery';
 const title=document.createElement('h3');title.textContent='Review this site’s location permission';
 const text=document.createElement('p');text.textContent='Tap the browser-controlled button below to allow precise location for this site. Your phone’s Location and precise app permission must also be enabled. This will not clear your saved settings.';
 const control=document.createElement('geolocation');control.setAttribute('accuracymode','precise');
 // Intentionally no autolocate or watch: permission/data flow starts only from the user's click.
 const status=document.createElement('p');status.role='status';status.setAttribute('aria-live','polite');
 control.addEventListener('location',()=>{if(!section.isConnected)return;const result=root.FMNLiveCore?.assessPosition(control.position,Date.now());
  if(result?.kind==='precise'){status.textContent='Precise position received. Restarting the selected location action.';onPrecise(result.position);}
  else if(result?.kind==='coarse')status.textContent='Your device still reports ±'+Math.round(result.accuracy)+' m. Turn on precise location for the browser in phone Settings, then retry outdoors.';
  else if(control.error)status.textContent='Location could not be obtained. Check the phone and site permissions described below.';
  else status.textContent='A fresh precise GPS fix has not arrived. Retry with a clear view of the sky.';
 });
 section.append(title,text,control,status);host.prepend(section);return true;
}
root.FMNPermissionUI={mount};
})(window);
