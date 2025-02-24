const CACHE_NAME = "my-gym-app-v1";
const URLS_TO_CACHE = [
  "/",
  "/static/css/my-styles.css",
  "/static/js/my-scripts.js",
  // Add more pages or assets to pre-cache
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
