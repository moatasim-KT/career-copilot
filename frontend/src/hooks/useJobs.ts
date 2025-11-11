import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';
import { queryKeys, getCacheConfig } from '@/lib/queryClient';

export interface UseJobsOptions {
  skip?: number;
  limit?: number;
  enabled?: boolean;
}

export const useJobs = (options: UseJobsOptions = {}) => {
  const { skip = 0, limit = 100, enabled = true } = options;
  
  return useQuery({
    queryKey: queryKeys.jobs.list({ skip, limit }),
    queryFn: async () => {
      const response = await apiClient.getJobs(skip, limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    enabled,
    ...getCacheConfig('JOBS'),
  });
};
