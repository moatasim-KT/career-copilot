/**
 * Unified API Client
 * 
 * Central API client for all backend communication.
 * Handles authentication, error handling, and request/response formatting.
 * 
 * @module lib/api/client
 */

import { logger } from '@/lib/logger';

import {
    handleError,
    retryWithBackoff,
} from '../errorHandling';

export type { Job as JobResponse, Application as ApplicationResponse } from './api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
const API_VERSION = '/api/v1';

interface RequestOptions extends RequestInit {
    params?: Record<string, string | number | boolean>;
    requiresAuth?: boolean;
}

interface ApiResponse<T = any> {
    data?: T;
    error?: string;
    status: number;
}

/**
 * Get authentication token from storage
 */
function getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
}

/**
 * Build URL with query parameters
 */
function buildUrl(endpoint: string, params?: Record<string, any>): string {
    const url = new URL(`${API_BASE_URL}${API_VERSION}${endpoint}`);

    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                url.searchParams.append(key, String(value));
            }
        });
    }

    return url.toString();
}

/**
 * Base fetch wrapper with error handling and retry logic
 */
async function fetchApi<T = any>(
    endpoint: string,
    options: RequestOptions = {},
): Promise<ApiResponse<T>> {
    const { params, requiresAuth = false, ...fetchOptions } = options;

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(fetchOptions.headers as Record<string, string>),
    };

    // Add auth token if required (authentication disabled by default)
    if (requiresAuth) {
        const token = getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }

    const url = buildUrl(endpoint, params);

    // Wrap fetch in retry logic
    try {
        return await retryWithBackoff(
            async () => {
                try {
                    const response = await fetch(url, {
                        ...fetchOptions,
                        headers,
                    });

                    let data: T | undefined;
                    const contentType = response.headers.get('content-type');

                    if (contentType?.includes('application/json')) {
                        data = await response.json();
                    }

                    if (!response.ok) {
                        const error: any = new Error(
                            (data as any)?.detail || `HTTP ${response.status}: ${response.statusText}`,
                        );
                        error.status = response.status;
                        error.response = { status: response.status, data };

                        // Intercept and handle specific errors
                        // Handle authentication errors
                        if (response.status === 401) {
                            handleError(error, {
                                component: 'API Client',
                                action: `${fetchOptions.method || 'GET'} ${endpoint}`,
                            });
                            // Optionally redirect to login
                            if (typeof window !== 'undefined') {
                                // Store current URL for redirect after login
                                sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
                            }
                        }
                        // Handle forbidden errors
                        else if (response.status === 403) {
                            handleError(error, {
                                component: 'API Client',
                                action: `${fetchOptions.method || 'GET'} ${endpoint}`,
                            });
                        }
                        // Handle not found errors
                        else if (response.status === 404) {
                            handleError(error, {
                                component: 'API Client',
                                action: `${fetchOptions.method || 'GET'} ${endpoint}`,
                            });
                        }
                        // Handle server errors
                        else if (response.status >= 500) {
                            handleError(error, {
                                component: 'API Client',
                                action: `${fetchOptions.method || 'GET'} ${endpoint}`,
                            });
                        }

                        // Throw error to trigger retry if applicable
                        throw error;
                    }

                    return {
                        data,
                        status: response.status,
                    };
                } catch (error: any) {
                    // Handle network errors
                    if (error instanceof TypeError || error.message === 'Failed to fetch') {
                        const networkError: any = new Error('Network error');
                        networkError.status = 0;
                        networkError.originalError = error;

                        handleError(networkError, {
                            component: 'API Client',
                            action: `${fetchOptions.method || 'GET'} ${endpoint}`,
                        });

                        throw networkError;
                    }

                    // Re-throw other errors
                    throw error;
                }
            },
            undefined, // Use default retry config
            (attemptNumber, error) => {
                // Log retry attempts in development
                if (process.env.NODE_ENV === 'development') {
                    logger.info(`Retry attempt ${attemptNumber} for ${endpoint}`, error);
                }
            },
        );
    } catch (error: any) {
        // Final error after all retries
        return {
            error: error.message || 'Request failed',
            status: error.status || 0,
        };
    }
}

/**
 * API Client
 */
export const apiClient = {
    // ============================================================================
    // Authentication
    // ============================================================================
    auth: {
        login: (email: string, password: string) =>
            fetchApi('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password }),
                requiresAuth: false,
            }),

        register: (email: string, password: string, username: string) =>
            fetchApi('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ email, password, username }),
                requiresAuth: false,
            }),

        logout: () =>
            fetchApi('/auth/logout', {
                method: 'POST',
                requiresAuth: true,
            }),

        me: () =>
            fetchApi('/auth/me', { requiresAuth: true }),
    },

    // ============================================================================
    // Jobs
    // ============================================================================
    jobs: {
        list: (params?: { skip?: number; limit?: number }) =>
            fetchApi('/jobs', { params, requiresAuth: true }),

        get: (id: number) =>
            fetchApi(`/jobs/${id}`, { requiresAuth: true }),

        create: (data: any) =>
            fetchApi('/jobs', {
                method: 'POST',
                body: JSON.stringify(data),
                requiresAuth: true,
            }),

        update: (id: number, data: any) =>
            fetchApi(`/jobs/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
                requiresAuth: true,
            }),

        delete: (id: number) =>
            fetchApi(`/jobs/${id}`, {
                method: 'DELETE',
                requiresAuth: true,
            }),

        available: (params?: { limit?: number; skip?: number }) =>
            fetchApi('/jobs/available', { params, requiresAuth: true }),

        scrape: () =>
            fetchApi('/jobs/scrape', {
                method: 'POST',
                requiresAuth: true,
            }),
    },

    // ============================================================================
    // Applications
    // ============================================================================
    applications: {
        list: (params?: { skip?: number; limit?: number; status?: string }) =>
            fetchApi('/applications', { params, requiresAuth: true }),

        get: (id: number) =>
            fetchApi(`/applications/${id}`, { requiresAuth: true }),

        create: (data: any) =>
            fetchApi('/applications', {
                method: 'POST',
                body: JSON.stringify(data),
                requiresAuth: true,
            }),

        update: (id: number, data: any) =>
            fetchApi(`/applications/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
                requiresAuth: true,
            }),

        delete: (id: number) =>
            fetchApi(`/applications/${id}`, {
                method: 'DELETE',
                requiresAuth: true,
            }),
    },

    // ============================================================================
    // Recommendations
    // ============================================================================
    recommendations: {
        list: (params?: { limit?: number; use_adaptive?: boolean }) =>
            fetchApi('/recommendations', { params }),

        algorithmInfo: () =>
            fetchApi('/recommendations/algorithm-info'),

        feedback: (jobId: number, isPositive: boolean, reason?: string) =>
            fetchApi(`/recommendations/${jobId}/feedback`, {
                method: 'POST',
                body: JSON.stringify({
                    is_positive: isPositive,
                    reason,
                }),
                requiresAuth: true,
            }),
    },

    // ============================================================================
    // Personalization
    // ============================================================================
    personalization: {
        getPreferences: (userId: number) =>
            fetchApi(`/users/${userId}/preferences`, { requiresAuth: true }),

        updatePreferences: (userId: number, preferences: any) =>
            fetchApi(`/users/${userId}/preferences`, {
                method: 'PUT',
                body: JSON.stringify(preferences),
                requiresAuth: true,
            }),

        getBehavior: (userId: number) =>
            fetchApi(`/users/${userId}/behavior`, { requiresAuth: true }),

        trackBehavior: (userId: number, action: string, jobId: string) =>
            fetchApi(`/users/${userId}/behavior`, {
                method: 'POST',
                body: JSON.stringify({ action, job_id: jobId }),
                requiresAuth: true,
            }),
    },

    // ============================================================================
    // Social Features
    // ============================================================================
    social: {
        getMentors: (userId: number, limit?: number) => {
            const params: Record<string, number> = {};
            if (limit !== undefined) params.limit = limit;
            return fetchApi(`/users/${userId}/mentors`, { params });
        },

        createConnection: (userId: number, mentorId: string) =>
            fetchApi(`/users/${userId}/connections`, {
                method: 'POST',
                body: JSON.stringify({ mentor_id: mentorId }),
            }),

        getConnections: (userId: number, statusFilter?: string) => {
            const params: Record<string, string> = {};
            if (statusFilter) params.status_filter = statusFilter;
            return fetchApi(`/users/${userId}/connections`, { params });
        },
    },

    // ============================================================================
    // Analytics
    // ============================================================================
    analytics: {
        get: (params?: { userId?: string; period?: string }) =>
            fetchApi('/analytics', { params }),

        dashboard: (userId: string) =>
            fetchApi('/analytics/dashboard', { params: { user_id: userId } }),
    },

    // ============================================================================
    // User Profile
    // ============================================================================
    user: {
        getProfile: () =>
            fetchApi('/users/me/profile'),

        updateProfile: (data: any) =>
            fetchApi('/users/me/profile', {
                method: 'PUT',
                body: JSON.stringify(data),
            }),

        getSettings: () =>
            fetchApi('/users/me/settings'),

        updateSettings: (data: any) =>
            fetchApi('/users/me/settings', {
                method: 'PUT',
                body: JSON.stringify(data),
            }),

        changePassword: (currentPassword: string, newPassword: string) =>
            fetchApi('/users/me/change-password', {
                method: 'POST',
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword,
                }),
            }),
    },

    // ============================================================================
    // Health & Status
    // ============================================================================
    health: {
        check: () =>
            fetchApi('/health', { requiresAuth: false }),

        comprehensive: () =>
            fetchApi('/health/comprehensive', { requiresAuth: false }),
    },
};

/**
 * Type-safe API client hooks
 */
export const ApplicationsService = apiClient.applications;
export const JobsService = apiClient.jobs;
export const AuthServices = apiClient.auth;
export const RecommendationsService = apiClient.recommendations;
export const PersonalizationService = apiClient.personalization;
export const SocialService = apiClient.social;
export const AnalyticsService = apiClient.analytics;
export const UserService = apiClient.user;
export const HealthService = apiClient.health;

// Export fetchApi for direct use when needed
export { fetchApi };

export default apiClient;
