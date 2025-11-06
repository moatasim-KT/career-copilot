/**
 * Service Worker
 * 
 * Implements caching strategies for offline support and performance
 * - Network-first for API calls
 * - Cache-first for static assets
 * - Stale-while-revalidate for images
 * 
 * @file public/sw.js
 */

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `career-copilot-static-${CACHE_VERSION}`;
const API_CACHE = `career-copilot-api-${CACHE_VERSION}`;
const IMAGE_CACHE = `career-copilot-images-${CACHE_VERSION}`;

// Assets to precache on install
const PRECACHE_ASSETS = [
    '/',
    '/dashboard',
    '/jobs',
    '/applications',
    '/offline',
    '/manifest.json',
];

// Cache duration in seconds
const API_CACHE_DURATION = 5 * 60; // 5 minutes
const IMAGE_CACHE_DURATION = 24 * 60 * 60; // 24 hours

/**
 * Install Event
 * Precaches essential assets
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker');

    event.waitUntil(
        caches
            .open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Precaching assets');
                return cache.addAll(PRECACHE_ASSETS);
            })
            .then(() => {
                // Force the waiting service worker to become the active service worker
                return self.skipWaiting();
            })
    );
});

/**
 * Activate Event
 * Cleans up old caches
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker');

    event.waitUntil(
        caches
            .keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((cacheName) => {
                            // Delete old versions of caches
                            return (
                                cacheName.startsWith('career-copilot-') &&
                                cacheName !== STATIC_CACHE &&
                                cacheName !== API_CACHE &&
                                cacheName !== IMAGE_CACHE
                            );
                        })
                        .map((cacheName) => {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                // Take control of all pages immediately
                return self.clients.claim();
            })
    );
});

/**
 * Fetch Event
 * Implements caching strategies based on request type
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome extensions
    if (url.protocol === 'chrome-extension:') {
        return;
    }

    // API requests - Network first, fallback to cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request, API_CACHE));
        return;
    }

    // Images - Cache first, fallback to network
    if (request.destination === 'image') {
        event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE));
        return;
    }

    // Static assets - Stale while revalidate
    if (
        request.destination === 'style' ||
        request.destination === 'script' ||
        request.destination === 'font'
    ) {
        event.respondWith(staleWhileRevalidateStrategy(request, STATIC_CACHE));
        return;
    }

    // Default - Network first for pages
    event.respondWith(networkFirstStrategy(request, STATIC_CACHE));
});

/**
 * Network First Strategy
 * Try network first, fall back to cache, then offline page
 */
async function networkFirstStrategy(request, cacheName) {
    try {
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[SW] Network request failed, trying cache:', request.url);

        // Try to get from cache
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            const offlinePage = await caches.match('/offline');
            if (offlinePage) {
                return offlinePage;
            }
        }

        // Return a custom offline response
        return new Response(
            JSON.stringify({
                error: 'Offline',
                message: 'You are currently offline. Please check your internet connection.',
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' },
            }
        );
    }
}

/**
 * Cache First Strategy
 * Try cache first, fall back to network
 */
async function cacheFirstStrategy(request, cacheName) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Return cached response and update cache in background
        updateCacheInBackground(request, cacheName);
        return cachedResponse;
    }

    // Not in cache, fetch from network
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('[SW] Cache first strategy failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

/**
 * Stale While Revalidate Strategy
 * Return cache immediately, update cache in background
 */
async function staleWhileRevalidateStrategy(request, cacheName) {
    const cachedResponse = await caches.match(request);

    // Always fetch and update cache in background
    const fetchPromise = fetch(request)
        .then((networkResponse) => {
            if (networkResponse.ok) {
                const cache = caches.open(cacheName);
                cache.then((c) => c.put(request, networkResponse.clone()));
            }
            return networkResponse;
        })
        .catch((error) => {
            console.error('[SW] Stale while revalidate failed:', error);
            return cachedResponse || new Response('Offline', { status: 503 });
        });

    // Return cached response immediately if available
    return cachedResponse || fetchPromise;
}

/**
 * Update cache in background
 */
function updateCacheInBackground(request, cacheName) {
    fetch(request)
        .then((response) => {
            if (response.ok) {
                caches.open(cacheName).then((cache) => {
                    cache.put(request, response);
                });
            }
        })
        .catch((error) => {
            console.error('[SW] Background cache update failed:', error);
        });
}

/**
 * Background Sync Event
 * Retry failed requests when connection is restored
 */
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync event:', event.tag);

    if (event.tag === 'sync-applications') {
        event.waitUntil(syncApplications());
    }
});

/**
 * Sync applications when online
 */
async function syncApplications() {
    try {
        // Get pending sync data from IndexedDB or cache
        // This is a placeholder - implement based on your app's needs
        console.log('[SW] Syncing applications');

        // Example: POST queued data to API
        // const response = await fetch('/api/v1/applications/sync', {
        //   method: 'POST',
        //   body: JSON.stringify(pendingData),
        // });

        return Promise.resolve();
    } catch (error) {
        console.error('[SW] Sync failed:', error);
        return Promise.reject(error);
    }
}

/**
 * Push Notification Event
 * Handle push notifications (future feature)
 */
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();
    const title = data.title || 'Career Copilot';
    const options = {
        body: data.body || 'You have a new notification',
        icon: '/icon-192.png',
        badge: '/badge-72.png',
        tag: data.tag || 'notification',
        data: data.url || '/',
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

/**
 * Notification Click Event
 * Handle notification clicks
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const urlToOpen = event.notification.data || '/';

    event.waitUntil(
        self.clients
            .matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Check if there's already a window open
                for (const client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Open new window if none found
                if (self.clients.openWindow) {
                    return self.clients.openWindow(urlToOpen);
                }
            })
    );
});
