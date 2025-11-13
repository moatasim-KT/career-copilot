import { useQuery } from '@tanstack/react-query';

import { JobsService } from '../lib/api/client';

export interface UseJobsOptions {
  skip?: number;
  limit?: number;
  enabled?: boolean;
}

export const useJobs = (options: UseJobsOptions = {}) => {
  const { skip = 0, limit = 100, enabled = true } = options;

  return useQuery({
    queryKey: ['jobs', { skip, limit }],
    queryFn: async () => {
      const response = await JobsService.list({ skip, limit });
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    enabled,
  });
};
