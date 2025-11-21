'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useCallback } from 'react';
import { toast } from 'sonner';

import { logger } from '@/lib/logger';
import { webSocketService } from '@/lib/api/websocket';

/**
 * Hook for real-time notifications via WebSocket
 * 
 * Features:
 * - Listen for new notifications
 * - Display toast notifications
 * - Update notification bell badge count
 * - Add to notification center list
 * - Play sound (with user preference)
 */

interface NotificationEvent {
  id: string;
  category: 'system' | 'job_alert' | 'application' | 'recommendation' | 'social';
  title: string;
  description: string;
  timestamp: string;
  actionUrl?: string;
  actionLabel?: string;
  metadata?: Record<string, any>;
}

interface NotificationPreferences {
  soundEnabled?: boolean;
  categories?: Record<string, boolean>;
}

// Simple notification sound (can be replaced with actual audio file)
const playNotificationSound = () => {
  if (typeof window === 'undefined') return;

  try {
    // Create a simple beep sound using Web Audio API
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.3);
  } catch (error) {
    logger.error('[Realtime Notifications] Failed to play sound:', error);
  }
};

export function useRealtimeNotifications() {
  const queryClient = useQueryClient();

  const handleNewNotification = useCallback((data: NotificationEvent) => {
    logger.info('[Realtime Notifications] New notification received:', data);

    // Get user preferences from localStorage
    const prefsStr = localStorage.getItem('notificationPreferences');
    const prefs: NotificationPreferences = prefsStr ? JSON.parse(prefsStr) : {};

    // Check if category is enabled
    const categoryEnabled = prefs.categories?.[data.category] !== false;
    if (!categoryEnabled) {
      logger.debug(`[Realtime Notifications] Category ${data.category} is disabled`);
      return;
    }

    // Play sound if enabled
    if (prefs.soundEnabled) {
      playNotificationSound();
    }

    // Show toast notification
    const toastOptions: any = {
      description: data.description,
      duration: 5000,
    };

    // Add action button if provided
    if (data.actionUrl && data.actionLabel) {
      const actionUrl = data.actionUrl;
      toastOptions.action = {
        label: data.actionLabel,
        onClick: () => {
          window.location.href = actionUrl;
        },
      };
    }

    // Show toast based on category
    switch (data.category) {
      case 'system':
        toast.info(data.title, toastOptions);
        break;
      case 'job_alert':
      case 'recommendation':
        toast.success(data.title, toastOptions);
        break;
      case 'application':
        toast(data.title, toastOptions);
        break;
      default:
        toast(data.title, toastOptions);
    }

    // Update notification count in cache
    queryClient.setQueryData<number>(
      ['notifications', 'unread-count'],
      (old) => (old || 0) + 1,
    );

    // Invalidate notifications query to trigger refetch
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
  }, [queryClient]);

  useEffect(() => {
    // Subscribe to new notification events
    const onNewNotification = (data: any) => {
      handleNewNotification(data as NotificationEvent);
    };

    webSocketService.on('notification:new', onNewNotification);

    return () => {
      webSocketService.off('notification:new', onNewNotification);
    };
  }, [handleNewNotification]);

  return {
    // Could expose additional functionality here if needed
  };
}
