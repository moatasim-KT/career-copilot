/**
 * Search Jobs Hook
 * 
 * Provides search functionality for jobs with React Query.
 */

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';
import { queryKeys, getCacheConfig } from '@/lib/queryClient';

export function useSearchJobs(query: string, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.jobs.search(query),
    queryFn: async () => {
      if (!query || query.trim().length === 0) {
        return [];
      }
      const response = await apiClient.searchJobs(query.trim(), 10);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    enabled: enabled && query.trim().length > 0,
    ...getCacheConfig('SEARCH'),
  });
}
