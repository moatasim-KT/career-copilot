import { useMutation, useQueryClient } from '@tanstack/react-query';

import { ApplicationsService } from '../lib/api/client';

export const useDeleteApplication = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => ApplicationsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
};
