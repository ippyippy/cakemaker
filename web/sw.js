const CACHE = 'fillmenow-web-v19-journey-20261009';
const SHELL = ["/journey.js", "/journey.css", "/nearby-core.js", "/nearby-ui.js", "/nearby.css", "/data/station-information.json", "/startup-support.css", "/support-chat.js", "/interaction-polish.css", "/", "/manifest.webmanifest", "/icon.svg", "/icons/icon-192.png", "/icons/icon-512.png", "/assets/maplibre.js", "/assets/maplibre.css", "/privacy", "/terms", "/assets/brands/bp.svg", "/assets/brands/shell.svg", "/assets/brands/caltex.png", "/assets/brands/ampol.svg", "/assets/brands/united.png", "/assets/brands/metro.png", "/assets/brands/liberty.svg", "/assets/brands/puma.svg", "/assets/brands/reddy.png", "/assets/brands/seven.svg"];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => /^(fillmenow-|fueldrop-)/.test(key) && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; }
  catch { data = {body: event.data ? event.data.text() : 'Fuel prices updated'}; }
  event.waitUntil(self.registration.showNotification(data.title || 'FillMeNow', {
    body: data.body || 'Your best-value fuel update is ready.',
    icon: '/icons/icon-192.png', badge: '/icons/icon-192.png',
    tag: data.tag || 'fillmenow', renotify: true, data: data.data || {},
    actions: [{action: 'open', title: 'Open FillMeNow'}]
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.matchAll({type: 'window', includeUncontrolled: true}).then(windows => {
    const existing = windows.find(window => new URL(window.url).origin === self.location.origin && 'focus' in window);
    return existing ? existing.focus() : clients.openWindow('/');
  }));
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok) {
      const copy = response.clone();
      event.waitUntil(caches.open(CACHE).then(cache => cache.put(event.request, copy)));
    }
    return response;
  }).catch(async () => {
    const cached = await caches.match(event.request);
    if (cached) return cached;
    if (event.request.mode === 'navigate') return await caches.match('/') || Response.error();
    return Response.error();
  }));
});
