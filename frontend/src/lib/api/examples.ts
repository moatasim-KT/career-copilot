/**
 * Example Usage of API Client with Recovery Strategies
 * This file demonstrates various recovery configurations
 */

import { APIClient } from './api';
import {
    RecoveryManager,
    TokenRefreshRecovery,
    CacheFallbackRecovery,
    ProgressiveRetryRecovery,
    DegradedModeRecovery,
} from './recovery';

// ============================================================================
// Example 1: Basic API Client (No Recovery)
// ============================================================================

export function createBasicApiClient() {
    const apiClient = new APIClient('http://localhost:8002');
    return apiClient;
}

// ============================================================================
// Example 2: API Client with Cache Fallback Only
// ============================================================================

export function createCachedApiClient() {
    const recoveryManager = new RecoveryManager();

    // Add cache fallback strategy
    recoveryManager.addStrategy(
        new CacheFallbackRecovery({
            enabled: true,
            maxAge: 3600000, // 1 hour
            allowStale: true, // Use stale cache when offline
        }),
    );

    // Note: APIClient now creates its own recovery manager internally
    const apiClient = new APIClient('http://localhost:8002');
    return apiClient;
}

// ============================================================================
// Example 3: API Client with Token Refresh
// ============================================================================

export function createAuthApiClient(
    getAccessToken: () => string | null,
    setAccessToken: (token: string) => void,
) {
    const recoveryManager = new RecoveryManager();

    // Add token refresh strategy
    recoveryManager.addStrategy(
        new TokenRefreshRecovery({
            refreshTokenFn: async () => {
                // Call your refresh endpoint
                try {
                    const response = await fetch('http://localhost:8002/api/v1/auth/refresh', {
                        method: 'POST',
                        credentials: 'include', // Send refresh token cookie
                    });

                    if (!response.ok) {
                        return null;
                    }

                    const { access_token } = await response.json();
                    return access_token;
                } catch (error) {
                    console.error('Token refresh failed:', error);
                    return null;
                }
            },
            onTokenRefreshed: (newToken) => {
                console.log('Token refreshed successfully');
                setAccessToken(newToken);
            },
            onRefreshFailed: (error) => {
                console.error('Token refresh failed, redirecting to login:', error);
                // Redirect to login page
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
            },
            maxRefreshAttempts: 2,
        }),
    );

    // Note: APIClient now creates its own recovery manager internally
    const apiClient = new APIClient('http://localhost:8002');

    // Set initial token if available
    const token = getAccessToken();
    if (token) {
        apiClient.setToken(token);
    }

    return apiClient;
}

// ============================================================================
// Example 4: Production-Ready Resilient API Client
// ============================================================================

export function createProductionApiClient(options?: {
    enableTokenRefresh?: boolean;
    enableCacheFallback?: boolean;
    enableDegradedMode?: boolean;
    onTokenRefresh?: (token: string) => void;
    onRecoveryFailure?: () => void;
}) {
    const {
        enableTokenRefresh = false,
        enableCacheFallback = true,
        enableDegradedMode = false,
        onTokenRefresh,
        onRecoveryFailure,
    } = options || {};

    const recoveryManager = new RecoveryManager();

    // 1. Token Refresh (if enabled)
    if (enableTokenRefresh) {
        recoveryManager.addStrategy(
            new TokenRefreshRecovery({
                refreshTokenFn: async () => {
                    const response = await fetch('/api/v1/auth/refresh', {
                        method: 'POST',
                        credentials: 'include',
                    });

                    if (!response.ok) return null;

                    const { access_token } = await response.json();
                    return access_token;
                },
                onTokenRefreshed: (token) => {
                    onTokenRefresh?.(token);
                },
                onRefreshFailed: (error) => {
                    console.error('Token refresh failed:', error);
                    onRecoveryFailure?.();
                },
                maxRefreshAttempts: 2,
            }),
        );
    }

    // 2. Progressive Retry (always enabled)
    recoveryManager.addStrategy(
        new ProgressiveRetryRecovery({
            maxAttempts: 3,
            baseDelay: 1000,
            maxDelay: 10000,
            backoffMultiplier: 2,
        }),
    );

    // 3. Cache Fallback (if enabled)
    if (enableCacheFallback) {
        recoveryManager.addStrategy(
            new CacheFallbackRecovery({
                enabled: true,
                maxAge: 3600000, // 1 hour
                allowStale: true,
            }),
        );
    }

    // 4. Degraded Mode (if enabled)
    if (enableDegradedMode) {
        const degradedMode = new DegradedModeRecovery();

        // Register degraded endpoints
        degradedMode.registerDegradedEndpoint('/api/v1/jobs', '/api/v1/jobs/cached');
        degradedMode.registerDegradedEndpoint('/api/v1/analytics', '/api/v1/analytics/summary');

        recoveryManager.addStrategy(degradedMode);
    }

    // Note: APIClient now creates its own recovery manager internally
    const apiClient = new APIClient(
        process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002',
    );

    return apiClient;
}

// ============================================================================
// Example 5: Development API Client with Verbose Logging
// ============================================================================

export function createDevApiClient() {
    const recoveryManager = new RecoveryManager();

    // Add all recovery strategies with logging
    recoveryManager.addStrategy(
        new ProgressiveRetryRecovery({
            maxAttempts: 3,
            baseDelay: 500,
            maxDelay: 5000,
            backoffMultiplier: 2,
        }),
    );

    recoveryManager.addStrategy(
        new CacheFallbackRecovery({
            enabled: true,
            maxAge: 300000, // 5 minutes in dev
            allowStale: true,
        }),
    );

    // Note: APIClient now creates its own recovery manager internally
    const apiClient = new APIClient('http://localhost:8002');

    // Add logging interceptor
    apiClient.addRequestInterceptor({
        onRequest: async (config: RequestInit, url: string) => {
            console.log('🚀 Request:', url, config.method || 'GET');
            return config;
        },
    });

    apiClient.addResponseInterceptor({
        onResponse: async (response: Response) => {
            console.log('✅ Response:', response.url, response.status);
            return response;
        },
        onResponseError: (error: Error) => {
            console.error('❌ Response Error:', error);
        },
    });

    return apiClient;
}

// ============================================================================
// Example 6: Singleton API Client Instance
// ============================================================================

let apiClientInstance: APIClient | null = null;

export function getApiClient(): APIClient {
    if (!apiClientInstance) {
        apiClientInstance = createProductionApiClient({
            enableCacheFallback: true,
            enableTokenRefresh: false, // Set to true if using authentication
        });
    }

    return apiClientInstance;
}

// ============================================================================
// Usage in React Components
// ============================================================================

/*
// In a React component:

import { getApiClient } from '@/lib/api/examples';

export function JobsList() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchJobs() {
      try {
        const apiClient = getApiClient();
        const response = await apiClient.getJobs(0, 50);

        if (response.error) {
          setError(response.error);
        } else {
          setJobs(response.data || []);
        }
      } catch {
        setError('Failed to fetch jobs');
      } finally {
        setLoading(false);
      }
    }

    fetchJobs();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {jobs.map(job => (
        <div key={job.id}>{job.title}</div>
      ))}
    </div>
  );
}


// With cache fallback, if the API is down, users will still see
// the last successfully fetched data!
*/
