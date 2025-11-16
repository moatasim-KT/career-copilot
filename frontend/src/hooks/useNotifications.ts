/**
 * useNotifications Hook
 * Manages notification state and actions
 */

'use client';

import { useState, useCallback, useEffect } from 'react';

import { logger } from '@/lib/logger';
import type { Notification, NotificationFilter } from '@/types/notification';

interface UseNotificationsOptions {
  autoFetch?: boolean;
  pollInterval?: number;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: Error | null;
  markAsRead: (id: string) => Promise<void>;
  markAsUnread: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: string) => Promise<void>;
  deleteMultiple: (ids: string[]) => Promise<void>;
  fetchNotifications: (filter?: NotificationFilter) => Promise<void>;
  refresh: () => Promise<void>;
}

/**
 * Hook for managing notifications
 */
export function useNotifications(
  options: UseNotificationsOptions = {},
): UseNotificationsReturn {
  const { autoFetch = true, pollInterval } = options;

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  /**
   * Fetch notifications from API
   */
  const fetchNotifications = useCallback(async (filter?: NotificationFilter) => {
    setIsLoading(true);
    setError(null);

    try {
      // In production, this would call the API:
      // const response = await apiClient.getNotifications(filter);
      // setNotifications(response.data || []);

      // For now, using mock data
      logger.info('Fetching notifications with filter:', filter);

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock data would be replaced with actual API call
      setIsLoading(false);
    } catch (err) {
      logger.error('Error fetching notifications:', err);
      setError(err as Error);
      setIsLoading(false);
    }
  }, []);

  /**
   * Mark a notification as read
   */
  const markAsRead = useCallback(async (id: string) => {
    try {
      // Optimistic update
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, read: true } : n)),
      );

      // In production, call API:
      // await apiClient.markNotificationAsRead(id);

      logger.info('Marked notification as read:', id);
    } catch (err) {
      logger.error('Error marking notification as read:', err);

      // Rollback on error
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, read: false } : n)),
      );

      throw err;
    }
  }, []);

  /**
   * Mark a notification as unread
   */
  const markAsUnread = useCallback(async (id: string) => {
    try {
      // Optimistic update
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, read: false } : n)),
      );

      // In production, call API:
      // await apiClient.markNotificationAsUnread(id);

      logger.info('Marked notification as unread:', id);
    } catch (err) {
      logger.error('Error marking notification as unread:', err);

      // Rollback on error
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, read: true } : n)),
      );

      throw err;
    }
  }, []);

  /**
   * Mark all notifications as read
   */
  const markAllAsRead = useCallback(async () => {
    // Store previous state for rollback
    const previousNotifications = notifications;

    try {
      // Optimistic update
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));

      // In production, call API:
      // await apiClient.markAllNotificationsAsRead();

      logger.info('Marked all notifications as read');
    } catch (err) {
      logger.error('Error marking all notifications as read:', err);

      // Rollback on error
      setNotifications(previousNotifications);

      throw err;
    }
  }, [notifications]);

  /**
   * Delete a notification
   */
  const deleteNotification = useCallback(async (id: string) => {
    const previousNotifications = notifications;

    try {
      // Optimistic update
      setNotifications(prev => prev.filter(n => n.id !== id));

      // In production, call API:
      // await apiClient.deleteNotification(id);

      logger.info('Deleted notification:', id);
    } catch (err) {
      logger.error('Error deleting notification:', err);

      // Rollback on error
      setNotifications(previousNotifications);
      throw err;
    }
  }, [notifications]);

  /**
   * Delete multiple notifications
   */
  const deleteMultiple = useCallback(async (ids: string[]) => {
    const previousNotifications = notifications;

    try {
      // Optimistic update
      setNotifications(prev => prev.filter(n => !ids.includes(n.id)));

      // In production, call API:
      // await apiClient.deleteNotifications(ids);

      logger.info('Deleted notifications:', ids);
    } catch (err) {
      logger.error('Error deleting notifications:', err);

      // Rollback on error
      setNotifications(previousNotifications);
      throw err;
    }
  }, [notifications]);

  /**
   * Refresh notifications
   */
  const refresh = useCallback(async () => {
    await fetchNotifications();
  }, [fetchNotifications]);

  /**
   * Auto-fetch on mount
   */
  useEffect(() => {
    if (autoFetch) {
      fetchNotifications();
    }
  }, [autoFetch, fetchNotifications]);

  /**
   * Poll for new notifications
   */
  useEffect(() => {
    if (pollInterval && pollInterval > 0) {
      const interval = setInterval(() => {
        fetchNotifications();
      }, pollInterval);

      return () => clearInterval(interval);
    }
  }, [pollInterval, fetchNotifications]);

  return {
    notifications,
    unreadCount,
    isLoading,
    error,
    markAsRead,
    markAsUnread,
    markAllAsRead,
    deleteNotification,
    deleteMultiple,
    fetchNotifications,
    refresh,
  };
}

/**
 * Hook for a single notification
 */
export function useNotification(id: string) {
  const {
    notifications,
    markAsRead,
    markAsUnread,
    deleteNotification,
  } = useNotifications();

  const notification = notifications.find(n => n.id === id);

  return {
    notification,
    markAsRead: () => markAsRead(id),
    markAsUnread: () => markAsUnread(id),
    deleteNotification: () => deleteNotification(id),
  };
}
