/**
 * Service Worker registration and management utilities
 */

interface ServiceWorkerMessage {
  type: string;
  data?: any;
}

class ServiceWorkerManager {
  private registration: ServiceWorkerRegistration | null = null;
  private isSupported: boolean = false;

  constructor() {
    this.isSupported = typeof window !== 'undefined' && 'serviceWorker' in navigator;
  }

  /**
   * Register the service worker
   */
  async register(): Promise<ServiceWorkerRegistration | null> {
    if (!this.isSupported) {
      console.warn('Service Workers are not supported in this browser');
      return null;
    }

    try {
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      console.log('Service Worker registered successfully:', this.registration);

      // Handle service worker updates
      this.registration.addEventListener('updatefound', () => {
        const newWorker = this.registration!.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is available
              this.notifyUpdate();
            }
          });
        }
      });

      // Listen for messages from service worker
      navigator.serviceWorker.addEventListener('message', this.handleMessage.bind(this));

      return this.registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return null;
    }
  }

  /**
   * Unregister the service worker
   */
  async unregister(): Promise<boolean> {
    if (!this.registration) {
      return false;
    }

    try {
      const result = await this.registration.unregister();
      console.log('Service Worker unregistered:', result);
      return result;
    } catch (error) {
      console.error('Service Worker unregistration failed:', error);
      return false;
    }
  }

  /**
   * Update the service worker
   */
  async update(): Promise<void> {
    if (!this.registration) {
      return;
    }

    try {
      await this.registration.update();
      console.log('Service Worker update check completed');
    } catch (error) {
      console.error('Service Worker update failed:', error);
    }
  }

  /**
   * Skip waiting and activate new service worker
   */
  skipWaiting(): void {
    if (this.registration?.waiting) {
      this.sendMessage({ type: 'SKIP_WAITING' });
    }
  }

  /**
   * Send message to service worker
   */
  sendMessage(message: ServiceWorkerMessage): void {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage(message);
    }
  }

  /**
   * Cache API response manually
   */
  cacheApiResponse(url: string, response: any): void {
    this.sendMessage({
      type: 'CACHE_API_RESPONSE',
      data: { url, response }
    });
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.sendMessage({ type: 'CLEAR_CACHE' });
  }

  /**
   * Check if service worker is active
   */
  isActive(): boolean {
    return this.registration?.active !== null;
  }

  /**
   * Get service worker state
   */
  getState(): string | null {
    if (!this.registration) return null;
    
    if (this.registration.installing) return 'installing';
    if (this.registration.waiting) return 'waiting';
    if (this.registration.active) return 'active';
    
    return 'unknown';
  }

  /**
   * Handle messages from service worker
   */
  private handleMessage(event: MessageEvent): void {
    const { type, data } = event.data;
    
    switch (type) {
      case 'CACHE_UPDATED':
        console.log('Cache updated for:', data.url);
        break;
      case 'OFFLINE_FALLBACK':
        console.log('Serving offline fallback for:', data.url);
        break;
      case 'SYNC_COMPLETE':
        console.log('Background sync completed:', data);
        this.notifySyncComplete(data);
        break;
      default:
        console.log('Unknown message from service worker:', type, data);
    }
  }

  /**
   * Notify about service worker update
   */
  private notifyUpdate(): void {
    // Dispatch custom event for components to listen to
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('sw-update-available'));
    }
  }

  /**
   * Notify about sync completion
   */
  private notifySyncComplete(data: any): void {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('sw-sync-complete', { detail: data }));
    }
  }

  /**
   * Register for background sync
   */
  async registerBackgroundSync(tag: string): Promise<void> {
    if (!this.registration) {
      throw new Error('Service Worker not registered');
    }

    try {
      await this.registration.sync.register(tag);
      console.log('Background sync registered:', tag);
    } catch (error) {
      console.error('Background sync registration failed:', error);
    }
  }

  /**
   * Check if background sync is supported
   */
  isBackgroundSyncSupported(): boolean {
    return this.isSupported && 'sync' in window.ServiceWorkerRegistration.prototype;
  }

  /**
   * Get cache storage estimate
   */
  async getStorageEstimate(): Promise<StorageEstimate | null> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        return await navigator.storage.estimate();
      } catch (error) {
        console.error('Failed to get storage estimate:', error);
      }
    }
    return null;
  }

  /**
   * Request persistent storage
   */
  async requestPersistentStorage(): Promise<boolean> {
    if ('storage' in navigator && 'persist' in navigator.storage) {
      try {
        return await navigator.storage.persist();
      } catch (error) {
        console.error('Failed to request persistent storage:', error);
      }
    }
    return false;
  }
}

// Export singleton instance
export const serviceWorkerManager = new ServiceWorkerManager();

// Auto-register service worker in production
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
  serviceWorkerManager.register().catch(console.error);
}

// Utility hooks for React components
export const useServiceWorker = () => {
  const [isActive, setIsActive] = React.useState(false);
  const [updateAvailable, setUpdateAvailable] = React.useState(false);
  const [syncInProgress, setSyncInProgress] = React.useState(false);

  React.useEffect(() => {
    // Check initial state
    setIsActive(serviceWorkerManager.isActive());

    // Listen for updates
    const handleUpdate = () => setUpdateAvailable(true);
    const handleSyncStart = () => setSyncInProgress(true);
    const handleSyncComplete = () => setSyncInProgress(false);

    window.addEventListener('sw-update-available', handleUpdate);
    window.addEventListener('sw-sync-start', handleSyncStart);
    window.addEventListener('sw-sync-complete', handleSyncComplete);

    return () => {
      window.removeEventListener('sw-update-available', handleUpdate);
      window.removeEventListener('sw-sync-start', handleSyncStart);
      window.removeEventListener('sw-sync-complete', handleSyncComplete);
    };
  }, []);

  return {
    isActive,
    updateAvailable,
    syncInProgress,
    update: () => serviceWorkerManager.skipWaiting(),
    clearCache: () => serviceWorkerManager.clearCache(),
  };
};

// Import React for the hook (will be available in components)
import React from 'react';