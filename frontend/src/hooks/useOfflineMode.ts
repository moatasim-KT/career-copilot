/**
 * Offline Mode Detection Hook
 * 
 * Detects online/offline status and provides offline mode functionality.
 * Shows offline banner, caches data, and disables network-dependent actions.
 * 
 * @module hooks/useOfflineMode
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';

export interface OfflineModeState {
  isOnline: boolean;
  isOffline: boolean;
  showOfflineBanner: boolean;
  canUseNetworkFeatures: boolean;
}

export interface OfflineModeActions {
  dismissBanner: () => void;
  checkConnection: () => Promise<boolean>;
}

export interface UseOfflineModeReturn extends OfflineModeState, OfflineModeActions {}

/**
 * Hook to detect and manage offline mode
 */
export function useOfflineMode(): UseOfflineModeReturn {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [showOfflineBanner, setShowOfflineBanner] = useState(false);

  /**
   * Check actual network connectivity by making a request
   */
  const checkConnection = useCallback(async (): Promise<boolean> => {
    try {
      // Try to fetch a small resource to verify connectivity
      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache',
      });
      return response.ok;
    } catch {
      return false;
    }
  }, []);

  /**
   * Handle online event
   */
  const handleOnline = useCallback(() => {
    setIsOnline(true);
    setShowOfflineBanner(false);

    // Show success toast
    toast.success('Back Online', {
      description: 'Your connection has been restored.',
      duration: 3000,
    });

    // Dismiss any offline toasts
    toast.dismiss('offline-toast');
  }, []);

  /**
   * Handle offline event
   */
  const handleOffline = useCallback(() => {
    setIsOnline(false);
    setShowOfflineBanner(true);

    // Show offline toast
    toast.error('You are offline', {
      description: 'Some features may be unavailable.',
      duration: Infinity,
      id: 'offline-toast',
    });
  }, []);

  /**
   * Dismiss offline banner
   */
  const dismissBanner = useCallback(() => {
    setShowOfflineBanner(false);
  }, []);

  /**
   * Set up event listeners
   */
  useEffect(() => {
    // Add event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check initial connection status
    if (!navigator.onLine) {
      handleOffline();
    }

    // Periodic connection check (every 30 seconds when offline)
    let intervalId: NodeJS.Timeout | null = null;

    if (!isOnline) {
      intervalId = setInterval(async () => {
        const connected = await checkConnection();
        if (connected && !isOnline) {
          handleOnline();
        }
      }, 30000);
    }

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isOnline, handleOnline, handleOffline, checkConnection]);

  return {
    isOnline,
    isOffline: !isOnline,
    showOfflineBanner,
    canUseNetworkFeatures: isOnline,
    dismissBanner,
    checkConnection,
  };
}

/**
 * Hook to disable network-dependent actions when offline
 */
export function useNetworkAction<T extends (...args: any[]) => any>(
  action: T,
  options?: {
    offlineMessage?: string;
    showToast?: boolean;
  }
): T {
  const { isOnline } = useOfflineMode();
  const { offlineMessage = 'This action requires an internet connection.', showToast = true } =
    options || {};

  return ((...args: any[]) => {
    if (!isOnline) {
      if (showToast) {
        toast.warning('Offline', {
          description: offlineMessage,
          duration: 3000,
        });
      }
      return Promise.reject(new Error('Offline'));
    }

    return action(...args);
  }) as T;
}
