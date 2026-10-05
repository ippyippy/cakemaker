const C='fillmenow-web-v2';
const HOME='/';
const SHELL=[HOME,'/manifest.webmanifest','/icon.svg'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('push',e=>{let d={};try{d=e.data?e.data.json():{}}catch{d={body:e.data?e.data.text():'Fuel prices updated'}};const title=d.title||'FillMeNow';const o={body:d.body||'Your best-value fuel update is ready.',icon:'/icon.svg',badge:'/icon.svg',tag:d.tag||'fueldrop',renotify:true,data:d.data||{},actions:[{action:'open',title:'Open FillMeNow'}]};e.waitUntil(self.registration.showNotification(title,o))});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(cs=>{for(const c of cs){if('focus' in c&&new URL(c.url).origin===self.location.origin)return c.focus()}return clients.openWindow(HOME)}))});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const u=new URL(e.request.url);if(u.origin!==self.location.origin)return;e.respondWith(fetch(e.request).then(r=>{if(r.ok)caches.open(C).then(c=>c.put(e.request,r.clone()));return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match(HOME))))});
