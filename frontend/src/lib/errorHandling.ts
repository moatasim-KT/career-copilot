/**
 * Error Handling Utility
 * 
 * Comprehensive error classification, user-friendly messaging, and retry logic.
 * Handles network errors, authentication errors, server errors, and client errors.
 * 
 * @module lib/errorHandling
 */

import { toast } from 'sonner';

/**
 * Error types for classification
 */
export type ErrorType = 'network' | 'auth' | 'server' | 'client' | 'unknown';

/**
 * Error context for logging and debugging
 */
export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  metadata?: Record<string, any>;
}

/**
 * Retry configuration
 */
export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number; // milliseconds
  maxDelay: number;
  backoffMultiplier: number;
}

/**
 * Default retry configuration
 */
export const defaultRetryConfig: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
};

/**
 * Classify error into specific type
 */
export function classifyError(error: any): ErrorType {
  // Network errors
  if (
    error instanceof TypeError &&
    (error.message.includes('fetch') || error.message.includes('network'))
  ) {
    return 'network';
  }

  if (error.message === 'Network error' || error.message === 'Failed to fetch') {
    return 'network';
  }

  // Check for status code if available
  const status = error.status || error.response?.status;

  if (status) {
    // Authentication errors
    if (status === 401 || status === 403) {
      return 'auth';
    }

    // Server errors
    if (status >= 500 && status < 600) {
      return 'server';
    }

    // Client errors
    if (status >= 400 && status < 500) {
      return 'client';
    }
  }

  // Check error name
  if (error.name === 'AbortError') {
    return 'network';
  }

  return 'unknown';
}

/**
 * Get user-friendly error message based on error type and details
 */
export function getErrorMessage(error: any): string {
  const errorType = classifyError(error);
  const status = error.status || error.response?.status;

  // Try to get message from error object
  const errorMessage =
    error.message ||
    error.error ||
    error.response?.data?.message ||
    error.response?.data?.detail;

  switch (errorType) {
    case 'network':
      return 'Connection lost. Please check your internet connection and try again.';

    case 'auth':
      if (status === 401) {
        return 'Your session has expired. Please log in again.';
      }
      if (status === 403) {
        return "You don't have permission to perform this action.";
      }
      return 'Authentication error. Please log in again.';

    case 'server':
      if (status === 500) {
        return 'Server error. Please try again later.';
      }
      if (status === 502 || status === 503) {
        return 'Service temporarily unavailable. Please try again in a few moments.';
      }
      if (status === 504) {
        return 'Request timeout. Please try again.';
      }
      return 'Server error. Our team has been notified.';

    case 'client':
      if (status === 404) {
        return 'The requested resource was not found.';
      }
      if (status === 422) {
        return errorMessage || 'Invalid data. Please check your input and try again.';
      }
      if (status === 429) {
        return 'Too many requests. Please wait a moment and try again.';
      }
      return errorMessage || 'Invalid request. Please check your input.';

    case 'unknown':
    default:
      return errorMessage || 'An unexpected error occurred. Please try again.';
  }
}

/**
 * Determine if error should be retried
 */
export function shouldRetry(error: any, attemptNumber: number = 1): boolean {
  const errorType = classifyError(error);
  const status = error.status || error.response?.status;

  // Don't retry if max attempts reached
  if (attemptNumber >= defaultRetryConfig.maxAttempts) {
    return false;
  }

  // Retry network errors
  if (errorType === 'network') {
    return true;
  }

  // Retry server errors (5xx)
  if (errorType === 'server') {
    return true;
  }

  // Retry specific status codes
  if (status === 408 || status === 429 || status === 503 || status === 504) {
    return true;
  }

  // Don't retry auth errors, client errors, or unknown errors
  return false;
}

/**
 * Calculate delay for exponential backoff
 */
export function calculateBackoffDelay(
  attemptNumber: number,
  config: RetryConfig = defaultRetryConfig,
): number {
  const delay = Math.min(
    config.baseDelay * Math.pow(config.backoffMultiplier, attemptNumber - 1),
    config.maxDelay,
  );

  // Add jitter to prevent thundering herd
  const jitter = Math.random() * 0.3 * delay;
  return delay + jitter;
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: RetryConfig = defaultRetryConfig,
  onRetry?: (attemptNumber: number, error: any) => void,
): Promise<T> {
  let lastError: any;

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Check if we should retry
      if (!shouldRetry(error, attempt)) {
        throw error;
      }

      // If this was the last attempt, throw the error
      if (attempt === config.maxAttempts) {
        throw error;
      }

      // Calculate delay and wait
      const delay = calculateBackoffDelay(attempt, config);

      // Call retry callback if provided
      if (onRetry) {
        onRetry(attempt, error);
      }

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Handle error with appropriate user notification
 */
export function handleError(
  error: any,
  context?: ErrorContext,
  options?: {
    showToast?: boolean;
    logToConsole?: boolean;
    logToSentry?: boolean;
  },
): void {
  const {
    showToast = true,
    logToConsole = true,
    logToSentry = true,
  } = options || {};

  const errorType = classifyError(error);
  const errorMessage = getErrorMessage(error);

  // Log to console in development
  if (logToConsole && process.env.NODE_ENV === 'development') {
    console.error('[Error Handler]', {
      type: errorType,
      message: errorMessage,
      error,
      context,
    });
  }

  // Log to Sentry in production
  if (logToSentry && process.env.NODE_ENV === 'production') {
    try {
      // Dynamic import to avoid bundling Sentry in development
      import('./sentry').then(({ captureException, setContext }) => {
        // Set error context
        if (context) {
          setContext('error_context', {
            component: context.component,
            action: context.action,
            userId: context.userId,
            ...context.metadata,
          });
        }

        // Capture exception with tags
        captureException(error, {
          tags: {
            errorType,
            component: context?.component || 'unknown',
          },
          extra: {
            errorMessage,
            context,
          },
          level: errorType === 'server' ? 'error' : 'warning',
        });
      });
    } catch (sentryError) {
      console.error('[Sentry Error]', sentryError);
    }
  }

  // Show toast notification
  if (showToast) {
    const toastOptions: any = {
      duration: 5000,
    };

    // Add action button for retryable errors
    if (shouldRetry(error)) {
      toastOptions.action = {
        label: 'Retry',
        onClick: () => {
          // The calling code should handle retry logic
          console.log('Retry clicked');
        },
      };
    }

    // Show appropriate toast based on error type
    switch (errorType) {
      case 'network':
        toast.error('Connection Error', {
          description: errorMessage,
          ...toastOptions,
        });
        break;

      case 'auth':
        toast.error('Authentication Error', {
          description: errorMessage,
          duration: 7000,
        });
        break;

      case 'server':
        toast.error('Server Error', {
          description: errorMessage,
          ...toastOptions,
        });
        break;

      case 'client':
        toast.warning('Request Error', {
          description: errorMessage,
          duration: 4000,
        });
        break;

      case 'unknown':
      default:
        toast.error('Error', {
          description: errorMessage,
          ...toastOptions,
        });
        break;
    }
  }
}

/**
 * Create error handler with context
 */
export function createErrorHandler(defaultContext?: ErrorContext) {
  return (error: any, additionalContext?: ErrorContext) => {
    handleError(error, { ...defaultContext, ...additionalContext });
  };
}

/**
 * Wrap async function with error handling
 */
export function withErrorHandling<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  context?: ErrorContext,
): T {
  return (async (...args: any[]) => {
    try {
      return await fn(...args);
    } catch (error) {
      handleError(error, context);
      throw error;
    }
  }) as T;
}

/**
 * Check if error is a specific type
 */
export function isNetworkError(error: any): boolean {
  return classifyError(error) === 'network';
}

export function isAuthError(error: any): boolean {
  return classifyError(error) === 'auth';
}

export function isServerError(error: any): boolean {
  return classifyError(error) === 'server';
}

export function isClientError(error: any): boolean {
  return classifyError(error) === 'client';
}

/**
 * Format error for logging
 */
export function formatErrorForLogging(error: any, context?: ErrorContext): Record<string, any> {
  return {
    type: classifyError(error),
    message: getErrorMessage(error),
    originalMessage: error.message,
    status: error.status || error.response?.status,
    stack: error.stack,
    context,
    timestamp: new Date().toISOString(),
  };
}
