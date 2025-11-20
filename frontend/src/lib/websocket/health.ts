
const PING_INTERVAL = 30 * 1000; // 30 seconds
const PONG_TIMEOUT = 10 * 1000; // 10 seconds

export class HealthMonitor {
  private pingTimeoutId: NodeJS.Timeout | null = null;
  private pongTimeoutId: NodeJS.Timeout | null = null;

  constructor(private ws: WebSocket) { }

  start() {
    this.pingTimeoutId = setInterval(() => {
      this.ws.send(JSON.stringify({ type: 'ping' }));
      this.pongTimeoutId = setTimeout(() => {
        // No pong received, connection is unhealthy
        this.ws.close();
      }, PONG_TIMEOUT);
    }, PING_INTERVAL);

    this.ws.addEventListener('message', event => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'pong') {
          if (this.pongTimeoutId) {
            clearTimeout(this.pongTimeoutId);
            this.pongTimeoutId = null;
          }
        }
      } catch (e) {
        // Ignore non-JSON messages or parse errors
      }
    });
  }

  stop() {
    if (this.pingTimeoutId) {
      clearInterval(this.pingTimeoutId);
      this.pingTimeoutId = null;
    }
    if (this.pongTimeoutId) {
      clearTimeout(this.pongTimeoutId);
      this.pongTimeoutId = null;
    }
  }
}
