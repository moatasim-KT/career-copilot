/**
 * Offline storage utilities using IndexedDB
 * Provides local data persistence for offline functionality
 */

interface OfflineAction {
  id: string;
  type: string;
  data: any;
  timestamp: number;
  retryCount: number;
}

interface CachedData {
  key: string;
  data: any;
  timestamp: number;
  expiresAt?: number;
}

class OfflineStorage {
  private dbName = 'career-copilot-offline';
  private version = 1;
  private db: IDBDatabase | null = null;

  /**
   * Initialize IndexedDB
   */
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => {
        reject(new Error('Failed to open IndexedDB'));
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object stores
        if (!db.objectStoreNames.contains('pendingActions')) {
          const actionStore = db.createObjectStore('pendingActions', { keyPath: 'id' });
          actionStore.createIndex('type', 'type', { unique: false });
          actionStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('cachedData')) {
          const dataStore = db.createObjectStore('cachedData', { keyPath: 'key' });
          dataStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('offlineJobs')) {
          const jobStore = db.createObjectStore('offlineJobs', { keyPath: 'id' });
          jobStore.createIndex('status', 'status', { unique: false });
          jobStore.createIndex('company', 'company', { unique: false });
        }

        if (!db.objectStoreNames.contains('userProfile')) {
          db.createObjectStore('userProfile', { keyPath: 'id' });
        }
      };
    });
  }

  /**
   * Store pending action for sync when online
   */
  async storePendingAction(type: string, data: any): Promise<string> {
    if (!this.db) await this.init();

    const action: OfflineAction = {
      id: `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      data,
      timestamp: Date.now(),
      retryCount: 0
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingActions'], 'readwrite');
      const store = transaction.objectStore('pendingActions');
      const request = store.add(action);

      request.onsuccess = () => resolve(action.id);
      request.onerror = () => reject(new Error('Failed to store pending action'));
    });
  }

  /**
   * Get all pending actions
   */
  async getPendingActions(): Promise<OfflineAction[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingActions'], 'readonly');
      const store = transaction.objectStore('pendingActions');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to get pending actions'));
    });
  }

  /**
   * Remove pending action after successful sync
   */
  async removePendingAction(id: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingActions'], 'readwrite');
      const store = transaction.objectStore('pendingActions');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to remove pending action'));
    });
  }

  /**
   * Cache data for offline access
   */
  async cacheData(key: string, data: any, expirationMinutes?: number): Promise<void> {
    if (!this.db) await this.init();

    const cachedData: CachedData = {
      key,
      data,
      timestamp: Date.now(),
      expiresAt: expirationMinutes ? Date.now() + (expirationMinutes * 60 * 1000) : undefined
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cachedData'], 'readwrite');
      const store = transaction.objectStore('cachedData');
      const request = store.put(cachedData);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to cache data'));
    });
  }

  /**
   * Get cached data
   */
  async getCachedData(key: string): Promise<any | null> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cachedData'], 'readonly');
      const store = transaction.objectStore('cachedData');
      const request = store.get(key);

      request.onsuccess = () => {
        const result = request.result;
        if (!result) {
          resolve(null);
          return;
        }

        // Check if data has expired
        if (result.expiresAt && Date.now() > result.expiresAt) {
          // Remove expired data
          this.removeCachedData(key);
          resolve(null);
          return;
        }

        resolve(result.data);
      };
      request.onerror = () => reject(new Error('Failed to get cached data'));
    });
  }

  /**
   * Remove cached data
   */
  async removeCachedData(key: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cachedData'], 'readwrite');
      const store = transaction.objectStore('cachedData');
      const request = store.delete(key);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to remove cached data'));
    });
  }

  /**
   * Store jobs for offline access
   */
  async storeOfflineJobs(jobs: any[]): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['offlineJobs'], 'readwrite');
      const store = transaction.objectStore('offlineJobs');

      // Clear existing jobs first
      const clearRequest = store.clear();
      clearRequest.onsuccess = () => {
        // Add new jobs
        let completed = 0;
        const total = jobs.length;

        if (total === 0) {
          resolve();
          return;
        }

        jobs.forEach(job => {
          const addRequest = store.add({
            ...job,
            offline: true,
            cachedAt: Date.now()
          });

          addRequest.onsuccess = () => {
            completed++;
            if (completed === total) {
              resolve();
            }
          };

          addRequest.onerror = () => {
            reject(new Error('Failed to store offline job'));
          };
        });
      };

      clearRequest.onerror = () => {
        reject(new Error('Failed to clear existing offline jobs'));
      };
    });
  }

  /**
   * Get offline jobs
   */
  async getOfflineJobs(): Promise<any[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['offlineJobs'], 'readonly');
      const store = transaction.objectStore('offlineJobs');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to get offline jobs'));
    });
  }

  /**
   * Store user profile for offline access
   */
  async storeUserProfile(profile: any): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['userProfile'], 'readwrite');
      const store = transaction.objectStore('userProfile');
      const request = store.put({
        id: 'current',
        ...profile,
        offline: true,
        cachedAt: Date.now()
      });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to store user profile'));
    });
  }

  /**
   * Get user profile
   */
  async getUserProfile(): Promise<any | null> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['userProfile'], 'readonly');
      const store = transaction.objectStore('userProfile');
      const request = store.get('current');

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(new Error('Failed to get user profile'));
    });
  }

  /**
   * Clear all offline data
   */
  async clearAllData(): Promise<void> {
    if (!this.db) await this.init();

    const storeNames = ['pendingActions', 'cachedData', 'offlineJobs', 'userProfile'];
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(storeNames, 'readwrite');
      let completed = 0;

      storeNames.forEach(storeName => {
        const store = transaction.objectStore(storeName);
        const request = store.clear();

        request.onsuccess = () => {
          completed++;
          if (completed === storeNames.length) {
            resolve();
          }
        };

        request.onerror = () => {
          reject(new Error(`Failed to clear ${storeName}`));
        };
      });
    });
  }

  /**
   * Get storage usage statistics
   */
  async getStorageStats(): Promise<{
    pendingActions: number;
    cachedData: number;
    offlineJobs: number;
    totalSize: number;
  }> {
    if (!this.db) await this.init();

    const [pendingActions, cachedData, offlineJobs] = await Promise.all([
      this.getPendingActions(),
      this.getAllCachedData(),
      this.getOfflineJobs()
    ]);

    // Estimate size (rough calculation)
    const totalSize = JSON.stringify({
      pendingActions,
      cachedData,
      offlineJobs
    }).length;

    return {
      pendingActions: pendingActions.length,
      cachedData: cachedData.length,
      offlineJobs: offlineJobs.length,
      totalSize
    };
  }

  /**
   * Get all cached data (for stats)
   */
  private async getAllCachedData(): Promise<CachedData[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cachedData'], 'readonly');
      const store = transaction.objectStore('cachedData');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to get all cached data'));
    });
  }
}

// Export singleton instance
export const offlineStorage = new OfflineStorage();

// Initialize on import
if (typeof window !== 'undefined') {
  offlineStorage.init().catch(console.error);
}

// Utility functions for common operations
export const offlineUtils = {
  /**
   * Store job application for offline sync
   */
  async storeJobApplication(jobId: number, applicationData: any): Promise<string> {
    return offlineStorage.storePendingAction('job-application', {
      jobId,
      ...applicationData
    });
  },

  /**
   * Store profile update for offline sync
   */
  async storeProfileUpdate(profileData: any): Promise<string> {
    return offlineStorage.storePendingAction('profile-update', profileData);
  },

  /**
   * Check if we're currently offline
   */
  isOffline(): boolean {
    return !navigator.onLine;
  },

  /**
   * Register for online/offline events
   */
  registerNetworkListeners(
    onOnline: () => void,
    onOffline: () => void
  ): () => void {
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);

    // Return cleanup function
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }
};