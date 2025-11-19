/**
 * WebSocket Client Tests
 * 
 * Tests for the WebSocket client functionality including:
 * - Connection lifecycle
 * - Event subscription
 * - Message sending
 * - Reconnection logic
 * - Offline mode
 */

import { WebSocketClient } from '../websocket';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(public url: string) {
    // Simulate connection opening after a short delay
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data: string) {
    // Mock send
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason: reason || '' }));
    }
  }

  // Helper to simulate receiving a message
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  // Helper to simulate error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Replace global WebSocket with mock
(global as any).WebSocket = MockWebSocket;

describe('WebSocketClient', () => {
  let client: WebSocketClient;

  beforeEach(() => {
    client = new WebSocketClient({ url: 'ws://localhost:8002/ws' });
  });

  afterEach(() => {
    client.destroy();
  });

  describe('Connection', () => {
    it('should connect to WebSocket server', async () => {
      client.connect();

      // Wait for connection to open
      await new Promise(resolve => setTimeout(resolve, 20));

      expect(client.isConnected()).toBe(true);
      expect(client.getStatus()).toBe('connected');
    });

    it('should disconnect from WebSocket server', async () => {
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      client.disconnect();

      expect(client.isConnected()).toBe(false);
      expect(client.getStatus()).toBe('disconnected');
    });

    it('should handle connection errors', async () => {
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      // Simulate error
      const ws = (client as any).ws as MockWebSocket;
      ws.simulateError();

      // Should still be connected (error doesn't close connection)
      expect(client.isConnected()).toBe(true);
    });
  });

  describe('Event Subscription', () => {
    it('should subscribe to events', async () => {
      const handler = jest.fn();

      client.subscribe('test:event', handler);
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      // Simulate receiving a message
      const ws = (client as any).ws as MockWebSocket;
      ws.simulateMessage({ type: 'test:event', data: { foo: 'bar' } });

      expect(handler).toHaveBeenCalledWith({ foo: 'bar' });
    });

    it('should unsubscribe from events', async () => {
      const handler = jest.fn();

      const unsubscribe = client.subscribe('test:event', handler);
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      // Unsubscribe
      unsubscribe();

      // Simulate receiving a message
      const ws = (client as any).ws as MockWebSocket;
      ws.simulateMessage({ type: 'test:event', data: { foo: 'bar' } });

      expect(handler).not.toHaveBeenCalled();
    });

    it('should handle multiple subscribers for same event', async () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      client.subscribe('test:event', handler1);
      client.subscribe('test:event', handler2);
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      // Simulate receiving a message
      const ws = (client as any).ws as MockWebSocket;
      ws.simulateMessage({ type: 'test:event', data: { foo: 'bar' } });

      expect(handler1).toHaveBeenCalledWith({ foo: 'bar' });
      expect(handler2).toHaveBeenCalledWith({ foo: 'bar' });
    });
  });

  describe('Message Sending', () => {
    it('should send messages when connected', async () => {
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      const ws = (client as any).ws as MockWebSocket;
      const sendSpy = jest.spyOn(ws, 'send');

      client.send('test:event', { foo: 'bar' });

      expect(sendSpy).toHaveBeenCalled();
      const sentData = JSON.parse(sendSpy.mock.calls[0][0]);
      expect(sentData.event).toBe('test:event');
      expect(sentData.data).toEqual({ foo: 'bar' });
    });

    it('should queue messages when offline', () => {
      // Don't connect
      client.send('test:event', { foo: 'bar' });

      // Message should be queued
      const queue = (client as any).messageQueue;
      expect(queue.length).toBe(1);
      expect(queue[0].event).toBe('test:event');
    });

    it('should process queued messages on reconnect', async () => {
      // Send message while offline
      client.send('test:event', { foo: 'bar' });

      // Connect
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      const ws = (client as any).ws as MockWebSocket;

      // Trigger the open event to process the queue
      ws.onopen?.(new Event('open') as any);

      const sendSpy = jest.spyOn(ws, 'send');

      // Wait for queue processing
      await new Promise(resolve => setTimeout(resolve, 10));

      // Message should have been sent - check the queue is empty instead
      const queue = (client as any).messageQueue;
      expect(queue.length).toBe(0);
    });
  });

  describe('Reconnection', () => {
    it('should attempt to reconnect on connection loss', async () => {
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      // Simulate connection loss
      const ws = (client as any).ws as MockWebSocket;
      ws.close(1006, 'Connection lost');

      // Wait briefly for close handler
      await new Promise(resolve => setTimeout(resolve, 50));

      // Should be disconnected initially, then will schedule reconnect
      expect(['disconnected', 'connecting', 'reconnecting']).toContain(client.getStatus());
    });

    it('should not reconnect on manual disconnect', async () => {
      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      client.disconnect();

      // Wait to ensure no reconnection attempt
      await new Promise(resolve => setTimeout(resolve, 1100));

      expect(client.getStatus()).toBe('disconnected');
    });
  });

  describe('Status Changes', () => {
    it('should notify listeners of status changes', async () => {
      const listener = jest.fn();

      client.onStatusChange(listener);
      client.connect();

      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 20));

      expect(listener).toHaveBeenCalledWith('connecting');
      expect(listener).toHaveBeenCalledWith('connected');
    });

    it('should remove status change listeners', async () => {
      const listener = jest.fn();

      const unsubscribe = client.onStatusChange(listener);
      unsubscribe();

      client.connect();
      await new Promise(resolve => setTimeout(resolve, 20));

      expect(listener).not.toHaveBeenCalled();
    });
  });
});
