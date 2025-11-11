import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';
import { queryKeys, getCacheConfig } from '@/lib/queryClient';

export interface UseApplicationsOptions {
  skip?: number;
  limit?: number;
  enabled?: boolean;
}

export const useApplications = (options: UseApplicationsOptions = {}) => {
  const { skip = 0, limit = 100, enabled = true } = options;
  
  return useQuery({
    queryKey: queryKeys.applications.list({ skip, limit }),
    queryFn: async () => {
      const response = await apiClient.getApplications(skip, limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    enabled,
    ...getCacheConfig('APPLICATIONS'),
  });
};
