

type BatchedRequest<T> = {
  resolve: (value: T | PromiseLike<T>) => void;
  reject: (reason?: any) => void;
};

class Batcher<T, R> {
  private queue: Map<T, BatchedRequest<R>[]> = new Map();
  private timeoutId: NodeJS.Timeout | null = null;

  constructor(private batchFn: (reqs: T[]) => Promise<R[]>, private maxBatchSize: number, private batchingWindow: number) { }

  async request(req: T): Promise<R> {
    return new Promise((resolve, reject) => {
      let bucket = this.queue.get(req);
      if (!bucket) {
        bucket = [];
        this.queue.set(req, bucket);
      }
      bucket.push({ resolve, reject });

      if (this.queue.size >= this.maxBatchSize) {
        this.flush();
      } else if (!this.timeoutId) {
        this.timeoutId = setTimeout(() => this.flush(), this.batchingWindow);
      }
    });
  }

  private async flush() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }

    const requests = Array.from(this.queue.keys());
    const callbacks = Array.from(this.queue.values());
    this.queue.clear();

    try {
      const results = await this.batchFn(requests);
      callbacks.forEach((cb, i) => {
        cb.forEach(c => c.resolve(results[i]));
      });
    } catch (error) {
      callbacks.forEach(cb => {
        cb.forEach(c => c.reject(error));
      });
    }
  }
}

export function createBatcher<T, R>(
  batchFn: (reqs: T[]) => Promise<R[]>,
  maxBatchSize = 10,
  batchingWindow = 100,
) {
  return new Batcher<T, R>(batchFn, maxBatchSize, batchingWindow);
}

// ============================================================================
// API Request Batching
// ============================================================================

interface BatchedAPIRequest {
  id: string;
  url: string;
  method: string;
  body?: any;
  headers?: Record<string, string>;
}

interface BatchedAPIResponse {
  id: string;
  status: number;
  data?: any;
  error?: string;
}

/**
 * Batch multiple API requests into a single request
 * This is useful when the backend supports batch endpoints
 */
export class APIBatcher {
  private batchEndpoint: string;
  private maxBatchSize: number;
  private batchWindow: number;
  private pendingRequests: Map<string, {
    request: BatchedAPIRequest;
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = new Map();
  private batchTimer: NodeJS.Timeout | null = null;

  constructor(
    batchEndpoint: string,
    options: {
      maxBatchSize?: number;
      batchWindow?: number;
    } = {},
  ) {
    this.batchEndpoint = batchEndpoint;
    this.maxBatchSize = options.maxBatchSize || 10;
    this.batchWindow = options.batchWindow || 100; // 100ms default window
  }

  /**
   * Add a request to the batch queue
   */
  async request<T>(
    url: string,
    options: {
      method?: string;
      body?: any;
      headers?: Record<string, string>;
    } = {},
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const requestId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      const request: BatchedAPIRequest = {
        id: requestId,
        url,
        method: options.method || 'GET',
        body: options.body,
        headers: options.headers,
      };

      this.pendingRequests.set(requestId, {
        request,
        resolve,
        reject,
      });

      // If batch size limit reached, flush immediately
      if (this.pendingRequests.size >= this.maxBatchSize) {
        this.flush();
      } else if (!this.batchTimer) {
        // Otherwise, schedule a flush
        this.batchTimer = setTimeout(() => this.flush(), this.batchWindow);
      }
    });
  }

  /**
   * Flush pending requests as a batch
   */
  private async flush() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    if (this.pendingRequests.size === 0) {
      return;
    }

    // Collect all pending requests
    const requests = Array.from(this.pendingRequests.values());
    const requestMap = new Map(this.pendingRequests);
    this.pendingRequests.clear();

    try {
      // Send batch request to server
      const response = await fetch(this.batchEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          requests: requests.map(r => r.request),
        }),
      });

      if (!response.ok) {
        throw new Error(`Batch request failed: ${response.statusText}`);
      }

      const result = await response.json();
      const responses: BatchedAPIResponse[] = result.responses || [];

      // Resolve individual requests
      responses.forEach((res) => {
        const pending = requestMap.get(res.id);
        if (pending) {
          if (res.error) {
            pending.reject(new Error(res.error));
          } else {
            pending.resolve(res.data);
          }
        }
      });
    } catch (error) {
      // Reject all pending requests if batch fails
      requests.forEach(({ reject }) => {
        reject(error);
      });
    }
  }

  /**
   * Cancel all pending requests
   */
  cancel() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    this.pendingRequests.forEach(({ reject }) => {
      reject(new Error('Batch request cancelled'));
    });

    this.pendingRequests.clear();
  }
}

/**
 * Create a simple batch function wrapper
 */
export function createBatchFunction<TInput, TOutput>(
  batchFn: (inputs: TInput[]) => Promise<TOutput[]>,
  options: {
    maxBatchSize?: number;
    batchWindow?: number;
  } = {},
): (input: TInput) => Promise<TOutput> {
  const batcher = createBatcher(batchFn, options.maxBatchSize, options.batchWindow);
  return (input: TInput) => batcher.request(input);
}
