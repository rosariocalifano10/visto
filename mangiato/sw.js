// Mangiato service worker: everything is cached so the app opens with no connection.
// Bump CACHE when you publish a new version; the update applies on the next launch.
// Mangiato shares its web address with Visto and Letto, so it only ever touches caches whose names start with "mangiato-".
const CACHE = 'mangiato-v1';
// The big restaurant list lives in its own cache so app updates don't download it again.
const DATA = 'mangiato-data';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-192.png', './icon-512.png'];

self.addEventListener('install', event => {
  // cache: 'reload' skips the browser's HTTP cache, so a new version never precaches an old copy
  event.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS.map(u => new Request(u, { cache: 'reload' }))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith('mangiato-') && k !== CACHE && k !== DATA).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(new URL(req.url).pathname.endsWith('/catalog.json') ? DATA : CACHE);
    const cached = await cache.match(req, { ignoreSearch: true });
    // Serve from cache right away and refresh it in the background, checked with the server rather than the HTTP cache.
    const network = fetch(req.url, { cache: 'no-cache', credentials: 'same-origin' })
      .then(res => { if (res && res.ok) cache.put(req, res.clone()); return res; })
      .catch(() => null);
    if (cached) {
      try { event.waitUntil(network); } catch (err) { /* already settled */ }
      return cached;
    }
    const res = await network;
    if (res) return res;
    if (req.mode === 'navigate') return (await cache.match('./index.html')) || Response.error();
    return Response.error();
  })());
});
