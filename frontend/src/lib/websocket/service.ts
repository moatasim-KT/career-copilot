/**
 * WebSocket Service with Auto-Reconnection
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Connection health monitoring
 * - Event-based message handling
 * - Graceful disconnection
 */

type MessageHandler = (data: any) => void;
type ErrorHandler = (error: Event) => void;
type ConnectionHandler = () => void;

interface WebSocketConfig {
    url: string;
    maxReconnectAttempts?: number;
    reconnectDelay?: number;
    maxReconnectDelay?: number;
    heartbeatInterval?: number;
}

export class WebSocketService {
    private ws: WebSocket | null = null;
    private config: Required<WebSocketConfig>;
    private reconnectAttempts = 0;
    private reconnectTimer?: NodeJS.Timeout;
    private heartbeatTimer?: NodeJS.Timeout;
    private lastToken: string | null = null;

    // Connection state
    private connected = false;
    private intentionallyClosed = false;

    // Event handlers
    private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
    private errorHandlers: Set<ErrorHandler> = new Set();
    private connectHandlers: Set<ConnectionHandler> = new Set();
    private disconnectHandlers: Set<ConnectionHandler> = new Set();

    constructor(config: WebSocketConfig) {
        this.config = {
            url: config.url,
            maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
            reconnectDelay: config.reconnectDelay ?? 1000,
            maxReconnectDelay: config.maxReconnectDelay ?? 30000,
            heartbeatInterval: config.heartbeatInterval ?? 30000,
        };
    }

    /**
     * Connect to WebSocket server
     */
    connect(token: string): void {
        if (this.ws && this.connected) {
            console.warn('WebSocket already connected');
            return;
        }

        this.lastToken = token;
        this.intentionallyClosed = false;

        try {
            const wsUrl = `${this.config.url}?token=${encodeURIComponent(token)}`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                this.notifyConnectHandlers();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.connected = false;
                this.stopHeartbeat();
                this.notifyDisconnectHandlers();

                if (!this.intentionallyClosed) {
                    this.reconnect();
                }
            };

            this.ws.onerror = (event) => {
                console.error('WebSocket error:', event);
                this.notifyErrorHandlers(event);

                // Connection will be retried in onclose
                this.connected = false;
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.reconnect();
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect(): void {
        this.intentionallyClosed = true;
        this.stopHeartbeat();
        this.clearReconnectTimer();

        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }

        this.connected = false;
    }

    /**
     * Send a message through WebSocket
     */
    send(type: string, data: any = {}): void {
        if (!this.ws || !this.connected) {
            console.warn('WebSocket not connected, cannot send message');
            return;
        }

        try {
            const message = JSON.stringify({ type, data });
            this.ws.send(message);
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
        }
    }

    /**
     * Subscribe to messages of a specific type
     */
    on(type: string, handler: MessageHandler): () => void {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, new Set());
        }
        this.messageHandlers.get(type)!.add(handler);

        // Return unsubscribe function
        return () => {
            const handlers = this.messageHandlers.get(type);
            if (handlers) {
                handlers.delete(handler);
                if (handlers.size === 0) {
                    this.messageHandlers.delete(type);
                }
            }
        };
    }

    /**
     * Subscribe to connection events
     */
    onConnect(handler: ConnectionHandler): () => void {
        this.connectHandlers.add(handler);
        return () => this.connectHandlers.delete(handler);
    }

    /**
     * Subscribe to disconnection events
     */
    onDisconnect(handler: ConnectionHandler): () => void {
        this.disconnectHandlers.add(handler);
        return () => this.disconnectHandlers.delete(handler);
    }

    /**
     * Subscribe to error events
     */
    onError(handler: ErrorHandler): () => void {
        this.errorHandlers.add(handler);
        return () => this.errorHandlers.delete(handler);
    }

    /**
     * Check if WebSocket is connected
     */
    isConnected(): boolean {
        return this.connected;
    }

    /**
     * Get current reconnection attempt count
     */
    getReconnectAttempts(): number {
        return this.reconnectAttempts;
    }

    /**
     * Handle incoming messages
     */
    private handleMessage(data: any): void {
        const { type, ...payload } = data;

        // Handle heartbeat response
        if (type === 'pong') {
            return;
        }

        // Notify type-specific handlers
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(payload);
                } catch (error) {
                    console.error(`Error in message handler for type "${type}":`, error);
                }
            });
        }

        // Also notify wildcard handlers
        const wildcardHandlers = this.messageHandlers.get('*');
        if (wildcardHandlers) {
            wildcardHandlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error('Error in wildcard message handler:', error);
                }
            });
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    private reconnect(): void {
        if (this.intentionallyClosed) {
            return;
        }

        if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.notifyErrorHandlers(new Event('max_reconnect_attempts'));
            return;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
            this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            this.config.maxReconnectDelay,
        );

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.config.maxReconnectAttempts})`);

        this.reconnectTimer = setTimeout(() => {
            this.reconnectAttempts++;
            if (this.lastToken) {
                this.connect(this.lastToken);
            }
        }, delay);
    }

    /**
     * Clear reconnection timer
     */
    private clearReconnectTimer(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = undefined;
        }
    }

    /**
     * Start heartbeat to keep connection alive
     */
    private startHeartbeat(): void {
        this.stopHeartbeat();

        this.heartbeatTimer = setInterval(() => {
            if (this.connected && this.ws) {
                this.send('ping');
            }
        }, this.config.heartbeatInterval);
    }

    /**
     * Stop heartbeat timer
     */
    private stopHeartbeat(): void {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = undefined;
        }
    }

    /**
     * Notify all connect handlers
     */
    private notifyConnectHandlers(): void {
        this.connectHandlers.forEach(handler => {
            try {
                handler();
            } catch (error) {
                console.error('Error in connect handler:', error);
            }
        });
    }

    /**
     * Notify all disconnect handlers
     */
    private notifyDisconnectHandlers(): void {
        this.disconnectHandlers.forEach(handler => {
            try {
                handler();
            } catch (error) {
                console.error('Error in disconnect handler:', error);
            }
        });
    }

    /**
     * Notify all error handlers
     */
    private notifyErrorHandlers(error: Event): void {
        this.errorHandlers.forEach(handler => {
            try {
                handler(error);
            } catch (handlerError) {
                console.error('Error in error handler:', handlerError);
            }
        });
    }
}

/**
 * Create a WebSocket service instance
 */
export function createWebSocketService(config: WebSocketConfig): WebSocketService {
    return new WebSocketService(config);
}

/**
 * Default WebSocket service instance
 */
let defaultService: WebSocketService | null = null;

export function getWebSocketService(): WebSocketService {
    if (!defaultService) {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8002/ws';
        defaultService = createWebSocketService({ url: wsUrl });
    }
    return defaultService;
}
