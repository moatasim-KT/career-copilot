'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { getWebSocketClient } from '@/lib/websocket';
import { logger } from '@/lib/logger';

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
    typeof window !== 'undefined' ? navigator.onLine : true
  );
  const [isReconnecting, setIsReconnecting] = useState(false);

  useEffect(() => {
    const wsClient = getWebSocketClient();
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
      if (!wsClient.isConnected()) {
        wsClient.connect();
      }
    };

    // Handle offline event
    const handleOffline = () => {
      logger.info('[Network] Network offline');
      setIsOnline(false);
      setIsReconnecting(false);

      // Show offline toast
      toast.error('Connection Lost', {
        description: 'You are currently offline. Some features may be unavailable.',
        duration: Infinity, // Keep showing until online
        id: 'offline-toast',
      });
    };

    // Listen for WebSocket status changes
    const unsubscribeStatus = wsClient.onStatusChange((status) => {
      if (status === 'connected' && isReconnecting) {
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
        toast.dismiss('offline-toast');

        // Trigger data resync
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('websocket:reconnected'));
        }
      } else if (status === 'reconnecting') {
        setIsReconnecting(true);

        if (!reconnectToastId) {
          reconnectToastId = toast.loading('Reconnecting...', {
            description: 'Attempting to restore connection',
          });
        }
      } else if (status === 'disconnected' && isOnline) {
        // Disconnected but network is online - show warning
        toast.warning('Connection Issue', {
          description: 'Having trouble connecting. Will retry automatically.',
          duration: 5000,
        });
      }
    });

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
      unsubscribeStatus();

      // Clean up toasts
      if (reconnectToastId) {
        toast.dismiss(reconnectToastId);
      }
      toast.dismiss('offline-toast');
    };
  }, [isReconnecting, isOnline]);

  return {
    isOnline,
    isReconnecting,
  };
}
