/* =====================================================================
   Kfar-Link Service Worker
   ----------------------------------------------------------------------
   מאפשר לאפליקציה לעבוד גם ב-offline ומספק חוויה כמו אפליקציה אמיתית.
   ===================================================================== */

const CACHE_NAME = 'kfar-link-v2';
const ASSETS = [
  './',
  './landing.html',
  './onboarding.html',
  './dashboard.html',
  './bulk-buy.html',
  './share-board.html',
  './gig-jobs.html',
  './activities.html',
  './assets/styles.css',
  './assets/app.js',
  './assets/icon.svg',
  './assets/icon-192.png',
  './assets/icon-512.png',
  './manifest.json'
];

// התקנה — מאחסנים את כל הנכסים העיקריים ב-cache
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// הפעלה — ניקוי caches ישנים
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// אחזור — Cache First עם רענון ברקע (stale-while-revalidate)
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request).then((response) => {
        if (response && response.status === 200 && response.type === 'basic') {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        }
        return response;
      }).catch(() => cached);
      return cached || fetchProm