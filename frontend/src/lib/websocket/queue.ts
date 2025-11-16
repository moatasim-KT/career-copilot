import { logger } from '@/lib/logger';


export class MessageQueue {
  private queue: string[] = [];

  constructor(private ws: WebSocket) {
    // Load queue from localStorage
    try {
      const stored = localStorage.getItem('websocket-queue');
      if (stored) {
        this.queue = JSON.parse(stored);
      }
    } catch (error) {
      logger.error('Failed to load message queue from localStorage:', error);
    }

    this.ws.onopen = () => this.flush();
  }

  send(message: string) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      this.queue.push(message);
      this.saveQueue();
    }
  }

  private flush() {
    this.queue.forEach(message => this.ws.send(message));
    this.queue = [];
    this.saveQueue();
  }

  private saveQueue() {
    try {
      localStorage.setItem('websocket-queue', JSON.stringify(this.queue));
    } catch (error) {
      logger.error('Failed to save message queue to localStorage:', error);
    }
  }
}
