'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { logger } from '@/lib/logger';
import { webSocketService } from '@/lib/api/websocket';

/**
 * Hook to monitor network status and handle reconnection
 * 
 * Features:
 * - Detect online/offline events
 * - Show reconnecting toast
 * - Retry connection with exponential backoff
 * - Resync data on reconnect
 * - Handle message queue for missed events
 */

export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof window !== 'undefined' ? navigator.onLine : true,
  );
  const [isReconnecting, setIsReconnecting] = useState(false);
  useEffect(() => {
    let reconnectToastId: string | number | undefined;

    // Handle online event
    const handleOnline = () => {
      logger.info('[Network] Network online');
      setIsOnline(true);
      setIsReconnecting(true);

      // Show reconnecting toast
      reconnectToastId = toast.loading('Reconnecting...', {
        description: 'Restoring real-time connection',
      });

      // Attempt to reconnect WebSocket
      if (webSocketService.getStatus() !== 'connected') {
        webSocketService.reconnect().catch(err => {
          logger.error('Reconnection failed:', err);
        });
      }
    };

    // Handle offline event
    const handleOffline = () => {
      logger.info('[Network] Network offline');
      setIsOnline(false);
      setIsReconnecting(false);

      // Show offline toast
      toast.error('Connection Lost', {
        description: 'Real-time updates are temporarily unavailable.',
        duration: Infinity, // Keep showing until online
        id: 'network-offline',
      });
    };

    // Listen for WebSocket status changes
    const handleConnected = () => {
      if (isReconnecting) {
        setIsReconnecting(false);

        // Dismiss reconnecting toast
        if (reconnectToastId) {
          toast.dismiss(reconnectToastId);
        }

        // Show success toast
        toast.success('Reconnected', {
          description: 'Real-time updates restored',
          duration: 3000,
        });

        // Dismiss offline toast if it exists
        toast.dismiss('network-offline');

        // Trigger data resync
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('websocket:reconnected'));
        }
      }
    };

    const handleReconnecting = () => {
      setIsReconnecting(true);

      if (!reconnectToastId) {
        reconnectToastId = toast.loading('Reconnecting...', {
          description: 'Attempting to restore connection',
        });
      }
    };

    const handleDisconnected = () => {
      if (isOnline) {
        // Disconnected but network is online - show warning
        toast.warning('Connection Issue', {
          description: 'Reconnecting automatically...',
          duration: 5000,
          id: 'network-warning',
        });
      }
    };

    webSocketService.on('connected', handleConnected);
    webSocketService.on('reconnecting', handleReconnecting);
    webSocketService.on('disconnected', handleDisconnected);

    // Add event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check initial state
    if (!navigator.onLine) {
      handleOffline();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);

      webSocketService.off('connected', handleConnected);
      webSocketService.off('reconnecting', handleReconnecting);
      webSocketService.off('disconnected', handleDisconnected);

      // Clean up toasts
      if (reconnectToastId) {
        toast.dismiss(reconnectToastId);
      }
      toast.dismiss('network-offline');
      toast.dismiss('network-warning');
    };
  }, [isReconnecting, isOnline]);

  return {
    isOnline,
    isReconnecting,
  };
}
