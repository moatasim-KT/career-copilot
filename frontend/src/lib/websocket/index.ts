/**
 * WebSocket utilities
 */

export { WebSocketService, createWebSocketService, getWebSocketService } from './service';
export { useWebSocket } from './useWebSocket';

// Also export legacy websocket if it exists
export * from '../api/websocket';
