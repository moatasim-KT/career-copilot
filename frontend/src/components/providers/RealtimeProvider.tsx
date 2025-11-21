'use client';

import { useDataResync } from '@/hooks/useDataResync';
import { useNetworkStatus } from '@/hooks/useNetworkStatus';
import { useRealtimeApplications } from '@/hooks/useRealtimeApplications';
import { useRealtimeJobs } from '@/hooks/useRealtimeJobs';
import { useRealtimeNotifications } from '@/hooks/useRealtimeNotifications';
import { logger } from '@/lib/logger';

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
  enableWebSocket = true,
}: RealtimeProviderProps) {
  // Initialize real-time hooks
  useRealtimeJobs();
  useRealtimeApplications();
  useRealtimeNotifications();
  useNetworkStatus();
  useDataResync();

  // WebSocket connection is managed by AuthContext and WebSocketService singleton
  // We just initialize the hooks here to set up event listeners


  return (
    <>
      {children}
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
