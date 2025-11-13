import { useMutation, useQueryClient } from '@tanstack/react-query';

import { ApplicationsService } from '../lib/api/client';

export const useAddApplication = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ApplicationsService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
};
