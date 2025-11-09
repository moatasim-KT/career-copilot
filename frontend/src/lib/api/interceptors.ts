/**
 * API Interceptors for logging, monitoring, and debugging
 */

import type { RequestInterceptor, ResponseInterceptor } from './api';

// ============================================================================
// Logging Interceptor
// ============================================================================

interface LoggingOptions {
    logRequests?: boolean;
    logResponses?: boolean;
    logErrors?: boolean;
    logBody?: boolean;
    logHeaders?: boolean;
}

export function createLoggingInterceptor(options: LoggingOptions = {}): {
    request: RequestInterceptor;
    response: ResponseInterceptor;
} {
    const {
        logRequests = true,
        logResponses = true,
        logErrors = true,
        logBody = true,
        logHeaders = false,
    } = options;

    return {
        request: {
            onRequest: async (config: RequestInit, url: string) => {
                if (logRequests) {
                    const logData: any = {
                        method: config.method || 'GET',
                        url,
                        timestamp: new Date().toISOString(),
                    };

                    if (logHeaders && config.headers) {
                        logData.headers = config.headers;
                    }

                    if (logBody && config.body) {
                        try {
                            logData.body = typeof config.body === 'string' ? JSON.parse(config.body) : config.body;
                        } catch {
                            logData.body = config.body;
                        }
                    }

                    console.log('[API Request]', logData);
                }
                return config;
            },
            onRequestError: (error: Error) => {
                if (logErrors) {
                    console.error('[API Request Error]', {
                        error: error.message,
                        timestamp: new Date().toISOString(),
                    });
                }
            },
        },
        response: {
            onResponse: async (response: Response) => {
                if (logResponses) {
                    console.log('[API Response]', {
                        url: response.url,
                        status: response.status,
                        statusText: response.statusText,
                        timestamp: new Date().toISOString(),
                    });
                }
                return response;
            },
            onResponseError: (error: Error) => {
                if (logErrors) {
                    console.error('[API Response Error]', {
                        error: error.message,
                        timestamp: new Date().toISOString(),
                    });
                }
            },
        },
    };
}

// ============================================================================
// Performance Monitoring Interceptor
// ============================================================================

interface PerformanceMetrics {
    url: string;
    method: string;
    duration: number;
    timestamp: number;
    status?: number;
}

export function createPerformanceInterceptor(
    onMetrics?: (metrics: PerformanceMetrics) => void,
): {
    request: RequestInterceptor;
    response: ResponseInterceptor;
} {
    const requestTimes = new Map<string, number>();

    return {
        request: {
            onRequest: async (config: RequestInit, url: string) => {
                const requestKey = `${config.method || 'GET'}:${url}`;
                requestTimes.set(requestKey, Date.now());
                return config;
            },
        },
        response: {
            onResponse: async (response: Response) => {
                const requestKey = `${response.url}`;
                const startTime = requestTimes.get(requestKey);

                if (startTime) {
                    const duration = Date.now() - startTime;
                    const metrics: PerformanceMetrics = {
                        url: response.url,
                        method: 'GET', // Could be extracted from request
                        duration,
                        timestamp: Date.now(),
                        status: response.status,
                    };

                    if (onMetrics) {
                        onMetrics(metrics);
                    }

                    // Log slow requests
                    if (duration > 3000) {
                        console.warn('[Slow API Request]', {
                            url: response.url,
                            duration: `${duration}ms`,
                            status: response.status,
                        });
                    }

                    requestTimes.delete(requestKey);
                }

                return response;
            },
        },
    };
}

// ============================================================================
// Token Refresh Interceptor
// ============================================================================

export function createAuthInterceptor(
    getToken: () => string | null,
    refreshToken: () => Promise<string | null>,
    onAuthError?: () => void,
): RequestInterceptor {
    return {
        onRequest: async (config: RequestInit, url: string) => {
            const token = getToken();

            if (token) {
                const headers = new Headers(config.headers);
                headers.set('Authorization', `Bearer ${token}`);
                config.headers = headers;
            }

            return config;
        },
        onRequestError: async (error: Error) => {
            // Handle 401 errors and attempt token refresh
            if (error.message.includes('401') || error.message.includes('Authentication')) {
                try {
                    const newToken = await refreshToken();
                    if (!newToken && onAuthError) {
                        onAuthError();
                    }
                } catch (_refreshError) {
                    if (onAuthError) {
                        onAuthError();
                    }
                }
            }
        },
    };
}

// ============================================================================
// Retry Headers Interceptor
// ============================================================================

export function createRetryHeadersInterceptor(): RequestInterceptor {
    let retryCount = 0;

    return {
        onRequest: async (config: RequestInit, url: string) => {
            const headers = new Headers(config.headers);

            if (retryCount > 0) {
                headers.set('X-Retry-Count', retryCount.toString());
            }

            config.headers = headers;
            return config;
        },
        onRequestError: (error: Error) => {
            retryCount++;
        },
    };
}

// ============================================================================
// Request ID Interceptor
// ============================================================================

export function createRequestIdInterceptor(): RequestInterceptor {
    return {
        onRequest: async (config: RequestInit, url: string) => {
            const headers = new Headers(config.headers);
            const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            headers.set('X-Request-ID', requestId);
            config.headers = headers;
            return config;
        },
    };
}

// ============================================================================
// Cache Control Interceptor
// ============================================================================

export function createCacheControlInterceptor(
    getCacheHeaders: (url: string) => Record<string, string>,
): RequestInterceptor {
    return {
        onRequest: async (config: RequestInit, url: string) => {
            const cacheHeaders = getCacheHeaders(url);
            const headers = new Headers(config.headers);

            Object.entries(cacheHeaders).forEach(([key, value]) => {
                headers.set(key, value);
            });

            config.headers = headers;
            return config;
        },
    };
}
