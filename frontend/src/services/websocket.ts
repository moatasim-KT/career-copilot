/**
 * WebSocket Client Service
 * Manages real-time WebSocket connections for notifications and updates
 */

import { logger } from '@/lib/logger';

enum WebSocketStatus {
    Connecting = 'connecting',
    Connected = 'connected',
    Disconnected = 'disconnected',
    Reconnecting = 'reconnecting',
    Error = 'error',
}

interface WebSocketMessage {
    type: string;
    [key: string]: unknown;
}

type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketClient {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
    private connectionPromise: Promise<void> | null = null;
    private isConnecting = false;
    private baseUrl: string;
    private token: string | null = null;
    private status: WebSocketStatus = WebSocketStatus.Disconnected;
    private statusChangeCallback: ((status: WebSocketStatus) => void) | null = null;

    // Expose a method to set the status change callback
    public setStatusChangeCallback(callback: (status: WebSocketStatus) => void): void {
        this.statusChangeCallback = callback;
    }

    private setStatus(status: WebSocketStatus): void {
        this.status = status;
        this.statusChangeCallback?.(status);
    }

    public getStatus(): WebSocketStatus {
        return this.status;
    }

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_WS_URL || process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000';
    }

    /**
     * Connect to WebSocket server
     */
    async connect(userId: number | string, token: string): Promise<void> {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.setStatus(WebSocketStatus.Connected);
            return;
        }

        if (this.isConnecting && this.connectionPromise) {
            this.setStatus(WebSocketStatus.Connecting);
            return this.connectionPromise;
        }

        this.isConnecting = true;
        this.token = token;
        this.setStatus(WebSocketStatus.Connecting);

        this.connectionPromise = new Promise((resolve, reject) => {
            try {
                const wsUrl = `${this.baseUrl}/ws?token=${encodeURIComponent(token)}`;
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    logger.info('WebSocket connected');
                    this.reconnectAttempts = 0;
                    this.isConnecting = false;
                    this.setStatus(WebSocketStatus.Connected);
                    resolve();

                    // Send ping every 30 seconds to keep connection alive
                    this.startPingInterval();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message: WebSocketMessage = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        logger.error('Failed to parse WebSocket message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    logger.error('WebSocket error:', error);
                    this.isConnecting = false;
                    this.setStatus(WebSocketStatus.Error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    logger.info('WebSocket disconnected');
                    this.isConnecting = false;
                    this.stopPingInterval();
                    this.setStatus(WebSocketStatus.Disconnected);
                    this.attemptReconnect(userId);
                };
            } catch (error) {
                this.isConnecting = false;
                this.setStatus(WebSocketStatus.Error);
                reject(error);
            }
        });

        return this.connectionPromise;
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect(): void {
        this.stopPingInterval();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connectionPromise = null;
        this.reconnectAttempts = 0;
        this.setStatus(WebSocketStatus.Disconnected);
    }

    /**
     * Subscribe to a specific message type
     */
    subscribe(messageType: string, handler: MessageHandler): () => void {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, new Set());
        }
        this.messageHandlers.get(messageType)!.add(handler);

        // Return unsubscribe function
        return () => {
            const handlers = this.messageHandlers.get(messageType);
            if (handlers) {
                handlers.delete(handler);
                if (handlers.size === 0) {
                    this.messageHandlers.delete(messageType);
                }
            }
        };
    }

    /**
     * Subscribe to a channel
     */
    subscribeToChannel(channel: string): void {
        this.send({
            type: 'subscribe',
            channel,
        });
    }

    /**
     * Unsubscribe from a channel
     */
    unsubscribeFromChannel(channel: string): void {
        this.send({
            type: 'unsubscribe',
            channel,
        });
    }

    /**
     * Send a message to the server
     */
    private send(message: Record<string, unknown>): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            logger.warn('WebSocket not connected, message not sent:', message);
        }
    }

    /**
     * Handle incoming message
     */
    private handleMessage(message: WebSocketMessage): void {
        const handlers = this.messageHandlers.get(message.type);
        if (handlers) {
            handlers.forEach((handler) => {
                try {
                    handler(message);
                } catch (error) {
                    logger.error('Error in message handler:', error);
                }
            });
        }

        // Also notify wildcard handlers
        const wildcardHandlers = this.messageHandlers.get('*');
        if (wildcardHandlers) {
            wildcardHandlers.forEach((handler) => {
                try {
                    handler(message);
                } catch (error) {
                    logger.error('Error in wildcard handler:', error);
                }
            });
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    private async attemptReconnect(userId: number | string): Promise<void> {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            logger.error('Max reconnection attempts reached');
            this.setStatus(WebSocketStatus.Error);
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        logger.info(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.setStatus(WebSocketStatus.Reconnecting);

        setTimeout(() => {
            if (this.token) {
                this.connect(userId, this.token).catch((error) => {
                    logger.error('Reconnection failed:', error);
                });
            }
        }, delay);
    }

    /**
     * Ping interval management
     */
    private pingIntervalId: number | null = null;

    private startPingInterval(): void {
        this.stopPingInterval();
        this.pingIntervalId = window.setInterval(() => {
            this.send({ type: 'ping' });
        }, 30000); // 30 seconds
    }

    private stopPingInterval(): void {
        if (this.pingIntervalId !== null) {
            clearInterval(this.pingIntervalId);
            this.pingIntervalId = null;
        }
    }

    /**
     * Get connection status
     */
    get isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}

// Singleton instance
export const webSocketClient = new WebSocketClient();

// Notification types for type safety
export interface JobMatchNotification {
    type: 'job_match_notification';
    job_id: number;
    job_title: string;
    company: string;
    match_score: number;
    timestamp: string;
}

export interface ApplicationStatusNotification {
    type: 'application_status_update';
    application_id: number;
    status: string;
    timestamp: string;
}

export interface AnalyticsNotification {
    type: 'analytics_update';
    analytics: Record<string, unknown>;
    timestamp: string;
}

export interface SystemNotification {
    type: 'system_notification';
    notification_type: 'info' | 'warning' | 'error';
    message: string;
    timestamp: string;
}

export type NotificationMessage =
    | JobMatchNotification
    | ApplicationStatusNotification
    | AnalyticsNotification
    | SystemNotification
    | WebSocketMessage;
