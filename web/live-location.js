/* Foreground-only, user-started location following. No history or background tracking. */
(function(root,factory){'use strict';const core=factory();if(typeof module==='object'&&module.exports){module.exports=core;return;}root.FMNLiveCore=core;
let app,map,watch=null,lastPoint=null,lastTimestamp=0,generation=0,deadline=null,wanted=false,locked=false,refreshAt=0,refreshPoint=null;
const $=id=>document.getElementById(id);
function say(text){const node=$('followStatus');if(node){node.textContent=text;node.hidden=!text;}}
function buttons(){const c=$('recenterBtn'),t=$('followToggle');if(c){c.setAttribute('aria-label',locked?'Centre on my live location':'Find and centre my location');c.classList.toggle('following',locked);c.title='Find and centre on your actual GPS location';}if(t){t.textContent=locked?'Stop following':wanted?'Resume follow':'Follow me';t.setAttribute('aria-pressed',String(locked));}}
function release(){generation++;clearTimeout(deadline);deadline=null;if(watch!==null){navigator.geolocation?.clearWatch(watch);watch=null;}}
function stop(message){release();wanted=false;locked=false;buttons();if(message!==undefined)say(message);}
function pause(){if(!wanted)return;locked=false;buttons();say('Map browsing · tap My location to resume following.');}
function fail(code){stop();const messages={1:'Location blocked. Allow this app in your browser and phone settings.',2:'GPS unavailable. Turn on phone Location, or use Search.',3:'GPS timed out. Tap My location to try again.'};say(messages[code]||messages[2]);}
function receive(position,id){if(id!==generation||!wanted||document.hidden)return;const p=core.validPosition(position,Date.now(),lastTimestamp);if(!p){say('Waiting for a fresh, usable GPS position…');return;}lastTimestamp=p.timestamp;lastPoint=p;clearTimeout(deadline);deadline=null;
 const state=app.locationState(p);if(!state){stop('GPS is near a state boundary or outside supported coverage. Use Search to confirm the state.');return;}
 const now=Date.now(),reload=!refreshPoint||now-refreshAt>180000||(now-refreshAt>=20000&&core.distance(refreshPoint,p)>=.5);
 if(reload){refreshAt=now;refreshPoint=p;}
 app.applyLiveLocation(p,state,{reload,follow:locked});buttons();say(p.accuracy>250?'Approximate GPS (±'+Math.round(p.accuracy)+' m). Check your position.':locked?'Following your live location':'Location updating · map browsing');
}
function start(){if(!app)return;app.prepareLiveMap();map=app.getMap();if(!root.isSecureContext||!navigator.geolocation?.watchPosition){fail(2);return;}const policy=document.permissionsPolicy||document.featurePolicy;if(policy?.allowsFeature&&!policy.allowsFeature('geolocation')){fail(1);return;}
 if(watch!==null&&wanted){locked=true;buttons();if(lastPoint)app.centreLive(lastPoint);say('Following your live location');return;}
 release();wanted=true;locked=true;const id=generation;buttons();say('Finding your location… allow the location request.');
 deadline=setTimeout(()=>{if(id===generation)fail(3);},15000);
 try{watch=navigator.geolocation.watchPosition(p=>receive(p,id),e=>{if(id===generation)fail(e?.code);},{enableHighAccuracy:true,timeout:10000,maximumAge:5000});if(id!==generation&&watch!==null){navigator.geolocation.clearWatch(watch);watch=null;}}catch{fail(2);}
}
function bindMap(){const m=app.getMap();if(!m||m===map&&m.__fmnFollowBound)return;map=m;map.__fmnFollowBound=true;map.on('dragstart',e=>{if(e.originalEvent)pause();});map.on('rotatestart',e=>{if(e.originalEvent)pause();});}
function init(){app=root.FMNJourneyApp;if(!app)return;const c=$('recenterBtn'),holder=c?.parentElement;if(!holder)return;
 c.innerHTML='<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="12" r="6" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="2.5" fill="currentColor"/><path d="M12 1v4M12 19v4M1 12h4M19 12h4" stroke="currentColor" stroke-width="2"/></svg><span>My location</span>';c.onclick=start;
 const t=document.createElement('button');t.id='followToggle';t.type='button';t.onclick=()=>{if(locked)stop('Following stopped.');else start();};c.after(t);
 const s=document.createElement('p');s.id='followStatus';s.role='status';s.hidden=true;holder.after(s);buttons();bindMap();
 document.addEventListener('fmn:map-ready',bindMap);document.addEventListener('fmn:manual-area',()=>stop('Following stopped for your selected area.'));
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&wanted){release();wanted=false;locked=false;buttons();say('Following paused while the app was hidden. Tap Follow me to resume.');}});
 root.addEventListener('pagehide',()=>stop());
}
root.FMNLiveLocation={start,stop,pause,getState:()=>({watching:watch!==null,wanted,locked})};
document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));
})(typeof window!=='undefined'?window:globalThis,function(){'use strict';
function distance(a,b){const r=Math.PI/180,dl=(b.lat-a.lat)*r,dn=(b.lng-a.lng)*r,q=Math.sin(dl/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(dn/2)**2;return 6371*2*Math.atan2(Math.sqrt(q),Math.sqrt(Math.max(0,1-q)));}
function validPosition(p,now,last=0){const c=p?.coords,t=Number(p?.timestamp);if(!c||!Number.isFinite(c.latitude)||!Number.isFinite(c.longitude)||Math.abs(c.latitude)>90||Math.abs(c.longitude)>180||!Number.isFinite(c.accuracy)||c.accuracy<0||c.accuracy>5000||!Number.isFinite(t)||t<last||now-t>60000||t-now>5000)return null;return {lat:c.latitude,lng:c.longitude,accuracy:c.accuracy,timestamp:t};}
function bearing(a,b){const r=Math.PI/180,dl=(b.lng-a.lng)*r;return Math.atan2(Math.sin(dl)*Math.cos(b.lat*r),Math.cos(a.lat*r)*Math.sin(b.lat*r)-Math.sin(a.lat*r)*Math.cos(b.lat*r)*Math.cos(dl));}
function toward(row,origin,destination){if(!origin||!destination||destination.manual||![origin.lat,origin.lng,destination.lat,destination.lng,row.latitude,row.longitude].every(v=>v!=null&&Number.isFinite(+v)))return null;const station={lat:+row.latitude,lng:+row.longitude},trip=distance(origin,destination),d=distance(origin,station);if(trip<.25)return false;let angle=bearing(origin,station)-bearing(origin,destination);angle=Math.atan2(Math.sin(angle),Math.cos(angle));return Math.abs(angle)<=Math.PI*5/12&&d*Math.cos(angle)<=trip&&distance(station,destination)<trip;}
return Object.freeze({distance,validPosition,toward});
});
