'use client';

import { useEffect } from 'react';
import { Toaster } from 'sonner';

import { initializeWebSocket, destroyWebSocket } from '@/lib/websocket';
import { logger } from '@/lib/logger';
import { useRealtimeJobs } from '@/hooks/useRealtimeJobs';
import { useRealtimeApplications } from '@/hooks/useRealtimeApplications';
import { useRealtimeNotifications } from '@/hooks/useRealtimeNotifications';
import { useNetworkStatus } from '@/hooks/useNetworkStatus';
import { useDataResync } from '@/hooks/useDataResync';

/**
 * RealtimeProvider Component
 * 
 * Initializes WebSocket connection and manages real-time updates
 * Should be placed high in the component tree (e.g., in layout)
 * 
 * Features:
 * - Initializes WebSocket on mount
 * - Cleans up on unmount
 * - Subscribes to all real-time events
 * - Provides toast notifications
 */

interface RealtimeProviderProps {
  children: React.ReactNode;
  enableWebSocket?: boolean;
}

export function RealtimeProvider({ 
  children, 
  enableWebSocket = true 
}: RealtimeProviderProps) {
  // Initialize real-time hooks
  useRealtimeJobs();
  useRealtimeApplications();
  useRealtimeNotifications();
  useNetworkStatus();
  useDataResync();

  useEffect(() => {
    if (!enableWebSocket) {
      logger.info('[RealtimeProvider] WebSocket disabled');
      return;
    }

    logger.info('[RealtimeProvider] Initializing WebSocket connection');

    // Initialize WebSocket connection
    const wsClient = initializeWebSocket();

    // Cleanup on unmount
    return () => {
      logger.info('[RealtimeProvider] Cleaning up WebSocket connection');
      destroyWebSocket();
    };
  }, [enableWebSocket]);

  return (
    <>
      {children}
      {/* Toast notifications container */}
      <Toaster
        position="top-right"
        expand={false}
        richColors
        closeButton
        toastOptions={{
          className: 'dark:bg-neutral-800 dark:text-neutral-100 dark:border-neutral-700',
        }}
      />
    </>
  );
}

/**
 * Hook to check if WebSocket is enabled
 */
export function useRealtimeEnabled() {
  // Could read from context or environment variable
  return process.env.NEXT_PUBLIC_ENABLE_WEBSOCKETS !== 'false';
}
