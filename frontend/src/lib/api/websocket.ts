import { logger } from '@/lib/logger';

/**
 * WebSocket service for real-time notifications and updates
 * Connects to the FastAPI WebSocket endpoint for live dashboard updates
 */

export interface WebSocketMessage {
  type: string;
  user_id?: number;
  timestamp: string;
  message?: string;
  [key: string]: unknown;
}

export interface JobMatchNotification extends WebSocketMessage {
  type: 'job_match';
  job: Record<string, unknown>;
  match_score: number;
}

export interface ApplicationStatusUpdate extends WebSocketMessage {
  type: 'application_status_update';
  application: Record<string, unknown>;
}

export interface AnalyticsUpdate extends WebSocketMessage {
  type: 'analytics_update';
  analytics: Record<string, unknown>;
}

export interface SystemNotification extends WebSocketMessage {
  type: 'system_notification';
  notification_type: 'info' | 'warning' | 'error';
}

export interface SkillGapUpdate extends WebSocketMessage {
  type: 'skill_gap_update';
  skill_gap: Record<string, unknown>;
}

type WebSocketEventCallback = (_data: WebSocketMessage) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private token: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10; // Increased from 5
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000; // Max 30 seconds
  private eventListeners: Map<string, WebSocketEventCallback[]> = new Map();
  private isConnecting = false;
  private pingInterval: NodeJS.Timeout | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pongTimeout: NodeJS.Timeout | null = null;
  private lastPongTime: number = 0;
  private baseUrl: string;
  private shouldReconnect = true; // Flag to control reconnection
  private messageQueue: Record<string, unknown>[] = [];
  private messageQueue: Record<string, unknown>[] = [];

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002';
    // Convert HTTP URL to WebSocket URL
    this.baseUrl = this.baseUrl
      .replace('http://', 'ws://')
      .replace('https://', 'wss://');
  }

  /**
   * Connect to the WebSocket server with authentication token
   */
  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.token = token;
      this.isConnecting = true;
      this.shouldReconnect = true; // Enable reconnection

      try {
        // Create WebSocket connection with token in header (if supported) or as query param
        const wsUrl = `${this.baseUrl}/ws`;
        this.socket = new WebSocket(wsUrl);

        // Send token after connection opens
        this.socket.onopen = () => {
          logger.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;

          // Send authentication message
          this.sendMessage({
            type: 'auth',
            token: this.token,
          });

          // Process offline message queue
          this.processMessageQueue();

          // Process offline message queue
          this.processMessageQueue();

          // Start ping interval to keep connection alive
          this.startPingInterval();

          this.emit('connected', {
            type: 'connected',
            timestamp: new Date().toISOString(),
          });

          resolve();
        };

        this.socket.onmessage = event => {
          try {
            const data = JSON.parse(event.data) as WebSocketMessage;
            this.handleMessage(data);
          } catch (error) {
            logger.error('Error parsing WebSocket message:', error);
          }
        };

        this.socket.onclose = event => {
          logger.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.stopPingInterval();
          this.stopPongTimeout();

          this.emit('disconnected', {
            type: 'disconnected',
            timestamp: new Date().toISOString(),
            code: event.code,
            reason: event.reason,
          });

          // Attempt to reconnect if not a normal closure and reconnection is enabled
          if (
            event.code !== 1000 &&
            this.shouldReconnect &&
            this.reconnectAttempts < this.maxReconnectAttempts
          ) {
            this.scheduleReconnect();
          }
        };

        this.socket.onerror = error => {
          logger.error('WebSocket error:', error);
          this.isConnecting = false;

          this.emit('error', {
            type: 'error',
            timestamp: new Date().toISOString(),
            message: 'WebSocket connection error',
          });

          reject(error);
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    this.shouldReconnect = false; // Prevent reconnection
    this.clearReconnectTimeout();
    this.stopPingInterval();
    this.stopPongTimeout();

    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.token = null;
    this.reconnectAttempts = 0;
  }

  /**
   * Reconnect to the WebSocket server
   */
  reconnect(): Promise<void> {
    this.shouldReconnect = true;
    this.disconnect();

    if (!this.token) {
      return Promise.reject(new Error('No authentication token available'));
    }

    return this.connect(this.token);
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  /**
   * Send a message to the server
   */
  private sendMessage(message: Record<string, unknown>): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      this.messageQueue.push(message);
    }
  }

  /**
   * Process the offline message queue
   */
  private processMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message);
      }
    }
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(data: WebSocketMessage): void {
    logger.log('WebSocket message received:', data);

    // Handle specific message types
    switch (data.type) {
      case 'connection_established':
        logger.log('WebSocket connection established for user:', data.user_id);
        this.reconnectAttempts = 0; // Reset reconnect counter on successful connection
        this.emit('connected', data);
        break;
      case 'pong':
        this.lastPongTime = Date.now();
        this.stopPongTimeout();
        break;
      case 'subscription_confirmation':
        logger.log('Subscription confirmed:', data);
        break;
      case 'error':
        logger.error('WebSocket error message:', data.message);
        this.emit('error', data);
        break;
      default:
        // Emit to registered listeners
        this.emit(data.type, data);
        break;
    }

    // Always emit to 'message' listeners for all messages
    this.emit('message', data);
  }

  /**
   * Subscribe to a specific event type
   */
  on(eventType: string, callback: WebSocketEventCallback): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      listeners.push(callback);
    }
  }

  /**
   * Unsubscribe from a specific event type
   */
  off(eventType: string, callback?: WebSocketEventCallback): void {
    if (!this.eventListeners.has(eventType)) {
      return;
    }

    if (callback) {
      const listeners = this.eventListeners.get(eventType);
      if (listeners) {
        const index = listeners.indexOf(callback);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    } else {
      // Remove all listeners for this event type
      this.eventListeners.delete(eventType);
    }
  }

  /**
   * Emit an event to all registered listeners
   */
  private emit(eventType: string, data: WebSocketMessage): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          logger.error('Error in WebSocket event listener:', error);
        }
      });
    }
  }

  /**
   * Subscribe to a notification channel
   */
  subscribeToChannel(channel: string): void {
    this.sendMessage({
      type: 'subscribe',
      channel,
    });
  }

  /**
   * Unsubscribe from a notification channel
   */
  unsubscribeFromChannel(channel: string): void {
    this.sendMessage({
      type: 'unsubscribe',
      channel,
    });
  }

  /**
   * Send ping to keep connection alive
   */
  private ping(): void {
    this.sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString(),
    });

    // Set timeout to detect if pong is not received
    this.stopPongTimeout();
    this.pongTimeout = setTimeout(() => {
      logger.warn('Pong not received, connection may be dead');
      // Force reconnect if pong not received within 10 seconds
      if (this.socket) {
        this.socket.close();
      }
    }, 10000);
  }

  /**
   * Stop pong timeout
   */
  private stopPongTimeout(): void {
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
  }

  /**
   * Start ping interval
   */
  private startPingInterval(): void {
    this.stopPingInterval();
    this.lastPongTime = Date.now();
    this.pingInterval = setInterval(() => {
      this.ping();
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Clear reconnect timeout
   */
  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * Schedule reconnection attempt with exponential backoff
   */
  private scheduleReconnect(): void {
    if (!this.shouldReconnect || !this.token) {
      return;
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      logger.error(`Max reconnection attempts (${this.maxReconnectAttempts}) reached`);
      this.emit('max_reconnect_attempts', {
        type: 'max_reconnect_attempts',
        timestamp: new Date().toISOString(),
        reconnectAttempts: this.reconnectAttempts,
      });
      return;
    }

    this.reconnectAttempts++;

    // Exponential backoff: delay = baseDelay * 2^(attempts - 1)
    // Capped at maxReconnectDelay
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay,
    );

    logger.log(
      `Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`,
    );

    this.emit('reconnecting', {
      type: 'reconnecting',
      timestamp: new Date().toISOString(),
      reconnectAttempts: this.reconnectAttempts,
      delayMs: delay,
    });

    this.clearReconnectTimeout();
    this.reconnectTimeout = setTimeout(() => {
      if (this.shouldReconnect && this.token) {
        logger.log(`Reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        this.connect(this.token).catch(error => {
          logger.error('Reconnect failed:', error);
          // scheduleReconnect will be called again by onclose handler
        });
      }
    }, delay);
  }

  /**
   * Process the offline message queue
   */
  private processMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message);
      }
    }
  }
  getConnectionInfo(): {
    connected: boolean;
    reconnectAttempts: number;
    maxReconnectAttempts: number;
    hasToken: boolean;
    lastPongTime: number;
    isConnecting: boolean;
  } {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      hasToken: !!this.token,
      lastPongTime: this.lastPongTime,
      isConnecting: this.isConnecting,
    };
  }

  /**
   * Get connection health status
   */
  getHealthStatus(): 'healthy' | 'degraded' | 'disconnected' {
    if (!this.isConnected()) {
      return 'disconnected';
    }

    const timeSinceLastPong = Date.now() - this.lastPongTime;

    // If no pong in last 60 seconds, connection is degraded
    if (timeSinceLastPong > 60000) {
      return 'degraded';
    }

    return 'healthy';
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();