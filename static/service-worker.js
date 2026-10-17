// FreeTime service worker
// Scopo: rendere l'app installabile e resiliente a brevi interruzioni
// del server Flask locale. Il gioco resta comunque server-rendered:
// qui NON viene duplicata alcuna logica di gioco.

const CACHE_VERSION = 'freetime-cache-v1';
const APP_SHELL = [
  '/static/css/style.css?v=0.9b',
  '/static/js/app.js?v=0.9b',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon-maskable-512.png',
  '/static/manifest.json',
  '/offline.html'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_VERSION)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Non intercettare mai richieste che non sono GET (es. le mosse di
  // gioco sono POST): devono sempre andare dritte al server Flask.
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Navigazione tra pagine (HTML): prova la rete (dati sempre freschi,
  // perché il gioco è server-rendered), e solo se il server locale
  // non risponde momentaneamente mostra una pagina di attesa carina
  // invece dell'errore del browser.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/offline.html'))
    );
    return;
  }

  // Asset statici (CSS/JS/icone): cache-first per caricamento istantaneo,
  // con aggiornamento in background della cache.
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const network = fetch(request)
          .then((response) => {
            if (response && response.ok) {
              caches.open(CACHE_VERSION).then((cache) => cache.put(request, response.clone()));
            }
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
  }
});
