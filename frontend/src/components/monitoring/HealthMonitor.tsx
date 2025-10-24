'use client';

import axios from 'axios';
import { useEffect, useState } from 'react';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  message: string;
  timestamp: string;
  response_time_ms: number;
  details?: Record<string, any>;
  error?: string;
}

interface ErrorMonitorProps {
  onError: (error: Error) => void;
}

const ErrorMonitor: React.FC<ErrorMonitorProps> = ({ onError }) => {
  useEffect(() => {
    let errorCount = 0;
    const maxErrors = 10;

    const handleError = (error: Error) => {
      errorCount++;
      onError(error);

      // Report to health endpoint if too many errors
      if (errorCount >= maxErrors) {
        fetch('/_health/js-errors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            error_count: errorCount,
            latest_error: error.message,
          }),
        }).catch(console.error);
      }
    };

    // Add global error handler
    const originalOnError = window.onerror;
    window.onerror = (msg, url, line, col, error) => {
      handleError(error || new Error(msg as string));
      if (originalOnError) {
        return originalOnError(msg, url, line, col, error);
      }
      return false;
    };

    // Add unhandled promise rejection handler
    const unhandledRejection = (event: PromiseRejectionEvent) => {
      handleError(event.reason);
    };
    window.addEventListener('unhandledrejection', unhandledRejection);

    return () => {
      window.onerror = originalOnError;
      window.removeEventListener('unhandledrejection', unhandledRejection);
    };
  }, [onError]);

  return null;
};

export function HealthMonitor() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [jsErrors, setJsErrors] = useState<Error[]>([]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const start = performance.now();
        const response = await axios.get('/api/health');
        const responseTime = performance.now() - start;

        setHealth({
          status: response.data.status,
          message: response.data.message,
          timestamp: new Date().toISOString(),
          response_time_ms: responseTime,
          details: response.data.details,
        });
      } catch (error) {
        setHealth({
          status: 'unhealthy',
          message: 'Health check failed',
          timestamp: new Date().toISOString(),
          response_time_ms: 0,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    };

    // Check health immediately and then every 30 seconds
    checkHealth();
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleJsError = (error: Error) => {
    setJsErrors(prev => [...prev, error]);
  };

  return (
    <div className="health-monitor">
      <ErrorMonitor onError={handleJsError} />

      {health && (
        <div className={`health-status health-status-${health.status}`}>
          <h3>Application Health</h3>
          <p>Status: {health.status}</p>
          <p>Last Check: {new Date(health.timestamp).toLocaleString()}</p>
          <p>Response Time: {health.response_time_ms.toFixed(2)}ms</p>

          {health.error && (
            <div className="health-error">
              <h4>Error</h4>
              <p>{health.error}</p>
            </div>
          )}

          {health.details && (
            <div className="health-details">
              <h4>Details</h4>
              <pre>{JSON.stringify(health.details, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {jsErrors.length > 0 && (
        <div className="js-errors">
          <h3>JavaScript Errors</h3>
          <ul>
            {jsErrors.map((error, index) => (
              <li key={index}>
                {error.message}
                <br />
                <small>{error.stack}</small>
              </li>
            ))}
          </ul>
        </div>
      )}

      <style jsx>{`
        .health-monitor {
          padding: 1rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          margin: 1rem 0;
        }

        .health-status {
          padding: 1rem;
          border-radius: 4px;
          margin-bottom: 1rem;
        }

        .health-status-healthy {
          background-color: #d4edda;
          border: 1px solid #c3e6cb;
        }

        .health-status-degraded {
          background-color: #fff3cd;
          border: 1px solid #ffeeba;
        }

        .health-status-unhealthy {
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
        }

        .health-error,
        .js-errors {
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          padding: 1rem;
          border-radius: 4px;
          margin-top: 1rem;
        }

        .health-details {
          margin-top: 1rem;
          padding: 1rem;
          background-color: #f8f9fa;
          border-radius: 4px;
          overflow-x: auto;
        }

        pre {
          margin: 0;
          white-space: pre-wrap;
        }
      `}</style>
    </div>
  );
}
