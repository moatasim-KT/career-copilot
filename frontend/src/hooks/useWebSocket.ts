/**
 * React hook for managing WebSocket connections and real-time updates
 *
 * Note: ESLint flags parameter names in function type signatures as "unused",
 * but these are necessary for TypeScript type documentation and IntelliSense.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { webSocketService, type WebSocketMessage } from '@/lib/websocket';

// Parameter names in type signatures provide documentation - not actual unused vars
/* eslint-disable @typescript-eslint/no-unused-vars */
export interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (_error: unknown) => void;
  onMessage?: (message: WebSocketMessage) => void;
}
/* eslint-enable @typescript-eslint/no-unused-vars */

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  reconnectAttempts: number;
}

// eslint-disable-next-line max-lines-per-function
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { autoConnect = true, onConnect, onDisconnect, onError, onMessage } = options;

  const [state, setState] = useState<WebSocketState>({
    connected: false,
    connecting: false,
    error: null,
    reconnectAttempts: 0,
  });

  const eventListenersRef = useRef<Map<string, (data: WebSocketMessage) => void>>(
    new Map(),
  );
  const isInitializedRef = useRef(false);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(async () => {
    const token = localStorage.getItem('auth_token') ?? 'guest';

    setState(prev => ({ ...prev, connecting: true, error: null }));

    try {
      await webSocketService.connect(token);
      setState(prev => ({
        ...prev,
        connected: true,
        connecting: false,
        error: null,
        reconnectAttempts: 0,
      }));
      onConnect?.();
    } catch (err) {
      setState(prev => ({
        ...prev,
        connected: false,
        connecting: false,
        error: err instanceof Error ? err.message : 'Connection failed',
      }));
      onError?.(err);
    }
  }, [onConnect, onError]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    webSocketService.disconnect();
    setState(prev => ({
      ...prev,
      connected: false,
      connecting: false,
      reconnectAttempts: 0,
    }));
    onDisconnect?.();
  }, [onDisconnect]);

  /**
   * Subscribe to a specific event type
   */
  const subscribe = useCallback(
    (eventType: string, callback: (message: WebSocketMessage) => void) => {
      // Store callback for cleanup
      eventListenersRef.current.set(eventType, callback);
      // Register with service
      webSocketService.on(eventType, callback);
    },
    [],
  );

  /**
   * Unsubscribe from a specific event type
   */
  const unsubscribe = useCallback((eventType: string) => {
    const callback = eventListenersRef.current.get(eventType);
    if (callback) {
      webSocketService.off(eventType, callback);
      eventListenersRef.current.delete(eventType);
    }
  }, []);

  /**
   * Subscribe to a notification channel
   */
  const subscribeToChannel = useCallback((channel: string) => {
    webSocketService.subscribeToChannel(channel);
  }, []);

  /**
   * Unsubscribe from a notification channel
   */
  const unsubscribeFromChannel = useCallback((channel: string) => {
    webSocketService.unsubscribeFromChannel(channel);
  }, []);

  /**
   * Get current connection info
   */
  const getConnectionInfo = useCallback(() => {
    return webSocketService.getConnectionInfo();
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    // Capture current listeners at effect execution time
    const listeners = eventListenersRef.current;

    if (!isInitializedRef.current && autoConnect) {
      isInitializedRef.current = true;
      connect();
    }

    // Set up global message listener
    if (onMessage) {
      webSocketService.on('message', onMessage);
    }

    return () => {
      // Clean up event listeners using captured value
      listeners.forEach((callback, eventType) => {
        webSocketService.off(eventType, callback);
      });
      listeners.clear();

      if (onMessage) {
        webSocketService.off('message', onMessage);
      }
    };
  }, [autoConnect, connect, onMessage]);

  // Update state based on connection info
  useEffect(() => {
    const interval = setInterval(() => {
      const info = webSocketService.getConnectionInfo();
      setState(prev => ({
        ...prev,
        connected: info.connected,
        reconnectAttempts: info.reconnectAttempts,
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    subscribeToChannel,
    unsubscribeFromChannel,
    getConnectionInfo,
  };
}

/**
 * Hook for job match notifications
 */
export function useJobMatchNotifications(onJobMatch?: (data: WebSocketMessage) => void) {
  const { subscribe, unsubscribe } = useWebSocket({ autoConnect: false });

  useEffect(() => {
    if (onJobMatch) {
      subscribe('job_match', onJobMatch);
      return () => unsubscribe('job_match');
    }
  }, [subscribe, unsubscribe, onJobMatch]);
}

/**
 * Hook for application status updates
 */
export function useApplicationStatusUpdates(onStatusUpdate?: (data: WebSocketMessage) => void) {
  const { subscribe, unsubscribe } = useWebSocket({ autoConnect: false });

  useEffect(() => {
    if (onStatusUpdate) {
      subscribe('application_status_update', onStatusUpdate);
      return () => unsubscribe('application_status_update');
    }
  }, [subscribe, unsubscribe, onStatusUpdate]);
}

/**
 * Hook for analytics updates
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function useAnalyticsUpdates(onAnalyticsUpdate?: (data: WebSocketMessage) => void) {
  const { subscribe, unsubscribe } = useWebSocket({ autoConnect: false });

  useEffect(() => {
    if (onAnalyticsUpdate) {
      subscribe('analytics_update', onAnalyticsUpdate);
      return () => unsubscribe('analytics_update');
    }
  }, [subscribe, unsubscribe, onAnalyticsUpdate]);
}

/**
 * Hook for system notifications
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function useSystemNotifications(onSystemNotification?: (data: WebSocketMessage) => void) {
  const { subscribe, unsubscribe } = useWebSocket({ autoConnect: false });

  useEffect(() => {
    if (onSystemNotification) {
      subscribe('system_notification', onSystemNotification);
      return () => unsubscribe('system_notification');
    }
  }, [subscribe, unsubscribe, onSystemNotification]);
}
