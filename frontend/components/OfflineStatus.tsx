/**
 * Offline Status Component
 * Shows current offline/online status and pending sync actions
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/utils/api';
import { offlineStorage } from '@/utils/offline-storage';
import { useServiceWorker } from '@/utils/service-worker';

interface OfflineStatusProps {
  className?: string;
}

interface StorageStats {
  pendingActions: number;
  cachedData: number;
  offlineJobs: number;
  totalSize: number;
}

export const OfflineStatus: React.FC<OfflineStatusProps> = ({ className = '' }) => {
  const [isOnline, setIsOnline] = useState(true);
  const [pendingActions, setPendingActions] = useState(0);
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const { isActive, syncInProgress, updateAvailable, update, clearCache } = useServiceWorker();

  useEffect(() => {
    // Monitor network status
    const updateOnlineStatus = () => {
      setIsOnline(navigator.onLine);
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Initial status
    updateOnlineStatus();

    // Load storage stats
    loadStorageStats();

    // Update stats periodically
    const interval = setInterval(loadStorageStats, 30000); // Every 30 seconds

    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
      clearInterval(interval);
    };
  }, []);

  const loadStorageStats = async () => {
    try {
      const stats = await offlineStorage.getStorageStats();
      setStorageStats(stats);
      setPendingActions(stats.pendingActions);
    } catch (error) {
      console.error('Failed to load storage stats:', error);
    }
  };

  const handleClearCache = async () => {
    try {
      await apiClient.clearOfflineData();
      clearCache();
      await loadStorageStats();
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  const handleExportData = async () => {
    try {
      const response = await apiClient.exportUserData('json');
      if (response.success) {
        // Create download link
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `career-copilot-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  const getStatusColor = () => {
    if (!isOnline) return 'bg-red-500';
    if (syncInProgress) return 'bg-yellow-500';
    if (pendingActions > 0) return 'bg-orange-500';
    return 'bg-green-500';
  };

  const getStatusText = () => {
    if (!isOnline) return 'Offline';
    if (syncInProgress) return 'Syncing...';
    if (pendingActions > 0) return `${pendingActions} pending`;
    return 'Online';
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`relative ${className}`}>
      {/* Status Indicator */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
      >
        <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {getStatusText()}
        </span>
        {isActive && (
          <div className="w-2 h-2 rounded-full bg-blue-500" title="Service Worker Active" />
        )}
      </button>

      {/* Details Panel */}
      {showDetails && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          <div className="p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Offline Status
            </h3>

            {/* Connection Status */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Connection</span>
                <span className={`text-sm font-medium ${isOnline ? 'text-green-600' : 'text-red-600'}`}>
                  {isOnline ? 'Online' : 'Offline'}
                </span>
              </div>
              
              {!isOnline && (
                <div className="text-xs text-gray-500 dark:text-gray-400 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded">
                  You're offline. Changes will sync when connection is restored.
                </div>
              )}
            </div>

            {/* Service Worker Status */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Service Worker</span>
                <span className={`text-sm font-medium ${isActive ? 'text-green-600' : 'text-gray-500'}`}>
                  {isActive ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              {updateAvailable && (
                <button
                  onClick={update}
                  className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600 transition-colors"
                >
                  Update Available - Click to Refresh
                </button>
              )}
            </div>

            {/* Storage Stats */}
            {storageStats && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Offline Storage
                </h4>
                <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                  <div className="flex justify-between">
                    <span>Cached Jobs:</span>
                    <span>{storageStats.offlineJobs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pending Actions:</span>
                    <span>{storageStats.pendingActions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Storage Used:</span>
                    <span>{formatBytes(storageStats.totalSize)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2">
              <button
                onClick={handleExportData}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              >
                📥 Export Data
              </button>
              
              <button
                onClick={handleClearCache}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              >
                🗑️ Clear Cache
              </button>
              
              {pendingActions > 0 && (
                <div className="px-3 py-2 text-xs text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 rounded">
                  {pendingActions} action{pendingActions !== 1 ? 's' : ''} will sync when online
                </div>
              )}
            </div>

            {/* Offline Capabilities */}
            <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-600">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Available Offline
              </h4>
              <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <div>✅ Browse cached jobs</div>
                <div>✅ Edit profile</div>
                <div>✅ Track applications</div>
                <div>✅ View analytics</div>
                <div>✅ Export data</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OfflineStatus;