/**
 * Optimistic Updates Tests
 * 
 * Tests for optimistic update patterns including success and error scenarios.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

import {
  useOptimisticMutation,
  useOptimisticListMutation,
  useOptimisticAddMutation,
  useOptimisticRemoveMutation,
  performOptimisticUpdate,
} from '@/lib/optimisticUpdates';

// Create a test query client
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

// Wrapper component for hooks
function createWrapper(queryClient: QueryClient) {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
  return Wrapper;
}

describe('Optimistic Updates', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
  });

  describe('useOptimisticMutation', () => {
    it('should apply optimistic update immediately', async () => {
      const queryKey = ['test-data'];
      const initialData = [{ id: 1, name: 'Item 1' }];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const { result } = renderHook(
        () => useOptimisticMutation({
          mutationFn: async (variables: { id: number; name: string }) => {
            await new Promise(resolve => setTimeout(resolve, 100));
            return { id: variables.id, name: variables.name };
          },
          queryKey,
          updater: (oldData: any, variables) => {
            return oldData.map((item: any) =>
              item.id === variables.id ? { ...item, ...variables } : item
            );
          },
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate({ id: 1, name: 'Updated Item 1' });

      // Check that data was updated optimistically
      const cachedData = queryClient.getQueryData(queryKey);
      expect(cachedData).toEqual([{ id: 1, name: 'Updated Item 1' }]);
    });

    it('should rollback on error', async () => {
      const queryKey = ['test-data'];
      const initialData = [{ id: 1, name: 'Item 1' }];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const { result } = renderHook(
        () => useOptimisticMutation({
          mutationFn: async () => {
            throw new Error('API Error');
          },
          queryKey,
          updater: (oldData: any, variables: any) => {
            return oldData.map((item: any) =>
              item.id === variables.id ? { ...item, ...variables } : item
            );
          },
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate({ id: 1, name: 'Updated Item 1' });

      // Wait for error
      await waitFor(() => expect(result.current.isError).toBe(true));

      // Check that data was rolled back
      const cachedData = queryClient.getQueryData(queryKey);
      expect(cachedData).toEqual(initialData);
    });
  });

  describe('useOptimisticListMutation', () => {
    it('should update item in list optimistically', async () => {
      const queryKey = ['items'];
      const initialData = [
        { id: 1, name: 'Item 1', status: 'pending' },
        { id: 2, name: 'Item 2', status: 'pending' },
      ];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const { result } = renderHook(
        () => useOptimisticListMutation({
          mutationFn: async (variables: { id: number; status: string }) => {
            await new Promise(resolve => setTimeout(resolve, 100));
            return { id: variables.id, name: `Item ${variables.id}`, status: variables.status };
          },
          queryKey,
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate({ id: 1, status: 'completed' });

      // Check that item was updated optimistically
      const cachedData = queryClient.getQueryData(queryKey) as any[];
      expect(cachedData[0].status).toBe('completed');
      expect(cachedData[1].status).toBe('pending');
    });
  });

  describe('useOptimisticAddMutation', () => {
    it('should add item to list optimistically', async () => {
      const queryKey = ['items'];
      const initialData = [
        { id: 1, name: 'Item 1' },
      ];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const { result } = renderHook(
        () => useOptimisticAddMutation({
          mutationFn: async (variables: { name: string }) => {
            await new Promise(resolve => setTimeout(resolve, 100));
            return { id: 2, name: variables.name };
          },
          queryKey,
          getOptimisticItem: (variables) => ({
            id: Date.now(),
            name: variables.name,
          }),
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate({ name: 'Item 2' });

      // Check that item was added optimistically
      const cachedData = queryClient.getQueryData(queryKey) as any[];
      expect(cachedData).toHaveLength(2);
      expect(cachedData[1].name).toBe('Item 2');
    });
  });

  describe('useOptimisticRemoveMutation', () => {
    it('should remove item from list optimistically', async () => {
      const queryKey = ['items'];
      const initialData = [
        { id: 1, name: 'Item 1' },
        { id: 2, name: 'Item 2' },
      ];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const { result } = renderHook(
        () => useOptimisticRemoveMutation({
          mutationFn: async (id: number | string) => {
            await new Promise(resolve => setTimeout(resolve, 100));
          },
          queryKey,
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate(1);

      // Check that item was removed optimistically
      const cachedData = queryClient.getQueryData(queryKey) as any[];
      expect(cachedData).toHaveLength(1);
      expect(cachedData[0].id).toBe(2);
    });
  });

  describe('performOptimisticUpdate', () => {
    it('should perform manual optimistic update', () => {
      const queryKey = ['test-data'];
      const initialData = { count: 0 };

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      // Perform optimistic update
      const { rollback } = performOptimisticUpdate(
        queryClient,
        queryKey,
        (old: any) => ({ count: old.count + 1 })
      );

      // Check that data was updated
      const cachedData = queryClient.getQueryData(queryKey);
      expect(cachedData).toEqual({ count: 1 });

      // Rollback
      rollback();

      // Check that data was rolled back
      const rolledBackData = queryClient.getQueryData(queryKey);
      expect(rolledBackData).toEqual(initialData);
    });
  });

  describe('Error scenarios', () => {
    it('should handle network errors gracefully', async () => {
      const queryKey = ['test-data'];
      const initialData = [{ id: 1, name: 'Item 1' }];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const onError = vi.fn();

      const { result } = renderHook(
        () => useOptimisticListMutation({
          mutationFn: async () => {
            throw new Error('Network error');
          },
          queryKey,
          onError,
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate({ id: 1, name: 'Updated' });

      // Wait for error
      await waitFor(() => expect(result.current.isError).toBe(true));

      // Check that error handler was called
      expect(onError).toHaveBeenCalled();

      // Check that data was rolled back
      const cachedData = queryClient.getQueryData(queryKey);
      expect(cachedData).toEqual(initialData);
    });

    it('should handle server errors gracefully', async () => {
      const queryKey = ['test-data'];
      const initialData = [{ id: 1, status: 'pending' }];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const { result } = renderHook(
        () => useOptimisticListMutation({
          mutationFn: async () => {
            throw new Error('Server error: 500');
          },
          queryKey,
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate({ id: 1 });

      // Wait for error
      await waitFor(() => expect(result.current.isError).toBe(true));

      // Check that data was rolled back
      const cachedData = queryClient.getQueryData(queryKey);
      expect(cachedData).toEqual(initialData);
    });
  });

  describe('Success scenarios', () => {
    it('should update cache with server response on success', async () => {
      const queryKey = ['test-data'];
      const initialData = [{ id: 1, name: 'Item 1', version: 1 }];
      const serverResponse = [{ id: 1, name: 'Updated Item 1', version: 2 }];

      // Set initial data
      queryClient.setQueryData(queryKey, initialData);

      const { result } = renderHook(
        () => useOptimisticMutation({
          mutationFn: async () => {
            await new Promise(resolve => setTimeout(resolve, 100));
            return serverResponse;
          },
          queryKey,
          updater: (oldData: any, variables: any) => {
            return oldData.map((item: any) =>
              item.id === variables.id ? { ...item, ...variables } : item
            );
          },
        }),
        { wrapper: createWrapper(queryClient) }
      );

      // Trigger mutation
      result.current.mutate({ id: 1, name: 'Updated Item 1' });

      // Wait for success
      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Check that cache was updated with server response
      const cachedData = queryClient.getQueryData(queryKey);
      expect(cachedData).toEqual(serverResponse);
    });
  });
});
