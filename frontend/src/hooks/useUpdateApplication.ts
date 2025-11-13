import { useMutation, useQueryClient } from '@tanstack/react-query';

import { ApplicationsService } from '../lib/api/client';

export const useUpdateApplication = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => ApplicationsService.update(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      // Optionally, update a single application in the cache
      queryClient.setQueryData(['application', variables.id], data);
    },
  });
};
