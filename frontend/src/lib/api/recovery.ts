/**
 * Error Recovery Strategies for API Client
 * Provides fallback mechanisms for handling various error scenarios
 */

import { logger } from '@/lib/logger';

import { get, set } from './cache';


// ============================================================================
// Types
// ============================================================================

export interface RecoveryStrategy {
    name: string;
    canRecover: (error: Error) => boolean;
    recover: <T>(
        error: Error,
        context: RecoveryContext
    ) => Promise<T | null>;
}

export interface RecoveryContext {
    url: string;
    options: RequestInit;
    requestId: string;
    retryCount?: number;
    originalResponse?: Response;
}

export interface TokenRefreshConfig {
    refreshTokenFn: () => Promise<string | null>;
    onTokenRefreshed?: (token: string) => void;
    onRefreshFailed?: (error: Error) => void;
    maxRefreshAttempts?: number;
}

export interface CacheFallbackConfig {
    enabled: boolean;
    maxAge?: number; // Maximum age of cached data to use as fallback (ms)
    allowStale?: boolean; // Allow stale cache when offline
}

export interface RetryConfig {
    maxAttempts: number;
    baseDelay: number;
    maxDelay: number;
    backoffMultiplier: number;
}

// ============================================================================
// Token Refresh Strategy
// ============================================================================

export class TokenRefreshRecovery implements RecoveryStrategy {
    name = 'TokenRefreshRecovery';
    private refreshPromise: Promise<string | null> | null = null;
    private refreshAttempts = 0;

    constructor(private config: TokenRefreshConfig) { }

    canRecover(error: Error): boolean {
        // Recover from 401 Authentication errors
        return error.name === 'AuthenticationError' ||
            (!!error.message && error.message.includes('401'));
    }

    async recover<T>(
        error: Error,
        context: RecoveryContext,
    ): Promise<T | null> {
        const maxAttempts = this.config.maxRefreshAttempts || 1;

        // Check if we've exceeded max refresh attempts
        if (this.refreshAttempts >= maxAttempts) {
            this.config.onRefreshFailed?.(new Error('Max token refresh attempts exceeded'));
            this.refreshAttempts = 0;
            return null;
        }

        try {
            // Deduplicate refresh requests - if refresh is in progress, wait for it
            if (!this.refreshPromise) {
                this.refreshAttempts++;
                this.refreshPromise = this.config.refreshTokenFn();
            }

            const newToken = await this.refreshPromise;
            this.refreshPromise = null;

            if (!newToken) {
                this.config.onRefreshFailed?.(new Error('Token refresh returned null'));
                return null;
            }

            // Notify that token was refreshed
            this.config.onTokenRefreshed?.(newToken);

            // Retry the original request with new token
            const updatedOptions = {
                ...context.options,
                headers: {
                    ...context.options.headers,
                    Authorization: `Bearer ${newToken}`,
                },
            };

            const response = await fetch(context.url, updatedOptions);

            if (!response.ok) {
                return null;
            }

            const data = await response.json();
            this.refreshAttempts = 0; // Reset on success
            return data;
        } catch (refreshError) {
            this.refreshPromise = null;
            this.config.onRefreshFailed?.(refreshError as Error);
            return null;
        }
    }

    reset() {
        this.refreshAttempts = 0;
        this.refreshPromise = null;
    }
}

// ============================================================================
// Cache Fallback Strategy
// ============================================================================

export class CacheFallbackRecovery implements RecoveryStrategy {
    name = 'CacheFallbackRecovery';

    constructor(private config: CacheFallbackConfig) { }

    canRecover(error: Error): boolean {
        if (!this.config.enabled) return false;

        // Recover from network errors and server errors
        return (
            error.name === 'NetworkError' ||
            error.name === 'ServerError' ||
            error.name === 'TimeoutError' ||
            error.message?.includes('fetch') ||
            error.message?.includes('network') ||
            error.message?.includes('timeout')
        );
    }

    async recover<T>(
        error: Error,
        context: RecoveryContext,
    ): Promise<T | null> {
        try {
            const cacheKey = this.getCacheKey(context.url, context.options);
            const cachedData = await get<CacheEntry<T>>(cacheKey);

            if (!cachedData) {
                return null;
            }

            const now = Date.now();
            const age = now - cachedData.timestamp;
            const maxAge = this.config.maxAge || 3600000; // Default 1 hour

            // Check if cached data is fresh enough
            if (age <= maxAge) {
                logger.warn(`Using cached data for ${context.url} (age: ${age}ms)`);
                return cachedData.data;
            }

            // If stale cache is allowed, use it anyway
            if (this.config.allowStale) {
                logger.warn(`Using stale cached data for ${context.url} (age: ${age}ms)`);
                return cachedData.data;
            }

            return null;
        } catch (cacheError) {
            logger.error('Cache fallback error:', cacheError);
            return null;
        }
    }

    private getCacheKey(url: string, options: RequestInit): string {
        const method = options.method || 'GET';
        const body = options.body ? JSON.stringify(options.body) : '';
        return `api-cache:${method}:${url}:${body}`;
    }

    /**
     * Cache a successful response for later fallback
     */
    async cacheResponse<T>(
        url: string,
        options: RequestInit,
        data: T,
    ): Promise<void> {
        if (!this.config.enabled) return;

        try {
            const cacheKey = this.getCacheKey(url, options);
            const entry: CacheEntry<T> = {
                data,
                timestamp: Date.now(),
            };

            // Cache for 24 hours by default
            await set(cacheKey, entry, 86400000);
        } catch (error) {
            logger.error('Failed to cache response:', error);
        }
    }
}

interface CacheEntry<T> {
    data: T;
    timestamp: number;
}

// ============================================================================
// Progressive Retry Strategy
// ============================================================================

export class ProgressiveRetryRecovery implements RecoveryStrategy {
    name = 'ProgressiveRetryRecovery';

    constructor(private config: RetryConfig) { }

    canRecover(error: Error): boolean {
        // Retry transient errors but not client errors
        return (
            error.name === 'NetworkError' ||
            error.name === 'TimeoutError' ||
            error.name === 'ServerError' ||
            (!!error.message &&
                (error.message.includes('503') ||
                    error.message.includes('502') ||
                    error.message.includes('504')))
        );
    }

    async recover<T>(
        error: Error,
        context: RecoveryContext,
    ): Promise<T | null> {
        const retryCount = context.retryCount || 0;

        if (retryCount >= this.config.maxAttempts) {
            return null;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
            this.config.baseDelay * Math.pow(this.config.backoffMultiplier, retryCount),
            this.config.maxDelay,
        );

        logger.info(`Retry attempt ${retryCount + 1}/${this.config.maxAttempts} after ${delay}ms`);

        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, delay));

        try {
            const response = await fetch(context.url, context.options);

            if (!response.ok) {
                // If still failing, return null to try next recovery strategy
                return null;
            }

            const data = await response.json();
            return data;
        } catch (__retryError) {
            // If retry fails, return null to try next recovery strategy
            return null;
        }
    }
}

// ============================================================================
// Degraded Mode Strategy
// ============================================================================

export class DegradedModeRecovery implements RecoveryStrategy {
    name = 'DegradedModeRecovery';
    private degradedEndpoints: Map<string, string> = new Map();

    constructor(degradedEndpoints?: Map<string, string>) {
        this.degradedEndpoints = degradedEndpoints || new Map();
    }

    canRecover(error: Error): boolean {
        // Try degraded mode for server errors
        return error.name === 'ServerError' || error.name === 'NetworkError';
    }

    async recover<T>(
        error: Error,
        context: RecoveryContext,
    ): Promise<T | null> {
        const degradedUrl = this.getDegradedEndpoint(context.url);

        if (!degradedUrl) {
            return null;
        }

        logger.warn(`Falling back to degraded endpoint: ${degradedUrl}`);

        try {
            const response = await fetch(degradedUrl, context.options);

            if (!response.ok) {
                return null;
            }

            const data = await response.json();
            return data;
        } catch (degradedError) {
            logger.error('Degraded mode failed:', degradedError);
            return null;
        }
    }

    /**
     * Register a degraded endpoint fallback
     */
    registerDegradedEndpoint(originalPath: string, degradedPath: string) {
        this.degradedEndpoints.set(originalPath, degradedPath);
    }

    private getDegradedEndpoint(url: string): string | null {
        for (const [original, degraded] of this.degradedEndpoints.entries()) {
            if (url.includes(original)) {
                return url.replace(original, degraded);
            }
        }
        return null;
    }
}

// ============================================================================
// Recovery Manager
// ============================================================================

export class RecoveryManager {
    private strategies: RecoveryStrategy[] = [];

    constructor(strategies?: RecoveryStrategy[]) {
        if (strategies) {
            this.strategies = strategies;
        }
    }

    /**
     * Add a recovery strategy
     */
    addStrategy(strategy: RecoveryStrategy) {
        this.strategies.push(strategy);
    }

    /**
     * Remove a recovery strategy by name
     */
    removeStrategy(name: string) {
        this.strategies = this.strategies.filter(s => s.name !== name);
    }

    /**
     * Attempt to recover from an error using registered strategies
     */
    async recover<T>(
        error: Error,
        context: RecoveryContext,
    ): Promise<T | null> {
        logger.info(`Attempting recovery for error: ${error.name} - ${error.message}`);

        for (const strategy of this.strategies) {
            if (strategy.canRecover(error)) {
                logger.info(`Trying recovery strategy: ${strategy.name}`);

                try {
                    const result = await strategy.recover<T>(error, context);

                    if (result !== null) {
                        logger.info(`Recovery successful using: ${strategy.name}`);
                        return result;
                    }
                } catch (recoveryError) {
                    logger.error(`Recovery strategy ${strategy.name} failed:`, recoveryError);
                    // Continue to next strategy
                }
            }
        }

        logger.info('All recovery strategies failed');
        return null;
    }
}

// ============================================================================
// Default Recovery Configuration
// ============================================================================

export function createDefaultRecoveryManager(
    tokenRefreshConfig?: TokenRefreshConfig,
    cacheFallbackConfig?: CacheFallbackConfig,
): RecoveryManager {
    const manager = new RecoveryManager();

    // Add token refresh strategy if configured
    if (tokenRefreshConfig) {
        manager.addStrategy(new TokenRefreshRecovery(tokenRefreshConfig));
    }

    // Add progressive retry strategy
    manager.addStrategy(new ProgressiveRetryRecovery({
        maxAttempts: 3,
        baseDelay: 1000,
        maxDelay: 10000,
        backoffMultiplier: 2,
    }));

    // Add cache fallback strategy if configured
    if (cacheFallbackConfig?.enabled) {
        manager.addStrategy(new CacheFallbackRecovery(cacheFallbackConfig));
    }

    return manager;
}
