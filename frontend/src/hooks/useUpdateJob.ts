import { useMutation, useQueryClient } from '@tanstack/react-query';

import { JobsService } from '../lib/api/client';

export const useUpdateJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => JobsService.update(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      // Optionally, update a single job in the cache
      queryClient.setQueryData(['job', variables.id], data);
    },
  });
};
