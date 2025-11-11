/**
 * Offline Banner Component
 * 
 * Displays a banner at the top of the page when the user is offline.
 * Shows connection status and provides retry option.
 * 
 * @module components/ui/OfflineBanner
 */

'use client';

import { WifiOff, X, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { useOfflineMode } from '@/hooks/useOfflineMode';

export function OfflineBanner() {
  const { isOffline, showOfflineBanner, dismissBanner, checkConnection } = useOfflineMode();
  const [isChecking, setIsChecking] = useState(false);

  const handleRetry = async () => {
    setIsChecking(true);
    await checkConnection();
    setIsChecking(false);
  };

  if (!isOffline || !showOfflineBanner) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-orange-500 dark:bg-orange-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Icon and message */}
          <div className="flex items-center gap-3 flex-1">
            <WifiOff className="h-5 w-5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium">You are currently offline</p>
              <p className="text-xs opacity-90 mt-0.5">
                Some features may be unavailable. We'll reconnect automatically when your connection is restored.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* Retry button */}
            <button
              onClick={handleRetry}
              disabled={isChecking}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-md transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Check connection"
            >
              <RefreshCw className={`h-4 w-4 ${isChecking ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Retry</span>
            </button>

            {/* Dismiss button */}
            <button
              onClick={dismissBanner}
              className="p-1.5 hover:bg-white/20 rounded-md transition-colors"
              aria-label="Dismiss banner"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Cached Data Indicator
 * 
 * Shows when viewing cached data while offline
 */
export function CachedDataIndicator() {
  const { isOffline } = useOfflineMode();

  if (!isOffline) {
    return null;
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded-md text-xs font-medium">
      <WifiOff className="h-3 w-3" />
      <span>Viewing cached data</span>
    </div>
  );
}
