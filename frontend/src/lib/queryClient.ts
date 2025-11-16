/**
 * React Query Client Configuration
 * 
 * Optimized caching and state management configuration for different data types.
 * Implements stale-while-revalidate pattern with appropriate cache times.
 */

import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';

import { logger } from './logger';

/**
 * Query key prefixes for different data types
 */
export const QUERY_KEYS = {
  JOBS: 'jobs',
  APPLICATIONS: 'applications',
  USER_PROFILE: 'user-profile',
  ANALYTICS: 'analytics',
  NOTIFICATIONS: 'notifications',
  RECOMMENDATIONS: 'recommendations',
  SKILL_GAP: 'skill-gap',
  CONTENT: 'content',
  INTERVIEW: 'interview',
  FEEDBACK: 'feedback',
} as const;

/**
 * Cache time configurations for different data types (in milliseconds)
 */
export const CACHE_CONFIG = {
  // Jobs list: 5 min stale time, refetch on mount
  JOBS: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  },
  
  // Applications: 1 min stale time, refetch on mount
  APPLICATIONS: {
    staleTime: 1 * 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  },
  
  // User profile: 30 min stale time, refetch on focus
  USER_PROFILE: {
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    refetchOnMount: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
  
  // Analytics: 10 min stale time, no auto-refetch
  ANALYTICS: {
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  },
  
  // Notifications: 30 sec stale time, refetch on focus
  NOTIFICATIONS: {
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
  
  // Recommendations: 5 min stale time, refetch on mount
  RECOMMENDATIONS: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  },
  
  // Skill gap analysis: 15 min stale time
  SKILL_GAP: {
    staleTime: 15 * 60 * 1000, // 15 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  },
  
  // Search results: 30 sec stale time
  SEARCH: {
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  },
} as const;

/**
 * Default retry configuration with exponential backoff
 */
const defaultRetry = (failureCount: number, error: any) => {
  // Don't retry on 4xx errors (client errors)
  if (error?.statusCode >= 400 && error?.statusCode < 500) {
    return false;
  }
  
  // Retry up to 3 times for network/server errors
  return failureCount < 3;
};

/**
 * Default retry delay with exponential backoff
 */
const defaultRetryDelay = (attemptIndex: number) => {
  return Math.min(1000 * 2 ** attemptIndex, 30000);
};

/**
 * Create a configured QueryClient instance
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    queryCache: new QueryCache({
      onError: (error, query) => {
        logger.error('Query error:', {
          error,
          queryKey: query.queryKey,
        });
      },
      onSuccess: (data, query) => {
        logger.debug('Query success:', {
          queryKey: query.queryKey,
          dataSize: JSON.stringify(data).length,
        });
      },
    }),
    
    mutationCache: new MutationCache({
      onError: (error, variables, context, mutation) => {
        logger.error('Mutation error:', {
          error,
          mutationKey: mutation.options.mutationKey,
        });
      },
      onSuccess: (data, variables, context, mutation) => {
        logger.debug('Mutation success:', {
          mutationKey: mutation.options.mutationKey,
        });
      },
    }),
    
    defaultOptions: {
      queries: {
        // Default configuration for all queries
        staleTime: 5 * 60 * 1000, // 5 minutes default
        gcTime: 10 * 60 * 1000, // 10 minutes default (formerly cacheTime)
        refetchOnMount: true,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        retry: defaultRetry,
        retryDelay: defaultRetryDelay,
        
        // Network mode
        networkMode: 'online',
        
        // Structural sharing for better performance
        structuralSharing: true,
        
        // Throw errors to error boundaries
        throwOnError: false,
      },
      
      mutations: {
        // Default configuration for all mutations
        retry: false, // Don't retry mutations by default
        networkMode: 'online',
        
        // Throw errors to error boundaries
        throwOnError: false,
      },
    },
  });
}

/**
 * Helper to get cache config for a specific query type
 */
export function getCacheConfig(queryType: keyof typeof CACHE_CONFIG) {
  return CACHE_CONFIG[queryType];
}

/**
 * Helper to create query keys with proper typing
 */
export const queryKeys = {
  // Jobs
  jobs: {
    all: [QUERY_KEYS.JOBS] as const,
    lists: () => [QUERY_KEYS.JOBS, 'list'] as const,
    list: (filters: Record<string, any>) => [QUERY_KEYS.JOBS, 'list', filters] as const,
    details: () => [QUERY_KEYS.JOBS, 'detail'] as const,
    detail: (id: number) => [QUERY_KEYS.JOBS, 'detail', id] as const,
    search: (query: string) => [QUERY_KEYS.JOBS, 'search', query] as const,
  },
  
  // Applications
  applications: {
    all: [QUERY_KEYS.APPLICATIONS] as const,
    lists: () => [QUERY_KEYS.APPLICATIONS, 'list'] as const,
    list: (filters: Record<string, any>) => [QUERY_KEYS.APPLICATIONS, 'list', filters] as const,
    details: () => [QUERY_KEYS.APPLICATIONS, 'detail'] as const,
    detail: (id: number) => [QUERY_KEYS.APPLICATIONS, 'detail', id] as const,
    search: (query: string) => [QUERY_KEYS.APPLICATIONS, 'search', query] as const,
  },
  
  // User profile
  userProfile: {
    all: [QUERY_KEYS.USER_PROFILE] as const,
    current: () => [QUERY_KEYS.USER_PROFILE, 'current'] as const,
  },
  
  // Analytics
  analytics: {
    all: [QUERY_KEYS.ANALYTICS] as const,
    summary: () => [QUERY_KEYS.ANALYTICS, 'summary'] as const,
    comprehensive: (days: number) => [QUERY_KEYS.ANALYTICS, 'comprehensive', days] as const,
  },
  
  // Notifications
  notifications: {
    all: [QUERY_KEYS.NOTIFICATIONS] as const,
    lists: () => [QUERY_KEYS.NOTIFICATIONS, 'list'] as const,
    list: (filters: Record<string, any>) => [QUERY_KEYS.NOTIFICATIONS, 'list', filters] as const,
    preferences: () => [QUERY_KEYS.NOTIFICATIONS, 'preferences'] as const,
  },
  
  // Recommendations
  recommendations: {
    all: [QUERY_KEYS.RECOMMENDATIONS] as const,
    list: (filters: Record<string, any>) => [QUERY_KEYS.RECOMMENDATIONS, 'list', filters] as const,
  },
  
  // Skill gap
  skillGap: {
    all: [QUERY_KEYS.SKILL_GAP] as const,
    analysis: () => [QUERY_KEYS.SKILL_GAP, 'analysis'] as const,
  },
  
  // Content
  content: {
    all: [QUERY_KEYS.CONTENT] as const,
    detail: (id: string) => [QUERY_KEYS.CONTENT, 'detail', id] as const,
  },
  
  // Interview
  interview: {
    all: [QUERY_KEYS.INTERVIEW] as const,
    session: (id: string) => [QUERY_KEYS.INTERVIEW, 'session', id] as const,
    summary: (id: string) => [QUERY_KEYS.INTERVIEW, 'summary', id] as const,
  },
  
  // Feedback
  feedback: {
    all: [QUERY_KEYS.FEEDBACK] as const,
    summary: () => [QUERY_KEYS.FEEDBACK, 'summary'] as const,
  },
} as const;

/**
 * Prefetch helper for common queries
 */
export async function prefetchQuery(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
  queryFn: () => Promise<any>,
  config?: Record<string, any>,
) {
  await queryClient.prefetchQuery({
    queryKey,
    queryFn,
    ...config,
  });
}

/**
 * Invalidate queries helper
 */
export function invalidateQueries(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
) {
  return queryClient.invalidateQueries({ queryKey });
}

/**
 * Set query data helper
 */
export function setQueryData<T>(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
  data: T | ((old: T | undefined) => T),
) {
  return queryClient.setQueryData(queryKey, data);
}

/**
 * Get query data helper
 */
export function getQueryData<T>(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
): T | undefined {
  return queryClient.getQueryData(queryKey);
}
