/*
 * CampusBuddy service worker.
 *
 * A service worker is a small script the browser runs in the background, between
 * the app and the network. It is what makes the site installable and lets it open
 * even with no internet.
 *
 * Strategy:
 *   - App shell (the page, icons, manifest): saved on install, so the app opens offline.
 *   - Page loads: network first, so students always get the latest version;
 *     the saved copy is used only when offline.
 *   - API calls (/profiles, /events, /assistant ...): ALWAYS from the network, never cached.
 *     Attendee lists and chatbot answers must be live, and private data must not sit in a cache.
 *   - Fonts: cached after first use.
 *
 * To ship an update, change VERSION. Old caches are deleted when the new worker starts.
 */
const VERSION = 'campusbuddy-v1';
const SHELL_CACHE = `${VERSION}-shell`;
const FONT_CACHE = `${VERSION}-fonts`;
const SHELL_FILES = [
  '/',
  '/offline.html',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon.png',
];
const STATIC_PREFIXES = ['/icons/', '/manifest.webmanifest', '/offline.html'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;                      // uploads, check-ins, questions: network only
  const url = new URL(req.url);

  // Google Fonts: cache after first download
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(
      caches.open(FONT_CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        if (hit) return hit;
        const res = await fetch(req);
        if (res.ok || res.type === 'opaque') cache.put(req, res.clone());
        return res;
      })
    );
    return;
  }
  if (url.origin !== self.location.origin) return;

  // Opening the app: network first, saved copy when offline
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok && url.pathname === '/') {
            const copy = res.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put('/', copy));
          }
          return res;
        })
        .catch(async () => (await caches.match('/')) || caches.match('/offline.html'))
    );
    return;
  }

  // Icons and manifest: cache first
  if (STATIC_PREFIXES.some((p) => url.pathname.startsWith(p))) {
    event.respondWith(caches.match(req).then((hit) => hit || fetch(req)));
    return;
  }

  // Everything else is API data: always live. Offline -> a clear JSON error the page can handle.
  event.respondWith(
    fetch(req).catch(() => new Response(JSON.stringify({ detail: 'You are offline.' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    }))
  );
});
