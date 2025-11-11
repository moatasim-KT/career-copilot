/**
 * Notifications Query Hooks
 * 
 * React Query-based hooks for notifications with optimized caching (30 sec stale time, refetch on focus).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';
import { queryKeys, getCacheConfig } from '@/lib/queryClient';
import { logger } from '@/lib/logger';

export interface NotificationFilters {
  skip?: number;
  limit?: number;
  category?: string;
  read?: boolean;
}

/**
 * Hook to fetch notifications
 */
export function useNotificationsQuery(filters: NotificationFilters = {}, enabled: boolean = true) {
  const { skip = 0, limit = 50 } = filters;
  
  return useQuery({
    queryKey: queryKeys.notifications.list(filters),
    queryFn: async () => {
      const response = await apiClient.getNotifications(skip, limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    enabled,
    ...getCacheConfig('NOTIFICATIONS'),
  });
}

/**
 * Hook to fetch notification preferences
 */
export function useNotificationPreferences(enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.notifications.preferences(),
    queryFn: async () => {
      const response = await apiClient.getNotificationPreferences();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    enabled,
    ...getCacheConfig('NOTIFICATIONS'),
  });
}

/**
 * Hook to mark notification as read
 */
export function useMarkNotificationAsRead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (notificationId: string) => {
      const response = await apiClient.markNotificationAsRead(notificationId);
      if (response.error) {
        throw new Error(response.error);
      }
      return notificationId;
    },
    onMutate: async (notificationId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications.all });
      
      // Snapshot previous value
      const previousNotifications = queryClient.getQueriesData({ queryKey: queryKeys.notifications.all });
      
      // Optimistically update all notification queries
      queryClient.setQueriesData({ queryKey: queryKeys.notifications.all }, (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((notification: any) =>
          notification.id === notificationId
            ? { ...notification, read: true }
            : notification
        );
      });
      
      return { previousNotifications };
    },
    onError: (err, notificationId, context) => {
      // Rollback on error
      if (context?.previousNotifications) {
        context.previousNotifications.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      logger.error('Failed to mark notification as read:', err);
    },
    onSuccess: () => {
      // Invalidate to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

/**
 * Hook to mark all notifications as read
 */
export function useMarkAllNotificationsAsRead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.markAllNotificationsAsRead();
      if (response.error) {
        throw new Error(response.error);
      }
    },
    onMutate: async () => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications.all });
      
      // Snapshot previous value
      const previousNotifications = queryClient.getQueriesData({ queryKey: queryKeys.notifications.all });
      
      // Optimistically update all notification queries
      queryClient.setQueriesData({ queryKey: queryKeys.notifications.all }, (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((notification: any) => ({ ...notification, read: true }));
      });
      
      return { previousNotifications };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousNotifications) {
        context.previousNotifications.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      logger.error('Failed to mark all notifications as read:', err);
    },
    onSuccess: () => {
      // Invalidate to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

/**
 * Hook to delete notification
 */
export function useDeleteNotification() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (notificationId: string) => {
      const response = await apiClient.deleteNotification(notificationId);
      if (response.error) {
        throw new Error(response.error);
      }
      return notificationId;
    },
    onMutate: async (notificationId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications.all });
      
      // Snapshot previous value
      const previousNotifications = queryClient.getQueriesData({ queryKey: queryKeys.notifications.all });
      
      // Optimistically update all notification queries
      queryClient.setQueriesData({ queryKey: queryKeys.notifications.all }, (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.filter((notification: any) => notification.id !== notificationId);
      });
      
      return { previousNotifications };
    },
    onError: (err, notificationId, context) => {
      // Rollback on error
      if (context?.previousNotifications) {
        context.previousNotifications.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      logger.error('Failed to delete notification:', err);
    },
    onSuccess: () => {
      // Invalidate to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

/**
 * Hook to update notification preferences
 */
export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (preferences: any) => {
      const response = await apiClient.updateNotificationPreferences(preferences);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    onSuccess: (data) => {
      // Update cache with server response
      queryClient.setQueryData(queryKeys.notifications.preferences(), data);
      logger.info('Notification preferences updated successfully');
    },
    onError: (err) => {
      logger.error('Failed to update notification preferences:', err);
    },
  });
}
