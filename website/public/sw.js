// Simple Service Worker for MÁV Monitor
const CACHE_NAME = 'mav-monitor-v2';
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
  // Don't cache cross-origin (e.g., GCS map/data)
  if (reqUrl.origin !== self.location.origin) {
    return; // default network behaviour
  }
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
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