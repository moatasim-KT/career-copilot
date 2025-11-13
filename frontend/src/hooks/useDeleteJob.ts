import { useMutation, useQueryClient } from '@tanstack/react-query';

import { JobsService } from '../lib/api/client';

export const useDeleteJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => JobsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
