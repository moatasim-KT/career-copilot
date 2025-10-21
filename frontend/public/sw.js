/**
 * Service Worker for Career Co-Pilot
 * Provides offline functionality and caching
 */

const CACHE_NAME = 'career-copilot-v1';
const STATIC_CACHE = 'career-copilot-static-v1';
const API_CACHE = 'career-copilot-api-v1';

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/jobs',
  '/analytics',
  '/profile',
  '/_next/static/css/app.css',
  '/_next/static/chunks/main.js',
  '/_next/static/chunks/webpack.js',
  '/manifest.json'
];

// API endpoints to cache
const CACHEABLE_API_ENDPOINTS = [
  '/api/v1/jobs',
  '/api/v1/profile',
  '/api/v1/analytics',
  '/api/v1/recommendations'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static assets
      caches.open(STATIC_CACHE).then((cache) => {
        return cache.addAll(STATIC_ASSETS);
      }),
      // Cache API endpoints
      caches.open(API_CACHE).then((cache) => {
        // Pre-cache empty responses for offline fallback
        return Promise.all(
          CACHEABLE_API_ENDPOINTS.map(endpoint => {
            return cache.put(endpoint, new Response(JSON.stringify({
              offline: true,
              message: 'This data was cached for offline use',
              data: []
            }), {
              headers: { 'Content-Type': 'application/json' }
            }));
          })
        );
      })
    ]).then(() => {
      console.log('Service Worker installed successfully');
      // Skip waiting to activate immediately
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== STATIC_CACHE && 
              cacheName !== API_CACHE) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker activated');
      // Take control of all clients immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle API requests
  if (url.pathname.startsWith('/api/v1/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }
  
  // Handle static assets and pages
  if (url.origin === self.location.origin) {
    event.respondWith(handleStaticRequest(request));
    return;
  }
});

/**
 * Handle API requests with network-first strategy
 */
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // If successful, cache the response for cacheable endpoints
    if (networkResponse.ok && isCacheableEndpoint(url.pathname)) {
      const cache = await caches.open(API_CACHE);
      // Clone the response before caching
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network failed, trying cache for:', url.pathname);
    
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      // Add offline indicator to cached response
      const responseData = await cachedResponse.json();
      return new Response(JSON.stringify({
        ...responseData,
        offline: true,
        cached_at: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Return offline fallback
    return new Response(JSON.stringify({
      offline: true,
      error: 'No cached data available',
      message: 'Please check your internet connection'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * Handle static requests with cache-first strategy
 */
async function handleStaticRequest(request) {
  // Try cache first for static assets
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    // If not in cache, fetch from network
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/') || new Response('Offline', {
        status: 503,
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    throw error;
  }
}

/**
 * Check if an API endpoint should be cached
 */
function isCacheableEndpoint(pathname) {
  return CACHEABLE_API_ENDPOINTS.some(endpoint => 
    pathname.startsWith(endpoint)
  );
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'job-application-sync') {
    event.waitUntil(syncJobApplications());
  } else if (event.tag === 'profile-update-sync') {
    event.waitUntil(syncProfileUpdates());
  }
});

/**
 * Sync job applications when back online
 */
async function syncJobApplications() {
  try {
    // Get pending job applications from IndexedDB
    const pendingApplications = await getPendingApplications();
    
    for (const application of pendingApplications) {
      try {
        const response = await fetch('/api/v1/applications', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(application.data)
        });
        
        if (response.ok) {
          // Remove from pending queue
          await removePendingApplication(application.id);
          console.log('Synced job application:', application.id);
        }
      } catch (error) {
        console.error('Failed to sync application:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

/**
 * Sync profile updates when back online
 */
async function syncProfileUpdates() {
  try {
    // Get pending profile updates from IndexedDB
    const pendingUpdates = await getPendingProfileUpdates();
    
    for (const update of pendingUpdates) {
      try {
        const response = await fetch('/api/v1/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(update.data)
        });
        
        if (response.ok) {
          // Remove from pending queue
          await removePendingProfileUpdate(update.id);
          console.log('Synced profile update:', update.id);
        }
      } catch (error) {
        console.error('Failed to sync profile update:', error);
      }
    }
  } catch (error) {
    console.error('Profile sync failed:', error);
  }
}

// IndexedDB helpers for offline data storage
async function getPendingApplications() {
  try {
    const db = await openOfflineDB();
    const transaction = db.transaction(['pendingActions'], 'readonly');
    const store = transaction.objectStore('pendingActions');
    const index = store.index('type');
    const request = index.getAll('job-application');
    
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to get pending applications'));
    });
  } catch (error) {
    console.error('Failed to get pending applications:', error);
    return [];
  }
}

async function removePendingApplication(id) {
  try {
    const db = await openOfflineDB();
    const transaction = db.transaction(['pendingActions'], 'readwrite');
    const store = transaction.objectStore('pendingActions');
    const request = store.delete(id);
    
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to remove pending application'));
    });
  } catch (error) {
    console.error('Failed to remove pending application:', error);
  }
}

async function getPendingProfileUpdates() {
  try {
    const db = await openOfflineDB();
    const transaction = db.transaction(['pendingActions'], 'readonly');
    const store = transaction.objectStore('pendingActions');
    const index = store.index('type');
    const request = index.getAll('profile-update');
    
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to get pending profile updates'));
    });
  } catch (error) {
    console.error('Failed to get pending profile updates:', error);
    return [];
  }
}

async function removePendingProfileUpdate(id) {
  try {
    const db = await openOfflineDB();
    const transaction = db.transaction(['pendingActions'], 'readwrite');
    const store = transaction.objectStore('pendingActions');
    const request = store.delete(id);
    
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to remove pending profile update'));
    });
  } catch (error) {
    console.error('Failed to remove pending profile update:', error);
  }
}

// Open IndexedDB connection
async function openOfflineDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('career-copilot-offline', 1);
    
    request.onerror = () => reject(new Error('Failed to open IndexedDB'));
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('pendingActions')) {
        const actionStore = db.createObjectStore('pendingActions', { keyPath: 'id' });
        actionStore.createIndex('type', 'type', { unique: false });
        actionStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      
      if (!db.objectStoreNames.contains('cachedData')) {
        const dataStore = db.createObjectStore('cachedData', { keyPath: 'key' });
        dataStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
    };
  });
}

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
  const { type, data } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'CACHE_API_RESPONSE':
      cacheApiResponse(data.url, data.response);
      break;
      
    case 'CLEAR_CACHE':
      clearAllCaches();
      break;
      
    default:
      console.log('Unknown message type:', type);
  }
});

/**
 * Cache API response manually
 */
async function cacheApiResponse(url, responseData) {
  try {
    const cache = await caches.open(API_CACHE);
    const response = new Response(JSON.stringify(responseData), {
      headers: { 'Content-Type': 'application/json' }
    });
    await cache.put(url, response);
    console.log('Cached API response for:', url);
  } catch (error) {
    console.error('Failed to cache API response:', error);
  }
}

/**
 * Clear all caches
 */
async function clearAllCaches() {
  try {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('All caches cleared');
  } catch (error) {
    console.error('Failed to clear caches:', error);
  }
}