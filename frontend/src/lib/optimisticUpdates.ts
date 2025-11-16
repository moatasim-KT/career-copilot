/**
 * Optimistic Updates Pattern Implementation
 * 
 * This module provides utilities and patterns for implementing optimistic updates.
 * Optimistic updates improve perceived performance by updating the UI immediately
 * before the server responds, then rolling back if the request fails.
 * 
 * Key Benefits:
 * - Instant UI feedback
 * - Better user experience
 * - Reduced perceived latency
 * - Automatic rollback on errors
 */

import { useQueryClient, useMutation } from '@tanstack/react-query';

import { logger } from './logger';

/**
 * Optimistic update configuration
 */
export interface OptimisticUpdateConfig<TData, TVariables, TContext> {
  /**
   * Query key to update optimistically
   */
  queryKey: readonly unknown[];

  /**
   * Function to update the cached data optimistically
   */
  updater: (oldData: TData | undefined, variables: TVariables) => TData;

  /**
   * Optional: Additional query keys to invalidate after success
   */
  invalidateKeys?: readonly unknown[][];

  /**
   * Optional: Custom error handler
   */
  onError?: (error: Error, variables: TVariables, context: TContext | undefined) => void;

  /**
   * Optional: Custom success handler
   */
  onSuccess?: (data: any, variables: TVariables, context: TContext | undefined) => void;
}

/**
 * Create a mutation with optimistic updates
 * 
 * @example
 * ```tsx
 * const updateStatus = useOptimisticMutation({
 *   mutationFn: (data) => apiClient.updateApplication(data.id, data),
 *   queryKey: ['applications'],
 *   updater: (oldData, variables) => {
 *     return oldData.map(app =>
 *       app.id === variables.id ? { ...app, ...variables } : app
 *     );
 *   },
 * });
 * ```
 */
export function useOptimisticMutation<TData, TVariables, _TError = Error, TContext = unknown>(
  config: OptimisticUpdateConfig<TData, TVariables, TContext> & {
    mutationFn: (variables: TVariables) => Promise<any>;
  },
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: config.mutationFn,

    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: config.queryKey });

      // Snapshot previous value
      const previousData = queryClient.getQueryData<TData>(config.queryKey);

      // Optimistically update
      if (previousData !== undefined) {
        const newData = config.updater(previousData, variables);
        queryClient.setQueryData(config.queryKey, newData);
        logger.debug('Optimistic update applied', { queryKey: config.queryKey });
      }

      return { previousData } as TContext;
    },

    onError: (error, variables, context) => {
      // Rollback on error
      if (context && typeof context === 'object' && 'previousData' in context) {
        queryClient.setQueryData(config.queryKey, (context as any).previousData);
        logger.warn('Optimistic update rolled back', { queryKey: config.queryKey, error });
      }

      if (config.onError) {
        config.onError(error as Error, variables, context);
      }
    },

    onSuccess: (data, variables, context) => {
      // Update with server response
      queryClient.setQueryData(config.queryKey, data);
      logger.debug('Optimistic update confirmed', { queryKey: config.queryKey });

      // Invalidate related queries
      if (config.invalidateKeys) {
        config.invalidateKeys.forEach(key => {
          queryClient.invalidateQueries({ queryKey: key });
        });
      }

      if (config.onSuccess) {
        config.onSuccess(data, variables, context);
      }
    },

    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: config.queryKey });
    },
  });
}

/**
 * Create a mutation with optimistic updates for list items
 * Automatically handles updating items in an array
 */
export function useOptimisticListMutation<TItem extends { id: number | string }, TVariables extends { id: number | string }>(
  config: {
    mutationFn: (variables: TVariables) => Promise<TItem>;
    queryKey: readonly unknown[];
    invalidateKeys?: readonly unknown[][];
    onError?: (error: Error, variables: TVariables, context: any) => void;
    onSuccess?: (data: TItem, variables: TVariables, context: any) => void;
  },
) {
  return useOptimisticMutation<TItem[], TVariables, Error, { previousData: TItem[] | undefined }>({
    ...config,
    updater: (oldData, variables) => {
      if (!oldData) return [];
      return oldData.map(item =>
        item.id === variables.id ? { ...item, ...variables } : item,
      );
    },
  });
}

/**
 * Create a mutation with optimistic updates for adding items to a list
 */
export function useOptimisticAddMutation<TItem, TVariables>(
  config: {
    mutationFn: (variables: TVariables) => Promise<TItem>;
    queryKey: readonly unknown[];
    getOptimisticItem: (variables: TVariables) => TItem;
    invalidateKeys?: readonly unknown[][];
    onError?: (error: Error, variables: TVariables, context: any) => void;
    onSuccess?: (data: TItem, variables: TVariables, context: any) => void;
  },
) {
  return useOptimisticMutation<TItem[], TVariables, Error, { previousData: TItem[] | undefined }>({
    ...config,
    updater: (oldData, variables) => {
      const optimisticItem = config.getOptimisticItem(variables);
      return [...(oldData || []), optimisticItem];
    },
  });
}

/**
 * Create a mutation with optimistic updates for removing items from a list
 */
export function useOptimisticRemoveMutation<TItem extends { id: number | string }>(
  config: {
    mutationFn: (id: number | string) => Promise<void>;
    queryKey: readonly unknown[];
    invalidateKeys?: readonly unknown[][];
    onError?: (error: Error, id: number | string, context: any) => void;
    onSuccess?: (data: void, id: number | string, context: any) => void;
  },
) {
  return useOptimisticMutation<TItem[], number | string, Error, { previousData: TItem[] | undefined }>({
    ...config,
    updater: (oldData, id) => {
      if (!oldData) return [];
      return oldData.filter(item => item.id !== id);
    },
  });
}

/**
 * Example: Optimistic application status update
 */
export function useOptimisticApplicationStatusUpdate() {
  return useOptimisticListMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      // Simulate API call
      const response = await fetch(`/api/applications/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      return response.json();
    },
    queryKey: ['applications'],
    invalidateKeys: [['analytics']],
    onError: (error) => {
      logger.error('Failed to update application status:', error);
    },
    onSuccess: (data) => {
      logger.info('Application status updated:', data);
    },
  });
}

/**
 * Example: Optimistic job save/unsave
 */
export function useOptimisticJobSave() {
  return useOptimisticListMutation({
    mutationFn: async ({ id, saved }: { id: number; saved: boolean }) => {
      // Simulate API call
      const response = await fetch(`/api/jobs/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ saved }),
      });
      return response.json();
    },
    queryKey: ['jobs'],
    onError: (error) => {
      logger.error('Failed to save/unsave job:', error);
    },
    onSuccess: (data) => {
      logger.info('Job save status updated:', data);
    },
  });
}

/**
 * Example: Optimistic application creation
 */
export function useOptimisticCreateApplication() {
  return useOptimisticAddMutation({
    mutationFn: async (data: any) => {
      // Simulate API call
      const response = await fetch('/api/applications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return response.json();
    },
    queryKey: ['applications'],
    getOptimisticItem: (data) => ({
      ...data,
      id: Date.now(), // Temporary ID
      created_at: new Date().toISOString(),
    }),
    invalidateKeys: [['analytics']],
    onError: (error) => {
      logger.error('Failed to create application:', error);
    },
    onSuccess: (data) => {
      logger.info('Application created:', data);
    },
  });
}

/**
 * Example: Optimistic application deletion
 */
export function useOptimisticDeleteApplication() {
  return useOptimisticRemoveMutation({
    mutationFn: async (id: number | string) => {
      // Simulate API call
      await fetch(`/api/applications/${id}`, {
        method: 'DELETE',
      });
    },
    queryKey: ['applications'],
    invalidateKeys: [['analytics']],
    onError: (error) => {
      logger.error('Failed to delete application:', error);
    },
    onSuccess: () => {
      logger.info('Application deleted');
    },
  });
}

/**
 * Utility to manually perform an optimistic update
 */
export function performOptimisticUpdate<TData>(
  queryClient: any,
  queryKey: readonly unknown[],
  updater: (oldData: TData | undefined) => TData,
) {
  const previousData = queryClient.getQueryData(queryKey) as TData | undefined;
  const newData = updater(previousData);
  queryClient.setQueryData(queryKey, newData);

  logger.debug('Manual optimistic update applied', { queryKey });

  return {
    rollback: () => {
      queryClient.setQueryData(queryKey, previousData);
      logger.debug('Manual optimistic update rolled back', { queryKey });
    },
  };
}

/**
 * Hook to test optimistic updates with simulated errors
 */
export function useOptimisticUpdateTester() {
  const queryClient = useQueryClient();

  return {
    /**
     * Test optimistic update that succeeds
     */
    testSuccess: async (queryKey: readonly unknown[]) => {
      logger.info('Testing successful optimistic update', { queryKey });

      performOptimisticUpdate(
        queryClient,
        queryKey,
        (old: any) => {
          if (Array.isArray(old)) {
            return [...old, { id: Date.now(), test: true }];
          }
          return old;
        },
      );

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Success - keep the update
      logger.info('Optimistic update succeeded', { queryKey });
    },

    /**
     * Test optimistic update that fails
     */
    testFailure: async (queryKey: readonly unknown[]) => {
      logger.info('Testing failed optimistic update', { queryKey });

      const update = performOptimisticUpdate(
        queryClient,
        queryKey,
        (old: any) => {
          if (Array.isArray(old)) {
            return [...old, { id: Date.now(), test: true }];
          }
          return old;
        },
      );

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Failure - rollback
      update.rollback();
      logger.warn('Optimistic update failed and rolled back', { queryKey });
    },
  };
}
