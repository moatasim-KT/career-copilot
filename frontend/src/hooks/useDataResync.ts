'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import { logger } from '@/lib/logger';

/**
 * Hook to handle data resync after WebSocket reconnection
 * 
 * Listens for reconnection events and invalidates queries
 * to fetch the latest data from the server
 */

export function useDataResync() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const handleReconnect = () => {
      logger.info('[Data Resync] WebSocket reconnected, resyncing data');

      // Invalidate all queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });

      logger.info('[Data Resync] Data resync triggered');
    };

    // Listen for reconnection event
    window.addEventListener('websocket:reconnected', handleReconnect);

    return () => {
      window.removeEventListener('websocket:reconnected', handleReconnect);
    };
  }, [queryClient]);
}
