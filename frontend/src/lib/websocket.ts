/**
 * WebSocket Client for Real-time Updates
 * 
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Event subscription system
 * - Message queue for offline mode
 * - Connection lifecycle management
 * - Type-safe event handling
 */

import { logger } from './logger';

// ============================================================================
// Types
// ============================================================================

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'reconnecting';

export interface WebSocketEvent<T = any> {
  type: string;
  data: T;
  timestamp: Date;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  maxReconnectAttempts?: number;
  timeoutInterval?: number;
  enableMessageQueue?: boolean;
  maxQueueSize?: number;
}

export type EventHandler<T = any> = (data: T) => void;

interface QueuedMessage {
  event: string;
  data: any;
  timestamp: Date;
}

// ============================================================================
// WebSocket Client Class
// ============================================================================

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private status: ConnectionStatus = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private heartbeatIntervalId: NodeJS.Timeout | null = null;
  private eventHandlers: Map<string, Set<EventHandler>> = new Map();
  private messageQueue: QueuedMessage[] = [];
  private isManualDisconnect = false;

  // Status change listeners
  private statusChangeListeners: Set<(status: ConnectionStatus) => void> = new Set();

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval ?? 1000,
      maxReconnectInterval: config.maxReconnectInterval ?? 30000,
      reconnectDecay: config.reconnectDecay ?? 1.5,
      maxReconnectAttempts: config.maxReconnectAttempts ?? Infinity,
      timeoutInterval: config.timeoutInterval ?? 5000,
      enableMessageQueue: config.enableMessageQueue ?? true,
      maxQueueSize: config.maxQueueSize ?? 100,
    };

    // Listen for online/offline events
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleOnline);
      window.addEventListener('offline', this.handleOffline);
    }
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      logger.warn('[WebSocket] Already connected or connecting');
      return;
    }

    this.isManualDisconnect = false;
    this.setStatus('connecting');

    try {
      logger.info(`[WebSocket] Connecting to ${this.config.url}`);
      this.ws = new WebSocket(this.config.url);

      this.ws.onopen = this.handleOpen;
      this.ws.onclose = this.handleClose;
      this.ws.onerror = this.handleError;
      this.ws.onmessage = this.handleMessage;
    } catch (error) {
      logger.error('[WebSocket] Connection error:', error);
      this.setStatus('disconnected');
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isManualDisconnect = true;
    this.clearReconnectTimeout();
    this.clearHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setStatus('disconnected');
    logger.info('[WebSocket] Disconnected');
  }

  /**
   * Subscribe to an event
   */
  subscribe<T = any>(event: string, handler: EventHandler<T>): () => void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }

    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.add(handler as EventHandler);
    }
    logger.debug(`[WebSocket] Subscribed to event: ${event}`);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(event);
      if (handlers) {
        handlers.delete(handler as EventHandler);
        if (handlers.size === 0) {
          this.eventHandlers.delete(event);
        }
      }
      logger.debug(`[WebSocket] Unsubscribed from event: ${event}`);
    };
  }

  /**
   * Send a message to the server
   */
  send(event: string, data: any): void {
    const message = JSON.stringify({ event, data, timestamp: new Date().toISOString() });

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
      logger.debug('[WebSocket] Sent message:', { event, data });
    } else {
      // Queue message if offline and queueing is enabled
      if (this.config.enableMessageQueue) {
        this.queueMessage(event, data);
        logger.debug('[WebSocket] Message queued (offline):', { event, data });
      } else {
        logger.warn('[WebSocket] Cannot send message, not connected:', { event, data });
      }
    }
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.status === 'connected' && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Listen for status changes
   */
  onStatusChange(listener: (status: ConnectionStatus) => void): () => void {
    this.statusChangeListeners.add(listener);
    return () => {
      this.statusChangeListeners.delete(listener);
    };
  }

  /**
   * Cleanup and destroy the client
   */
  destroy(): void {
    this.disconnect();
    this.eventHandlers.clear();
    this.statusChangeListeners.clear();
    this.messageQueue = [];

    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline);
      window.removeEventListener('offline', this.handleOffline);
    }

    logger.info('[WebSocket] Client destroyed');
  }

  // ============================================================================
  // Private Methods
  // ============================================================================

  private handleOpen = (): void => {
    logger.info('[WebSocket] Connection opened');
    this.setStatus('connected');
    this.reconnectAttempts = 0;
    this.startHeartbeat();

    // Process queued messages
    this.processMessageQueue();
  };

  private handleClose = (event: CloseEvent): void => {
    logger.info(`[WebSocket] Connection closed: ${event.code} - ${event.reason}`);
    this.clearHeartbeat();
    this.setStatus('disconnected');

    // Reconnect if not a manual disconnect
    if (!this.isManualDisconnect && this.reconnectAttempts < this.config.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  };

  private handleError = (event: Event): void => {
    logger.error('[WebSocket] Connection error:', event);
    // Error will trigger close event, which handles reconnection
  };

  private handleMessage = (event: MessageEvent): void => {
    try {
      const message = JSON.parse(event.data);
      logger.debug('[WebSocket] Message received:', message);

      // Handle heartbeat/ping messages
      if (message.type === 'ping' || message.event === 'ping') {
        this.send('pong', {});
        return;
      }

      // Dispatch to event handlers
      const eventType = message.type || message.event;
      if (eventType) {
        this.dispatchEvent(eventType, message.data);
      }
    } catch (error) {
      logger.error('[WebSocket] Failed to parse message:', error);
    }
  };

  private handleOnline = (): void => {
    logger.info('[WebSocket] Network online, attempting to reconnect');
    if (this.status === 'disconnected' && !this.isManualDisconnect) {
      this.connect();
    }
  };

  private handleOffline = (): void => {
    logger.info('[WebSocket] Network offline');
    this.setStatus('disconnected');
  };

  private setStatus(status: ConnectionStatus): void {
    if (this.status !== status) {
      this.status = status;
      logger.debug(`[WebSocket] Status changed to: ${status}`);

      // Notify listeners
      this.statusChangeListeners.forEach(listener => {
        try {
          listener(status);
        } catch (error) {
          logger.error('[WebSocket] Error in status change listener:', error);
        }
      });
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeoutId) {
      return; // Already scheduled
    }

    this.reconnectAttempts++;
    this.setStatus('reconnecting');

    // Calculate backoff delay with exponential decay
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(this.config.reconnectDecay, this.reconnectAttempts - 1),
      this.config.maxReconnectInterval,
    );

    logger.info(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeoutId = setTimeout(() => {
      this.reconnectTimeoutId = null;
      this.connect();
    }, delay);
  }

  private clearReconnectTimeout(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();

    // Send periodic ping to keep connection alive
    this.heartbeatIntervalId = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping', {});
      }
    }, 30000); // Every 30 seconds
  }

  private clearHeartbeat(): void {
    if (this.heartbeatIntervalId) {
      clearInterval(this.heartbeatIntervalId);
      this.heartbeatIntervalId = null;
    }
  }

  private dispatchEvent(eventType: string, data: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers && handlers.size > 0) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          logger.error(`[WebSocket] Error in event handler for ${eventType}:`, error);
        }
      });
    } else {
      logger.debug(`[WebSocket] No handlers for event: ${eventType}`);
    }
  }

  private queueMessage(event: string, data: any): void {
    if (this.messageQueue.length >= this.config.maxQueueSize) {
      // Remove oldest message
      this.messageQueue.shift();
      logger.warn('[WebSocket] Message queue full, removed oldest message');
    }

    this.messageQueue.push({
      event,
      data,
      timestamp: new Date(),
    });
  }

  private processMessageQueue(): void {
    if (this.messageQueue.length === 0) {
      return;
    }

    logger.info(`[WebSocket] Processing ${this.messageQueue.length} queued messages`);

    const messages = [...this.messageQueue];
    this.messageQueue = [];

    messages.forEach(({ event, data }) => {
      this.send(event, data);
    });
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

let wsClient: WebSocketClient | null = null;

/**
 * Get or create the WebSocket client instance
 */
export function getWebSocketClient(): WebSocketClient {
  if (!wsClient) {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8002/ws';
    wsClient = new WebSocketClient({ url: wsUrl });
  }
  return wsClient;
}

/**
 * Initialize and connect the WebSocket client
 */
export function initializeWebSocket(): WebSocketClient {
  const client = getWebSocketClient();
  if (!client.isConnected()) {
    client.connect();
  }
  return client;
}

/**
 * Disconnect and cleanup the WebSocket client
 */
export function destroyWebSocket(): void {
  if (wsClient) {
    wsClient.destroy();
    wsClient = null;
  }
}

// ============================================================================
// React Hook
// ============================================================================

/**
 * Hook to use WebSocket in React components
 * This will be used in the next sub-task
 */
export function useWebSocket() {
  const client = getWebSocketClient();

  return {
    client,
    status: client.getStatus(),
    isConnected: client.isConnected(),
    connect: () => client.connect(),
    disconnect: () => client.disconnect(),
    subscribe: <T = any>(event: string, handler: EventHandler<T>) => client.subscribe(event, handler),
    send: (event: string, data: any) => client.send(event, data),
  };
}
