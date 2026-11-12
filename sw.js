/* Minimal shell cache for offline UI (API/WS still need local bridge). */
const CACHE = 'vortexa-shell-v3510';
const ASSETS = ['/', '/index.html', '/manifest.webmanifest', '/vendor/three/three.min.js'];
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).catch(() => caches.match('/index.html')))
  );
});
