/**
 * React hook for managing WebSocket connections and real-time updates
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { webSocketService, type WebSocketMessage } from '@/lib/websocket';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  reconnectAttempts: number;
}

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
    } catch (error) {
      setState(prev => ({
        ...prev,
        connected: false,
        connecting: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      }));
      onError?.(error);
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
    (eventType: string, callback: (data: WebSocketMessage) => void) => {
      eventListenersRef.current.set(eventType, callback);
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
    if (!isInitializedRef.current && autoConnect) {
      isInitializedRef.current = true;
      connect();
    }

    // Set up global message listener
    if (onMessage) {
      webSocketService.on('message', onMessage);
    }

    return () => {
      // Clean up event listeners
      eventListenersRef.current.forEach((callback, eventType) => {
        webSocketService.off(eventType, callback);
      });
      eventListenersRef.current.clear();

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
export function useJobMatchNotifications(onJobMatch?: (data: any) => void) {
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
export function useApplicationStatusUpdates(onStatusUpdate?: (data: any) => void) {
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
export function useAnalyticsUpdates(onAnalyticsUpdate?: (data: any) => void) {
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
export function useSystemNotifications(onSystemNotification?: (data: any) => void) {
  const { subscribe, unsubscribe } = useWebSocket({ autoConnect: false });

  useEffect(() => {
    if (onSystemNotification) {
      subscribe('system_notification', onSystemNotification);
      return () => unsubscribe('system_notification');
    }
  }, [subscribe, unsubscribe, onSystemNotification]);
}
