/**
 * Graceful Degradation Hook
 * 
 * Wraps features with error handling and fallback UI.
 * Prevents non-critical feature failures from crashing the app.
 * 
 * @module hooks/useGracefulDegradation
 */

'use client';

import { useState, useCallback, useEffect } from 'react';

interface GracefulDegradationOptions {
  /**
   * Whether the feature is critical (will show error) or non-critical (will hide)
   */
  critical?: boolean;
  /**
   * Whether to log errors to console
   */
  logErrors?: boolean;
  /**
   * Whether to log errors to monitoring service
   */
  logToMonitoring?: boolean;
  /**
   * Custom error handler
   */
  onError?: (error: Error) => void;
  /**
   * Retry configuration
   */
  maxRetries?: number;
  retryDelay?: number;
}

interface GracefulDegradationState {
  error: Error | null;
  hasError: boolean;
  isRetrying: boolean;
  retryCount: number;
}

interface GracefulDegradationReturn extends GracefulDegradationState {
  retry: () => void;
  reset: () => void;
  clearError: () => void;
}

/**
 * Hook to handle graceful degradation of features
 */
export function useGracefulDegradation(
  options: GracefulDegradationOptions = {},
): GracefulDegradationReturn {
  const {
    critical = false,
    logErrors = true,
    logToMonitoring = true,
    onError,
    maxRetries = 3,
    retryDelay = 1000,
  } = options;

  const [state, setState] = useState<GracefulDegradationState>({
    error: null,
    hasError: false,
    isRetrying: false,
    retryCount: 0,
  });

  /**
   * Handle error
   */
  const _handleError = useCallback(
    (error: Error) => {
      // Log to console in development
      if (logErrors && process.env.NODE_ENV === 'development') {
        console.error('[Graceful Degradation]', error);
      }

      // Log to monitoring service
      if (logToMonitoring && process.env.NODE_ENV === 'production') {
        // TODO: Send to Sentry or similar
        console.error('[Error Monitoring]', {
          error: error.message,
          stack: error.stack,
          critical,
        });
      }

      // Call custom error handler
      if (onError) {
        onError(error);
      }

      // Update state
      setState((prev) => ({
        ...prev,
        error,
        hasError: true,
      }));
    },
    [critical, logErrors, logToMonitoring, onError],
  );

  /**
   * Retry the feature
   */
  const retry = useCallback(() => {
    if (state.retryCount >= maxRetries) {
      console.warn('[Graceful Degradation] Max retries reached');
      return;
    }

    setState((prev) => ({
      ...prev,
      isRetrying: true,
      retryCount: prev.retryCount + 1,
    }));

    // Simulate retry delay
    setTimeout(() => {
      setState((prev) => ({
        ...prev,
        isRetrying: false,
        error: null,
        hasError: false,
      }));
    }, retryDelay);
  }, [state.retryCount, maxRetries, retryDelay]);

  /**
   * Reset error state
   */
  const reset = useCallback(() => {
    setState({
      error: null,
      hasError: false,
      isRetrying: false,
      retryCount: 0,
    });
  }, []);

  /**
   * Clear error without resetting retry count
   */
  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
      hasError: false,
    }));
  }, []);

  return {
    ...state,
    retry,
    reset,
    clearError,
  };
}

/**
 * Wrap async function with graceful degradation
 */
export function withGracefulDegradation<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: GracefulDegradationOptions = {},
): T {
  return (async (...args: any[]) => {
    try {
      return await fn(...args);
    } catch (error) {
      const { critical = false, logErrors = true, onError } = options;

      // Log error
      if (logErrors) {
        console.error('[Graceful Degradation]', error);
      }

      // Call custom error handler
      if (onError && error instanceof Error) {
        onError(error);
      }

      // If critical, re-throw error
      if (critical) {
        throw error;
      }

      // Otherwise, return null or undefined
      return null;
    }
  }) as T;
}

/**
 * Hook to wrap component with error boundary-like behavior
 */
export function useFeatureErrorBoundary(
  featureName: string,
  options: GracefulDegradationOptions = {},
) {
  const degradation = useGracefulDegradation(options);

  useEffect(() => {
    // Set up global error handler for this feature
    const handleGlobalError = (event: ErrorEvent) => {
      // Check if error is related to this feature
      if (event.error && event.error.message?.includes(featureName)) {
        event.preventDefault();
        degradation.retry();
      }
    };

    window.addEventListener('error', handleGlobalError);

    return () => {
      window.removeEventListener('error', handleGlobalError);
    };
  }, [featureName, degradation]);

  return degradation;
}

/**
 * Utility to check if feature should be shown
 */
export function shouldShowFeature(
  hasError: boolean,
  critical: boolean = false,
): boolean {
  // Always show critical features (they'll show error UI)
  if (critical) {
    return true;
  }

  // Hide non-critical features if they have errors
  return !hasError;
}
