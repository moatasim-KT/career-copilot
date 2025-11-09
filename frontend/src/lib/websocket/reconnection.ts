
const MAX_RETRIES = 5;
const INITIAL_DELAY = 1000; // 1 second

export class Reconnector {
  private retries = 0;
  private timeoutId: NodeJS.Timeout | null = null;

  constructor(private connect: () => Promise<void>) {}

  start() {
    this.connectWithBackoff();
  }

  stop() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }

  private async connectWithBackoff() {
    try {
      await this.connect();
      this.retries = 0; // Reset retries on successful connection
    } catch (__error) {
      if (this.retries < MAX_RETRIES) {
        const delay = INITIAL_DELAY * Math.pow(2, this.retries);
        this.timeoutId = setTimeout(() => this.connectWithBackoff(), delay);
        this.retries++;
      } else {
        console.__error('Max retries reached. Could not connect to WebSocket.');
      }
    }
  }
}
