/**
 * Stale-While-Revalidate (SWR) Pattern Implementation
 * 
 * This module demonstrates the SWR pattern using React Query.
 * The pattern shows cached data immediately while fetching fresh data in the background.
 * 
 * Key Benefits:
 * - Instant UI updates with cached data
 * - Background revalidation ensures data freshness
 * - Reduced perceived latency
 * - Better user experience
 */

import { useQuery, useQueryClient, type UseQueryOptions } from '@tanstack/react-query';
import { logger } from './logger';

/**
 * SWR Configuration Options
 */
export interface SWROptions<TData> extends Omit<UseQueryOptions<TData>, 'queryKey' | 'queryFn'> {
  /**
   * Time in milliseconds before data is considered stale
   * During this time, cached data is returned without revalidation
   */
  staleTime?: number;
  
  /**
   * Time in milliseconds before unused data is garbage collected
   */
  gcTime?: number;
  
  /**
   * Whether to refetch when component mounts
   */
  refetchOnMount?: boolean;
  
  /**
   * Whether to refetch when window regains focus
   */
  refetchOnWindowFocus?: boolean;
  
  /**
   * Whether to refetch when network reconnects
   */
  refetchOnReconnect?: boolean;
  
  /**
   * Whether to show cached data while revalidating
   * This is the core of the SWR pattern
   */
  keepPreviousData?: boolean;
}

/**
 * Default SWR configuration
 */
const DEFAULT_SWR_CONFIG: SWROptions<any> = {
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 10 * 60 * 1000, // 10 minutes
  refetchOnMount: true,
  refetchOnWindowFocus: false,
  refetchOnReconnect: true,
  keepPreviousData: true, // Show stale data while revalidating
};

/**
 * Custom hook implementing the SWR pattern
 * 
 * @example
 * ```tsx
 * const { data, isLoading, isStale } = useSWR(
 *   ['jobs', filters],
 *   () => fetchJobs(filters),
 *   { staleTime: 5 * 60 * 1000 }
 * );
 * 
 * // data is shown immediately from cache (if available)
 * // isStale indicates if data is being revalidated
 * ```
 */
export function useSWR<TData>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<TData>,
  options: SWROptions<TData> = {}
) {
  const mergedOptions = { ...DEFAULT_SWR_CONFIG, ...options };
  
  const result = useQuery({
    queryKey,
    queryFn: async () => {
      logger.debug('SWR: Fetching fresh data', { queryKey });
      const data = await queryFn();
      logger.debug('SWR: Fresh data received', { queryKey });
      return data;
    },
    ...mergedOptions,
  });
  
  // Determine if data is stale (being revalidated)
  const isStale = result.isFetching && !result.isLoading;
  
  return {
    ...result,
    isStale, // True when showing cached data while fetching fresh data
  };
}

/**
 * Hook to manually trigger revalidation
 */
export function useRevalidate() {
  const queryClient = useQueryClient();
  
  return {
    /**
     * Revalidate a specific query
     */
    revalidate: (queryKey: readonly unknown[]) => {
      logger.info('Manual revalidation triggered', { queryKey });
      return queryClient.invalidateQueries({ queryKey });
    },
    
    /**
     * Revalidate all queries
     */
    revalidateAll: () => {
      logger.info('Manual revalidation triggered for all queries');
      return queryClient.invalidateQueries();
    },
    
    /**
     * Refetch a specific query immediately
     */
    refetch: (queryKey: readonly unknown[]) => {
      logger.info('Manual refetch triggered', { queryKey });
      return queryClient.refetchQueries({ queryKey });
    },
  };
}

/**
 * Hook to check if data is being revalidated
 */
export function useIsRevalidating(queryKey?: readonly unknown[]) {
  const queryClient = useQueryClient();
  
  if (queryKey) {
    const query = queryClient.getQueryState(queryKey);
    return query?.isFetching && !query?.isLoading;
  }
  
  // Check if any query is revalidating
  const queries = queryClient.getQueryCache().getAll();
  return queries.some(query => query.state.isFetching && !query.state.isLoading);
}

/**
 * Prefetch data for SWR
 * Useful for prefetching data on hover or route changes
 */
export async function prefetchSWR<TData>(
  queryClient: any,
  queryKey: readonly unknown[],
  queryFn: () => Promise<TData>,
  options: SWROptions<TData> = {}
) {
  const mergedOptions = { ...DEFAULT_SWR_CONFIG, ...options };
  
  logger.debug('SWR: Prefetching data', { queryKey });
  
  await queryClient.prefetchQuery({
    queryKey,
    queryFn,
    ...mergedOptions,
  });
  
  logger.debug('SWR: Prefetch complete', { queryKey });
}

/**
 * Example: Jobs list with SWR
 */
export function useJobsWithSWR(filters: Record<string, any> = {}) {
  return useSWR(
    ['jobs', 'list', filters],
    async () => {
      // Simulate API call
      const response = await fetch('/api/jobs?' + new URLSearchParams(filters));
      return response.json();
    },
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
    }
  );
}

/**
 * Example: Applications list with SWR
 */
export function useApplicationsWithSWR(filters: Record<string, any> = {}) {
  return useSWR(
    ['applications', 'list', filters],
    async () => {
      // Simulate API call
      const response = await fetch('/api/applications?' + new URLSearchParams(filters));
      return response.json();
    },
    {
      staleTime: 1 * 60 * 1000, // 1 minute
      gcTime: 5 * 60 * 1000, // 5 minutes
    }
  );
}

/**
 * Example: User profile with SWR
 */
export function useUserProfileWithSWR() {
  return useSWR(
    ['user-profile', 'current'],
    async () => {
      // Simulate API call
      const response = await fetch('/api/profile');
      return response.json();
    },
    {
      staleTime: 30 * 60 * 1000, // 30 minutes
      gcTime: 60 * 60 * 1000, // 1 hour
      refetchOnWindowFocus: true, // Refetch when user returns to tab
    }
  );
}

/**
 * Example: Analytics with SWR
 */
export function useAnalyticsWithSWR() {
  return useSWR(
    ['analytics', 'summary'],
    async () => {
      // Simulate API call
      const response = await fetch('/api/analytics/summary');
      return response.json();
    },
    {
      staleTime: 10 * 60 * 1000, // 10 minutes
      gcTime: 30 * 60 * 1000, // 30 minutes
      refetchOnMount: false, // Don't auto-refetch on mount
      refetchOnWindowFocus: false, // Don't auto-refetch on focus
    }
  );
}

/**
 * Example: Notifications with SWR
 */
export function useNotificationsWithSWR() {
  return useSWR(
    ['notifications', 'list'],
    async () => {
      // Simulate API call
      const response = await fetch('/api/notifications');
      return response.json();
    },
    {
      staleTime: 30 * 1000, // 30 seconds
      gcTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: true, // Refetch when user returns to tab
      refetchOnReconnect: true, // Refetch when network reconnects
    }
  );
}
