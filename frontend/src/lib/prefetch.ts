/**
 * Prefetching Utilities
 * 
 * This module provides utilities for prefetching data to improve perceived performance.
 * Prefetching loads data before it's needed, reducing wait times when users navigate.
 * 
 * Key Benefits:
 * - Instant page transitions
 * - Reduced perceived latency
 * - Better user experience
 * - Predictive data loading
 */

import { useQueryClient, type QueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef } from 'react';

import { apiClient } from './api/api';
import { logger } from './logger';
import { queryKeys, getCacheConfig } from './queryClient';

/**
 * Prefetch configuration options
 */
export interface PrefetchOptions {
  /**
   * Time in milliseconds before data is considered stale
   */
  staleTime?: number;
  
  /**
   * Whether to force refetch even if data exists
   */
  force?: boolean;
  
  /**
   * Whether to log prefetch operations
   */
  silent?: boolean;
}

/**
 * Prefetch a job detail
 */
export async function prefetchJob(
  queryClient: QueryClient,
  jobId: number,
  options: PrefetchOptions = {},
) {
  const { silent = false } = options;
  
  if (!silent) {
    logger.debug('Prefetching job', { jobId });
  }
  
  await queryClient.prefetchQuery({
    queryKey: queryKeys.jobs.detail(jobId),
    queryFn: async () => {
      const response = await apiClient.getJobs(jobId, 1);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data?.[0];
    },
    ...getCacheConfig('JOBS'),
    ...options,
  });
}

/**
 * Prefetch an application detail
 */
export async function prefetchApplication(
  queryClient: QueryClient,
  applicationId: number,
  options: PrefetchOptions = {},
) {
  const { silent = false } = options;
  
  if (!silent) {
    logger.debug('Prefetching application', { applicationId });
  }
  
  await queryClient.prefetchQuery({
    queryKey: queryKeys.applications.detail(applicationId),
    queryFn: async () => {
      const response = await apiClient.getApplications(applicationId, 1);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data?.[0];
    },
    ...getCacheConfig('APPLICATIONS'),
    ...options,
  });
}

/**
 * Prefetch jobs list
 */
export async function prefetchJobs(
  queryClient: QueryClient,
  filters: Record<string, any> = {},
  options: PrefetchOptions = {},
) {
  const { silent = false } = options;
  const { skip = 0, limit = 100 } = filters;
  
  if (!silent) {
    logger.debug('Prefetching jobs list', { filters });
  }
  
  await queryClient.prefetchQuery({
    queryKey: queryKeys.jobs.list(filters),
    queryFn: async () => {
      const response = await apiClient.getJobs(skip, limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    ...getCacheConfig('JOBS'),
    ...options,
  });
}

/**
 * Prefetch applications list
 */
export async function prefetchApplications(
  queryClient: QueryClient,
  filters: Record<string, any> = {},
  options: PrefetchOptions = {},
) {
  const { silent = false } = options;
  const { skip = 0, limit = 100 } = filters;
  
  if (!silent) {
    logger.debug('Prefetching applications list', { filters });
  }
  
  await queryClient.prefetchQuery({
    queryKey: queryKeys.applications.list(filters),
    queryFn: async () => {
      const response = await apiClient.getApplications(skip, limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    ...getCacheConfig('APPLICATIONS'),
    ...options,
  });
}

/**
 * Prefetch next page of paginated data
 */
export async function prefetchNextPage(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
  currentPage: number,
  pageSize: number,
  fetchFn: (skip: number, limit: number) => Promise<any>,
  options: PrefetchOptions = {},
) {
  const { silent = false } = options;
  const nextSkip = (currentPage + 1) * pageSize;
  
  if (!silent) {
    logger.debug('Prefetching next page', { queryKey, currentPage, nextSkip });
  }
  
  await queryClient.prefetchQuery({
    queryKey: [...queryKey, 'page', currentPage + 1],
    queryFn: () => fetchFn(nextSkip, pageSize),
    ...options,
  });
}

/**
 * Hook to prefetch on hover
 * 
 * @example
 * ```tsx
 * const prefetchOnHover = usePrefetchOnHover();
 * 
 * <div onMouseEnter={() => prefetchOnHover(() => prefetchJob(queryClient, jobId))}>
 *   Job Card
 * </div>
 * ```
 */
export function usePrefetchOnHover() {
  const prefetchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  return useCallback((prefetchFn: () => Promise<void>, delay: number = 200) => {
    // Clear any existing timeout
    if (prefetchTimeoutRef.current) {
      clearTimeout(prefetchTimeoutRef.current);
    }
    
    // Set new timeout to prefetch after delay
    prefetchTimeoutRef.current = setTimeout(() => {
      prefetchFn().catch(error => {
        logger.error('Prefetch on hover failed:', error);
      });
    }, delay);
    
    return () => {
      if (prefetchTimeoutRef.current) {
        clearTimeout(prefetchTimeoutRef.current);
      }
    };
  }, []);
}

/**
 * Hook to prefetch job on hover
 */
export function usePrefetchJob() {
  const queryClient = useQueryClient();
  const prefetchOnHover = usePrefetchOnHover();
  
  return useCallback((jobId: number) => {
    return prefetchOnHover(() => prefetchJob(queryClient, jobId, { silent: true }));
  }, [queryClient, prefetchOnHover]);
}

/**
 * Hook to prefetch application on hover
 */
export function usePrefetchApplication() {
  const queryClient = useQueryClient();
  const prefetchOnHover = usePrefetchOnHover();
  
  return useCallback((applicationId: number) => {
    return prefetchOnHover(() => prefetchApplication(queryClient, applicationId, { silent: true }));
  }, [queryClient, prefetchOnHover]);
}

/**
 * Hook to prefetch next page when near end of list
 * 
 * @example
 * ```tsx
 * const { observerRef } = usePrefetchNextPage({
 *   currentPage: 0,
 *   pageSize: 20,
 *   totalItems: 100,
 *   onPrefetch: () => prefetchJobs(queryClient, { skip: 20, limit: 20 }),
 * });
 * 
 * <div ref={observerRef}>Sentinel element near end of list</div>
 * ```
 */
export function usePrefetchNextPage(config: {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  onPrefetch: () => Promise<void>;
  threshold?: number;
}) {
  const { currentPage, pageSize, totalItems, onPrefetch, threshold = 0.8 } = config;
  const observerRef = useRef<HTMLDivElement>(null);
  const hasPrefetchedRef = useRef(false);
  
  useEffect(() => {
    const hasMorePages = (currentPage + 1) * pageSize < totalItems;
    
    if (!hasMorePages || !observerRef.current) {
      return;
    }
    
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        
        if (entry.isIntersecting && !hasPrefetchedRef.current) {
          hasPrefetchedRef.current = true;
          
          logger.debug('Prefetching next page (intersection)', {
            currentPage,
            nextPage: currentPage + 1,
          });
          
          onPrefetch().catch(error => {
            logger.error('Prefetch next page failed:', error);
            hasPrefetchedRef.current = false;
          });
        }
      },
      { threshold },
    );
    
    observer.observe(observerRef.current);
    
    return () => {
      observer.disconnect();
    };
  }, [currentPage, pageSize, totalItems, onPrefetch, threshold]);
  
  // Reset prefetch flag when page changes
  useEffect(() => {
    hasPrefetchedRef.current = false;
  }, [currentPage]);
  
  return { observerRef };
}

/**
 * Hook to prefetch on scroll position
 */
export function usePrefetchOnScroll(config: {
  onPrefetch: () => Promise<void>;
  threshold?: number;
  enabled?: boolean;
}) {
  const { onPrefetch, threshold = 0.8, enabled = true } = config;
  const hasPrefetchedRef = useRef(false);
  
  useEffect(() => {
    if (!enabled) return;
    
    const handleScroll = () => {
      const scrollHeight = document.documentElement.scrollHeight;
      const scrollTop = document.documentElement.scrollTop;
      const clientHeight = document.documentElement.clientHeight;
      
      const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
      
      if (scrollPercentage >= threshold && !hasPrefetchedRef.current) {
        hasPrefetchedRef.current = true;
        
        logger.debug('Prefetching on scroll', { scrollPercentage });
        
        onPrefetch().catch(error => {
          logger.error('Prefetch on scroll failed:', error);
          hasPrefetchedRef.current = false;
        });
      }
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [onPrefetch, threshold, enabled]);
  
  return { reset: () => { hasPrefetchedRef.current = false; } };
}

/**
 * Hook to prefetch related data
 * Automatically prefetches related queries when a query succeeds
 */
export function usePrefetchRelated() {
  const queryClient = useQueryClient();
  
  return {
    /**
     * Prefetch related job data when viewing an application
     */
    prefetchJobForApplication: useCallback(async (jobId: number) => {
      await prefetchJob(queryClient, jobId, { silent: true });
    }, [queryClient]),
    
    /**
     * Prefetch related applications when viewing a job
     */
    prefetchApplicationsForJob: useCallback(async (jobId: number) => {
      // In a real implementation, this would fetch applications for a specific job
      await prefetchApplications(queryClient, { job_id: jobId }, { silent: true });
    }, [queryClient]),
    
    /**
     * Prefetch analytics when viewing dashboard
     */
    prefetchAnalytics: useCallback(async () => {
      await queryClient.prefetchQuery({
        queryKey: queryKeys.analytics.summary(),
        queryFn: async () => {
          const response = await apiClient.getAnalyticsSummary();
          if (response.error) {
            throw new Error(response.error);
          }
          return response.data;
        },
        ...getCacheConfig('ANALYTICS'),
      });
    }, [queryClient]),
  };
}

/**
 * Hook to prefetch on route change
 * Prefetches data for the next route before navigation
 */
export function usePrefetchRoute() {
  const queryClient = useQueryClient();
  
  return {
    prefetchDashboard: useCallback(async () => {
      logger.debug('Prefetching dashboard data');
      await Promise.all([
        prefetchJobs(queryClient, { skip: 0, limit: 10 }, { silent: true }),
        prefetchApplications(queryClient, { skip: 0, limit: 10 }, { silent: true }),
        queryClient.prefetchQuery({
          queryKey: queryKeys.analytics.summary(),
          queryFn: async () => {
            const response = await apiClient.getAnalyticsSummary();
            if (response.error) throw new Error(response.error);
            return response.data;
          },
          ...getCacheConfig('ANALYTICS'),
        }),
      ]);
    }, [queryClient]),
    
    prefetchJobsPage: useCallback(async () => {
      logger.debug('Prefetching jobs page data');
      await prefetchJobs(queryClient, { skip: 0, limit: 50 }, { silent: true });
    }, [queryClient]),
    
    prefetchApplicationsPage: useCallback(async () => {
      logger.debug('Prefetching applications page data');
      await prefetchApplications(queryClient, { skip: 0, limit: 50 }, { silent: true });
    }, [queryClient]),
  };
}
