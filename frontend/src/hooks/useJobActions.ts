/**
 * Job Actions Hooks
 * 
 * Hooks for job-related actions with optimistic updates.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { apiClient, type Job } from '@/lib/api/api';
import { logger } from '@/lib/logger';
import { queryKeys } from '@/lib/queryClient';

/**
 * Hook to save/bookmark a job
 * Note: This assumes there's a saved/bookmarked field on the Job type
 */
export function useSaveJob() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (jobId: number) => {
      // In a real implementation, this would call an API endpoint like:
      // const response = await apiClient.saveJob(jobId);
      // For now, we'll update the job with a saved flag
      const response = await apiClient.updateJob(jobId, { 
        // @ts-ignore - saved field may not exist on Job type yet
        saved: true, 
      });
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    onMutate: async (jobId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.jobs.all });
      
      // Snapshot previous values
      const previousJobs = queryClient.getQueriesData({ queryKey: queryKeys.jobs.all });
      
      // Optimistically update all job queries
      queryClient.setQueriesData({ queryKey: queryKeys.jobs.all }, (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((job: Job) =>
          job.id === jobId ? { ...job, saved: true } : job,
        );
      });
      
      // Also update the detail query if it exists
      const detailKey = queryKeys.jobs.detail(jobId);
      const previousDetail = queryClient.getQueryData(detailKey);
      if (previousDetail) {
        queryClient.setQueryData(detailKey, (old: Job | undefined) => {
          if (!old) return old;
          return { ...old, saved: true };
        });
      }
      
      return { previousJobs, previousDetail };
    },
    onError: (err, jobId, context) => {
      // Rollback on error
      if (context?.previousJobs) {
        context.previousJobs.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(queryKeys.jobs.detail(jobId), context.previousDetail);
      }
      logger.error('Failed to save job:', err);
    },
    onSuccess: (data) => {
      // Update cache with server response
      if (data) {
        queryClient.setQueryData(queryKeys.jobs.detail(data.id), data);
      }
      logger.info('Job saved successfully');
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
  });
}

/**
 * Hook to unsave/unbookmark a job
 */
export function useUnsaveJob() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (jobId: number) => {
      // In a real implementation, this would call an API endpoint like:
      // const response = await apiClient.unsaveJob(jobId);
      // For now, we'll update the job with a saved flag
      const response = await apiClient.updateJob(jobId, { 
        // @ts-ignore - saved field may not exist on Job type yet
        saved: false, 
      });
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    onMutate: async (jobId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.jobs.all });
      
      // Snapshot previous values
      const previousJobs = queryClient.getQueriesData({ queryKey: queryKeys.jobs.all });
      
      // Optimistically update all job queries
      queryClient.setQueriesData({ queryKey: queryKeys.jobs.all }, (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((job: Job) =>
          job.id === jobId ? { ...job, saved: false } : job,
        );
      });
      
      // Also update the detail query if it exists
      const detailKey = queryKeys.jobs.detail(jobId);
      const previousDetail = queryClient.getQueryData(detailKey);
      if (previousDetail) {
        queryClient.setQueryData(detailKey, (old: Job | undefined) => {
          if (!old) return old;
          return { ...old, saved: false };
        });
      }
      
      return { previousJobs, previousDetail };
    },
    onError: (err, jobId, context) => {
      // Rollback on error
      if (context?.previousJobs) {
        context.previousJobs.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(queryKeys.jobs.detail(jobId), context.previousDetail);
      }
      logger.error('Failed to unsave job:', err);
    },
    onSuccess: (data) => {
      // Update cache with server response
      if (data) {
        queryClient.setQueryData(queryKeys.jobs.detail(data.id), data);
      }
      logger.info('Job unsaved successfully');
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
  });
}

/**
 * Hook to toggle job save status
 */
export function useToggleJobSave() {
  const saveJob = useSaveJob();
  const unsaveJob = useUnsaveJob();
  
  return {
    toggleSave: (jobId: number, currentlySaved: boolean) => {
      if (currentlySaved) {
        return unsaveJob.mutate(jobId);
      } else {
        return saveJob.mutate(jobId);
      }
    },
    isLoading: saveJob.isPending || unsaveJob.isPending,
    error: saveJob.error || unsaveJob.error,
  };
}
