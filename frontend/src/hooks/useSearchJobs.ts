/**
 * Search Jobs Hook
 * 
 * Provides search functionality for jobs with React Query.
 */

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';

export function useSearchJobs(query: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['jobs', 'search', query],
    queryFn: async () => {
      if (!query || query.trim().length === 0) {
        return [];
      }
      const response = await apiClient.searchJobs(query.trim(), 10);
      return response.data || [];
    },
    enabled: enabled && query.trim().length > 0,
    staleTime: 30000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
  });
}
