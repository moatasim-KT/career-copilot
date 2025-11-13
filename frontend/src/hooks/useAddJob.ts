import { useMutation, useQueryClient } from '@tanstack/react-query';
import { JobsService } from '../lib/api/client';

export const useAddJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: JobsService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
