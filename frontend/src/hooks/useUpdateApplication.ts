import { useMutation, useQueryClient } from '@tanstack/react-query';

import { apiClient, type Application } from '@/lib/api/api';
import { queryKeys } from '@/lib/queryClient';
import { logger } from '@/lib/logger';

export const useUpdateApplication = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Application> }) => {
      const response = await apiClient.updateApplication(id, data);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.applications.all });
      
      // Snapshot previous values
      const previousApplications = queryClient.getQueriesData({ queryKey: queryKeys.applications.all });
      
      // Optimistically update all application queries
      queryClient.setQueriesData({ queryKey: queryKeys.applications.all }, (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((app: Application) =>
          app.id === id ? { ...app, ...data } : app
        );
      });
      
      // Also update the detail query if it exists
      const detailKey = queryKeys.applications.detail(id);
      const previousDetail = queryClient.getQueryData(detailKey);
      if (previousDetail) {
        queryClient.setQueryData(detailKey, (old: Application | undefined) => {
          if (!old) return old;
          return { ...old, ...data };
        });
      }
      
      return { previousApplications, previousDetail };
    },
    onError: (err, { id }, context) => {
      // Rollback on error
      if (context?.previousApplications) {
        context.previousApplications.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(queryKeys.applications.detail(id), context.previousDetail);
      }
      logger.error('Failed to update application:', err);
    },
    onSuccess: (data) => {
      // Update cache with server response
      queryClient.setQueryData(queryKeys.applications.detail(data.id), data);
      logger.info('Application updated successfully');
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.applications.all });
    },
  });
};
