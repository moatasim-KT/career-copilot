/**
 * API Client Configuration with Recovery Strategies
 * Example usage and configuration helpers
 */

import {
    createDefaultRecoveryManager,
    DegradedModeRecovery,
    type TokenRefreshConfig,
    type CacheFallbackConfig,
} from './recovery';

// ============================================================================
// Example Configuration
// ============================================================================

/**
 * Example: Configure API client with token refresh
 */
export function createApiClientWithTokenRefresh(
    baseUrl: string,
    getRefreshToken: () => Promise<string | null>,
    onTokenRefreshed: (token: string) => void,
) {
    const tokenRefreshConfig: TokenRefreshConfig = {
        refreshTokenFn: getRefreshToken,
        onTokenRefreshed,
        onRefreshFailed: (error) => {
            console.error('Token refresh failed:', error);
            // Redirect to login or show notification
        },
        maxRefreshAttempts: 2,
    };

    const recoveryManager = createDefaultRecoveryManager(tokenRefreshConfig);

    // Import APIClient dynamically to avoid circular dependency
    return { recoveryManager };
}

/**
 * Example: Configure API client with cache fallback
 */
export function createApiClientWithCacheFallback(baseUrl: string) {
    const cacheFallbackConfig: CacheFallbackConfig = {
        enabled: true,
        maxAge: 3600000, // 1 hour
        allowStale: true, // Allow stale cache when offline
    };

    const recoveryManager = createDefaultRecoveryManager(undefined, cacheFallbackConfig);

    return { recoveryManager };
}

/**
 * Example: Configure API client with all recovery strategies
 */
export function createResilientApiClient(
    baseUrl: string,
    tokenRefreshFn?: () => Promise<string | null>,
    onTokenRefreshed?: (token: string) => void,
) {
    const tokenRefreshConfig: TokenRefreshConfig | undefined = tokenRefreshFn
        ? {
            refreshTokenFn: tokenRefreshFn,
            onTokenRefreshed,
            onRefreshFailed: (error) => {
                console.error('Token refresh failed:', error);
            },
            maxRefreshAttempts: 2,
        }
        : undefined;

    const cacheFallbackConfig: CacheFallbackConfig = {
        enabled: true,
        maxAge: 3600000, // 1 hour
        allowStale: true,
    };

    const recoveryManager = createDefaultRecoveryManager(
        tokenRefreshConfig,
        cacheFallbackConfig,
    );

    // Optionally add degraded mode recovery
    const degradedMode = new DegradedModeRecovery();
    // Example: Register fallback endpoints
    degradedMode.registerDegradedEndpoint('/api/v1/jobs', '/api/v1/jobs/cached');
    recoveryManager.addStrategy(degradedMode);

    return { recoveryManager };
}

// ============================================================================
// Recovery Event Hooks
// ============================================================================

export interface RecoveryEventHandlers {
    onRecoveryAttempt?: (strategy: string, error: Error) => void;
    onRecoverySuccess?: (strategy: string, data: any) => void;
    onRecoveryFailure?: (error: Error) => void;
    onCacheFallback?: (url: string, age: number) => void;
    onTokenRefresh?: (newToken: string) => void;
}

/**
 * Add event handlers to recovery manager
 */
export function addRecoveryEventHandlers(
    recoveryManager: any,
    handlers: RecoveryEventHandlers,
) {
    // This is a simplified example
    // In a real implementation, you would enhance the RecoveryManager
    // to support event emission

    if (handlers.onTokenRefresh) {
        // Add token refresh handler
        const strategies = recoveryManager['strategies'] || [];
        const tokenRefreshStrategy = strategies.find(
            (s: any) => s.name === 'TokenRefreshRecovery',
        );

        if (tokenRefreshStrategy) {
            const originalOnTokenRefreshed = tokenRefreshStrategy['config'].onTokenRefreshed;
            tokenRefreshStrategy['config'].onTokenRefreshed = (token: string) => {
                handlers.onTokenRefresh?.(token);
                originalOnTokenRefreshed?.(token);
            };
        }
    }

    return recoveryManager;
}

// ============================================================================
// Usage Examples
// ============================================================================

/*
// Example 1: Simple API client with cache fallback
import { APIClient } from './api';
import { createApiClientWithCacheFallback } from './config';

const { recoveryManager } = createApiClientWithCacheFallback('http://localhost:8002');
const apiClient = new APIClient('http://localhost:8002', recoveryManager);

// Now all requests will automatically use cache fallback on errors
const jobs = await apiClient.getJobs();


// Example 2: API client with token refresh
import { APIClient } from './api';
import { createApiClientWithTokenRefresh } from './config';

const { recoveryManager } = createApiClientWithTokenRefresh(
  'http://localhost:8002',
  async () => {
    // Your token refresh logic
    const response = await fetch('/api/refresh-token', {
      method: 'POST',
      credentials: 'include',
    });
    const { token } = await response.json();
    return token;
  },
  (newToken) => {
    // Store new token
    localStorage.setItem('token', newToken);
  }
);

const apiClient = new APIClient('http://localhost:8002', recoveryManager);
apiClient.setToken(localStorage.getItem('token') || '');

// Requests will automatically refresh token on 401 errors


// Example 3: Full resilient API client
import { APIClient } from './api';
import { createResilientApiClient } from './config';

const { recoveryManager } = createResilientApiClient(
  'http://localhost:8002',
  async () => {
    // Token refresh logic
    const response = await fetch('/api/refresh-token');
    const { token } = await response.json();
    return token;
  },
  (newToken) => {
    localStorage.setItem('token', newToken);
  }
);

const apiClient = new APIClient('http://localhost:8002', recoveryManager);

// This client will:
// 1. Attempt token refresh on 401 errors
// 2. Use progressive retry on network errors
// 3. Fall back to cached data on failures
// 4. Use degraded endpoints if configured
*/
