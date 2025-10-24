'use client';

import { HealthMonitor } from '@/components/monitoring/HealthMonitor';
import axios from 'axios';
import { useEffect, useState } from 'react';

interface ComponentHealth {
  status: string;
  components: {
    backend: any;
    frontend: any;
    database: any;
  };
  message: string;
}

export default function HealthPage() {
  const [systemHealth, setSystemHealth] = useState<ComponentHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSystemHealth = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/v1/health/comprehensive');
        setSystemHealth(response.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch health status');
      } finally {
        setLoading(false);
      }
    };

    fetchSystemHealth();
    const interval = setInterval(fetchSystemHealth, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">System Health Dashboard</h1>

      <div className="mb-8">
        <HealthMonitor />
      </div>

      {loading && (
        <div className="text-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2">Loading health status...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p>{error}</p>
        </div>
      )}

      {systemHealth && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Backend Health */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Backend Status</h2>
            <div
              className={`text-lg font-medium ${getStatusColor(systemHealth.components.backend.status)}`}
            >
              {systemHealth.components.backend.status}
            </div>
            <pre className="mt-4 bg-gray-50 p-4 rounded text-sm overflow-auto">
              {JSON.stringify(systemHealth.components.backend, null, 2)}
            </pre>
          </div>

          {/* Frontend Health */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Frontend Status</h2>
            <div
              className={`text-lg font-medium ${getStatusColor(systemHealth.components.frontend.status)}`}
            >
              {systemHealth.components.frontend.status}
            </div>
            <pre className="mt-4 bg-gray-50 p-4 rounded text-sm overflow-auto">
              {JSON.stringify(systemHealth.components.frontend, null, 2)}
            </pre>
          </div>

          {/* Database Health */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Database Status</h2>
            <div
              className={`text-lg font-medium ${getStatusColor(systemHealth.components.database.status)}`}
            >
              {systemHealth.components.database.status}
            </div>
            <pre className="mt-4 bg-gray-50 p-4 rounded text-sm overflow-auto">
              {JSON.stringify(systemHealth.components.database, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <style jsx>{`
        pre {
          max-height: 300px;
        }
      `}</style>
    </div>
  );
}
