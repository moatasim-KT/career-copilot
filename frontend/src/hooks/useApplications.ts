import { useQuery } from '@tanstack/react-query';

import { ApplicationsService } from '../lib/api/client';

export interface UseApplicationsOptions {
  skip?: number;
  limit?: number;
  enabled?: boolean;
}

export const useApplications = (options: UseApplicationsOptions = {}) => {
  const { skip = 0, limit = 100, enabled = true } = options;

  return useQuery({
    queryKey: ['applications', { skip, limit }],
    queryFn: async () => {
      const response = await ApplicationsService.list({ skip, limit });
      if (response.error) {
        throw new Error(response.error.message);
      }
      return response.data || [];
    },
    enabled,
  });
};
