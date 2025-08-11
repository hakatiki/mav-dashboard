// Simple Service Worker for MÁV Monitor
const CACHE_NAME = 'mav-monitor-v3';
const urlsToCache = [
  './',
  'index.html',
  'script.js',
  'images/android-chrome-192x192.png',
  'images/favicon-32x32.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting();
});

self.addEventListener('fetch', event => {
  const reqUrl = new URL(event.request.url);
  // network-first for HTML/JS to ensure fresh data
  if (reqUrl.origin === self.location.origin && (reqUrl.pathname.endsWith('.html') || reqUrl.pathname.endsWith('.js'))) {
    event.respondWith(
      fetch(event.request).then(r => {
        const clone = r.clone();
        caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        return r;
      }).catch(() => caches.match(event.request))
    );
    return;
  }
  // cache-first for static assets
  if (reqUrl.origin === self.location.origin) {
    event.respondWith(caches.match(event.request).then(r => r || fetch(event.request)));
  }
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
}); 