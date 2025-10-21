/**
 * Offline Data Export Component
 * Provides comprehensive data export functionality with offline support
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/utils/api';
import { offlineStorage } from '@/utils/offline-storage';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';

interface ExportOptions {
  format: 'json' | 'csv';
  includeOfflineData: boolean;
  includeDocuments: boolean;
  compressionLevel: 'none' | 'standard' | 'maximum';
}

interface ExportStatus {
  status: 'idle' | 'preparing' | 'exporting' | 'complete' | 'error';
  progress: number;
  message: string;
  downloadUrl?: string;
  error?: string;
}

export const OfflineDataExport: React.FC = () => {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'json',
    includeOfflineData: true,
    includeDocuments: false,
    compressionLevel: 'standard'
  });
  
  const [exportStatus, setExportStatus] = useState<ExportStatus>({
    status: 'idle',
    progress: 0,
    message: 'Ready to export'
  });
  
  const [storageStats, setStorageStats] = useState<any>(null);
  const [offlineCapabilities, setOfflineCapabilities] = useState<any>(null);

  useEffect(() => {
    loadStorageStats();
    loadOfflineCapabilities();
  }, []);

  const loadStorageStats = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/offline/storage-stats`);
      const stats = await response.json();
      setStorageStats(stats);
    } catch (error) {
      console.error('Failed to load storage stats:', error);
    }
  };

  const loadOfflineCapabilities = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/offline/capabilities`);
      const data = await response.json();
      if (response.ok) {
        setOfflineCapabilities(data);
      }
    } catch (error) {
      console.error('Failed to load offline capabilities:', error);
    }
  };

  const handleExport = async () => {
    setExportStatus({
      status: 'preparing',
      progress: 10,
      message: 'Preparing export...'
    });

    try {
      let result;
      
      if (exportOptions.includeOfflineData) {
        // Export with offline support
        setExportStatus({
          status: 'exporting',
          progress: 30,
          message: 'Exporting with offline support...'
        });
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/export/with-offline-support?include_offline_data=${exportOptions.includeOfflineData}`);
        result = await response.json();
      } else {
        // Standard export
        setExportStatus({
          status: 'exporting',
          progress: 30,
          message: 'Exporting user data...'
        });
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/export/user-data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ format: exportOptions.format })
        });
        result = await response.json();
      }

      if (result.success) {
        setExportStatus({
          status: 'exporting',
          progress: 70,
          message: 'Creating download file...'
        });

        // Create download
        const blob = new Blob([JSON.stringify(result.data, null, 2)], {
          type: exportOptions.format === 'json' ? 'application/json' : 'text/csv'
        });
        
        const url = URL.createObjectURL(blob);
        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `career-copilot-export-${timestamp}.${exportOptions.format}`;
        
        // Trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setExportStatus({
          status: 'complete',
          progress: 100,
          message: `Export completed: ${filename}`,
          downloadUrl: url
        });
      } else {
        throw new Error(result.error || 'Export failed');
      }
    } catch (error) {
      setExportStatus({
        status: 'error',
        progress: 0,
        message: 'Export failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  const handleOfflinePackageExport = async () => {
    setExportStatus({
      status: 'preparing',
      progress: 10,
      message: 'Preparing offline package...'
    });

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/export/offline-package`);
      const result = await response.json();
      
      if (result.success) {
        setExportStatus({
          status: 'exporting',
          progress: 50,
          message: 'Creating offline package...'
        });

        const blob = new Blob([JSON.stringify(result.data.offline_package, null, 2)], {
          type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `career-copilot-offline-package-${timestamp}.json`;
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setExportStatus({
          status: 'complete',
          progress: 100,
          message: `Offline package created: ${filename}`
        });
      } else {
        throw new Error(result.error || 'Offline package creation failed');
      }
    } catch (error) {
      setExportStatus({
        status: 'error',
        progress: 0,
        message: 'Offline package creation failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  const handleClearOfflineData = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/offline/clear-data`, {
        method: 'DELETE'
      });
      await loadStorageStats();
      setExportStatus({
        status: 'complete',
        progress: 100,
        message: 'Offline data cleared successfully'
      });
    } catch (error) {
      setExportStatus({
        status: 'error',
        progress: 0,
        message: 'Failed to clear offline data',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Data Export & Backup
        </h3>

        {/* Export Options */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Export Format
            </label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="json"
                  checked={exportOptions.format === 'json'}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, format: e.target.value as 'json' | 'csv' }))}
                  className="mr-2"
                />
                JSON (Recommended)
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="csv"
                  checked={exportOptions.format === 'csv'}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, format: e.target.value as 'json' | 'csv' }))}
                  className="mr-2"
                />
                CSV (Spreadsheet)
              </label>
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exportOptions.includeOfflineData}
                onChange={(e) => setExportOptions(prev => ({ ...prev, includeOfflineData: e.target.checked }))}
                className="mr-2"
              />
              Include offline functionality data
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exportOptions.includeDocuments}
                onChange={(e) => setExportOptions(prev => ({ ...prev, includeDocuments: e.target.checked }))}
                className="mr-2"
              />
              Include document metadata
            </label>
          </div>
        </div>

        {/* Export Status */}
        {exportStatus.status !== 'idle' && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {exportStatus.message}
              </span>
              <span className="text-sm text-gray-500">
                {exportStatus.progress}%
              </span>
            </div>
            <Progress value={exportStatus.progress} className="w-full" />
            {exportStatus.error && (
              <p className="text-sm text-red-600 mt-2">{exportStatus.error}</p>
            )}
          </div>
        )}

        {/* Export Actions */}
        <div className="flex space-x-3">
          <Button
            onClick={handleExport}
            disabled={exportStatus.status === 'preparing' || exportStatus.status === 'exporting'}
            className="flex-1"
          >
            {exportStatus.status === 'preparing' || exportStatus.status === 'exporting' 
              ? 'Exporting...' 
              : 'Export Data'
            }
          </Button>
          
          <Button
            onClick={handleOfflinePackageExport}
            variant="secondary"
            disabled={exportStatus.status === 'preparing' || exportStatus.status === 'exporting'}
          >
            Offline Package
          </Button>
        </div>
      </Card>

      {/* Storage Statistics */}
      {storageStats && (
        <Card className="p-6">
          <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
            Storage Statistics
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{storageStats.offlineJobs}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Cached Jobs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{storageStats.pendingActions}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Pending Sync</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{storageStats.cachedData}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Cached Items</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{formatBytes(storageStats.totalSize)}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Storage Used</div>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
            <Button
              onClick={handleClearOfflineData}
              variant="danger"
              size="sm"
            >
              Clear Offline Data
            </Button>
          </div>
        </Card>
      )}

      {/* Offline Capabilities */}
      {offlineCapabilities && (
        <Card className="p-6">
          <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
            Offline Capabilities
          </h4>
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Available Offline
              </h5>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(offlineCapabilities.offline_features).map(([feature, available]) => (
                  <div key={feature} className="flex items-center">
                    <span className={`w-2 h-2 rounded-full mr-2 ${available ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {feature.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Storage Support
              </h5>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                IndexedDB: {offlineCapabilities.storage.indexeddb ? '✅' : '❌'} | 
                Cache API: {offlineCapabilities.storage.cache_api ? '✅' : '❌'} | 
                Estimated Quota: {offlineCapabilities.storage.estimated_quota_mb}MB
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default OfflineDataExport;