import { logger } from '@/lib/logger';


const POLLING_INTERVAL = 5 * 1000; // 5 seconds

export class FallbackTransport {
  private ws: WebSocket | null = null;
  private pollingIntervalId: NodeJS.Timeout | null = null;

  constructor(private url: string, private onMessage: (data: any) => void) { }

  async connect() {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onmessage = event => this.onMessage(JSON.parse(event.data));
      this.ws.onclose = () => {
        this.ws = null;
        this.startPolling();
      };
    } catch (__error) {
      this.startPolling();
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
    if (this.pollingIntervalId) {
      clearInterval(this.pollingIntervalId);
    }
  }

  private startPolling() {
    this.pollingIntervalId = setInterval(async () => {
      try {
        const response = await fetch(this.url.replace('ws', 'http'));
        const data = await response.json();
        this.onMessage(data);
      } catch (error) {
        logger.error('Polling failed:', error);
      }
    }, POLLING_INTERVAL);
  }
}
