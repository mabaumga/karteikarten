const CACHE_NAME = 'karteikarten-v2';
const STATIC_ASSETS = [
    '/',
    '/lernen/offline/',
    '/js/db.js',
    '/js/sync.js',
    '/js/offline-learning.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js'
];

// Install: Cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate: Clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Network first, fallback to cache
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Skip API requests for sync (always network)
    if (url.pathname.startsWith('/api/sync/')) return;

    // For API karte/antwort - handle offline
    if (url.pathname.includes('/api/karte/') && url.pathname.includes('/antwort/')) {
        return; // Let the app handle offline via IndexedDB
    }

    // Handle page requests - Network first, fallback to cache
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // Cache successful page responses
                    if (response.ok) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, clone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Offline: Try cache, fallback to offline learning page
                    return caches.match(event.request)
                        .then(cached => {
                            if (cached) return cached;
                            // Redirect to offline learning page
                            return caches.match('/lernen/offline/') || caches.match('/');
                        });
                })
        );
        return;
    }

    // Handle static assets - Cache first, fallback to network
    if (STATIC_ASSETS.some(asset => url.pathname === asset || url.href === asset)) {
        event.respondWith(
            caches.match(event.request)
                .then(cached => {
                    if (cached) return cached;
                    return fetch(event.request).then(response => {
                        if (response.ok) {
                            const clone = response.clone();
                            caches.open(CACHE_NAME).then(cache => {
                                cache.put(event.request, clone);
                            });
                        }
                        return response;
                    });
                })
        );
        return;
    }

    // Default: Network first, fallback to cache
    event.respondWith(
        fetch(event.request)
            .then(response => {
                if (response.ok && event.request.url.startsWith(self.location.origin)) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, clone);
                    });
                }
                return response;
            })
            .catch(() => {
                return caches.match(event.request)
                    .then(cached => cached || new Response('Offline', { status: 503 }));
            })
    );
});

// Background Sync: Sync queued answers when online
self.addEventListener('sync', event => {
    if (event.tag === 'sync-antworten') {
        event.waitUntil(syncQueuedAnswers());
    }
});

async function syncQueuedAnswers() {
    // This will be handled by the main app via karteikartenSync
    // Just notify all clients to sync
    const clients = await self.clients.matchAll();
    for (const client of clients) {
        client.postMessage({ type: 'SYNC_NEEDED' });
    }
}

// Listen for messages from main app
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
