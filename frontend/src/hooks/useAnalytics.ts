/**
 * Analytics Hooks
 * 
 * Manages analytics data with optimized caching (10 min stale time, no auto-refetch).
 */

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';
import { queryKeys, getCacheConfig } from '@/lib/queryClient';

/**
 * Hook to fetch analytics summary
 */
export function useAnalyticsSummary(enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.analytics.summary(),
    queryFn: async () => {
      const response = await apiClient.getAnalyticsSummary();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    enabled,
    ...getCacheConfig('ANALYTICS'),
  });
}

/**
 * Hook to fetch comprehensive analytics
 */
export function useComprehensiveAnalytics(days: number = 90, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.analytics.comprehensive(days),
    queryFn: async () => {
      const response = await apiClient.getComprehensiveAnalytics(days);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    enabled,
    ...getCacheConfig('ANALYTICS'),
  });
}
