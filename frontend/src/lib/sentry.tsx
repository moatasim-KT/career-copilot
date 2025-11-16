/**
 * Sentry Error Tracking Integration
 * 
 * Enterprise-grade error tracking with Sentry for production monitoring,
 * source maps, user context, and performance traces.
 * 
 * @module lib/sentry
 */

'use client';

import { logger } from '@/lib/logger';

// Dynamic import to handle optional dependency
let Sentry: any = null;

// Try to import Sentry if available
if (typeof window !== 'undefined') {
  try {
    Sentry = require('@sentry/nextjs');
  } catch {
    logger.warn('Sentry is not installed. Error tracking will be disabled.');
  }
}

export interface SentryConfig {
  dsn: string;
  environment: string;
  release?: string;
  tracesSampleRate?: number;
  replaysSessionSampleRate?: number;
  replaysOnErrorSampleRate?: number;
  enabled?: boolean;
}

/**
 * Initialize Sentry
 * 
 * Call this in your app initialization (e.g., _app.tsx or layout.tsx)
 * 
 * @example
 * ```tsx
 * initSentry({
 *   dsn: process.env.NEXT_PUBLIC_SENTRY_DSN!,
 *   environment: process.env.NODE_ENV,
 *   release: process.env.NEXT_PUBLIC_APP_VERSION,
 * });
 * ```
 */
export function initSentry(config: SentryConfig): void {
  if (!Sentry) {
    logger.warn('Sentry not available. Error tracking disabled.');
    return;
  }

  if (!config.enabled && process.env.NODE_ENV !== 'production') {
    logger.info('Sentry disabled in development');
    return;
  }

  Sentry.init({
    dsn: config.dsn,
    environment: config.environment,
    release: config.release,

    // Performance Monitoring
    tracesSampleRate: config.tracesSampleRate ?? 0.1, // 10% of transactions

    // Session Replay
    replaysSessionSampleRate: config.replaysSessionSampleRate ?? 0.1, // 10% of sessions
    replaysOnErrorSampleRate: config.replaysOnErrorSampleRate ?? 1.0, // 100% of errors

    // Integrations
    integrations: [
      new Sentry.BrowserTracing({
        tracePropagationTargets: ['localhost', /^https:\/\/.*\.vercel\.app/],
      }),
      new Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],

    // Error filtering
    beforeSend(event: any, hint: any) {
      // Filter out non-error events in development
      if (config.environment === 'development' && !event.exception) {
        return null;
      }

      // Don't send errors from browser extensions
      const error = hint.originalException as Error;
      if (error?.stack?.includes('chrome-extension://')) {
        return null;
      }

      return event;
    },

    // Ignore certain errors
    ignoreErrors: [
      // Browser extension errors
      'ResizeObserver loop limit exceeded',
      'Non-Error promise rejection captured',

      // Network errors
      'NetworkError',
      'Failed to fetch',

      // Third-party errors
      /Loading chunk \d+ failed/,
    ],
  });
}

/**
 * Set user context for error tracking
 * 
 * @example
 * ```tsx
 * setUserContext({
 *   id: user.id,
 *   email: user.email,
 *   username: user.username,
 * });
 * ```
 */
export function setUserContext(user: {
  id: string;
  email?: string;
  username?: string;
  [key: string]: any;
}): void {
  if (!Sentry) return;
  Sentry.setUser({
    email: user.email,
    username: user.username,
    id: user.id,
  });
}

/**
 * Clear user context (e.g., on logout)
 */
export function clearUserContext(): void {
  if (!Sentry) return;
  Sentry.setUser(null);
}

/**
 * Set custom context
 * 
 * @example
 * ```tsx
 * setContext('job_application', {
 *   jobId: '123',
 *   company: 'Acme Corp',
 *   status: 'submitted',
 * });
 * ```
 */
export function setContext(name: string, context: Record<string, any>): void {
  if (!Sentry) return;
  Sentry.setContext(name, context);
}

/**
 * Capture exception manually
 * 
 * @example
 * ```tsx
 * try {
 *   await submitApplication(data);
 * } catch (error) {
 *   captureException(error, {
 *     tags: { feature: 'job-application' },
 *     extra: { applicationData: data },
 *   });
 * }
 * ```
 */
export function captureException(
  error: Error,
  context?: {
    tags?: Record<string, string>;
    extra?: Record<string, any>;
    level?: string;
  },
): void {
  if (!Sentry) return;

  if (context?.tags) {
    Object.entries(context.tags).forEach(([key, value]) => {
      Sentry.setTag(key, value);
    });
  }

  if (context?.extra) {
    Object.entries(context.extra).forEach(([key, value]) => {
      Sentry.setExtra(key, value);
    });
  }

  Sentry.captureException(error, {
    level: context?.level ?? 'error',
  });
}

/**
 * Capture message manually
 * 
 * @example
 * ```tsx
 * captureMessage('User reached application limit', {
 *   level: 'warning',
 *   tags: { feature: 'job-application' },
 * });
 * ```
 */
export function captureMessage(
  message: string,
  context?: {
    tags?: Record<string, string>;
    extra?: Record<string, any>;
    level?: string;
  },
): void {
  if (!Sentry) return;

  if (context?.tags) {
    Object.entries(context.tags).forEach(([key, value]) => {
      Sentry.setTag(key, value);
    });
  }

  if (context?.extra) {
    Object.entries(context.extra).forEach(([key, value]) => {
      Sentry.setExtra(key, value);
    });
  }

  Sentry.captureMessage(message, context?.level ?? 'info');
}

/**
 * Start a performance transaction
 * 
 * @example
 * ```tsx
 * const transaction = startTransaction('job-search', 'http.request');
 * try {
 *   const results = await searchJobs(query);
 *   transaction.setStatus('ok');
 * } catch (error) {
 *   transaction.setStatus('internal_error');
 *   throw error;
 * } finally {
 *   transaction.finish();
 * }
 * ```
 */
export function startTransaction(
  name: string,
  op: string,
  data?: Record<string, any>,
): any {
  if (!Sentry) return null;
  return Sentry.startTransaction({
    name,
    op,
    data,
  });
}

/**
 * Add breadcrumb for debugging context
 * 
 * @example
 * ```tsx
 * addBreadcrumb({
 *   category: 'navigation',
 *   message: 'User navigated to job details',
 *   level: 'info',
 *   data: { jobId: '123' },
 * });
 * ```
 */
export function addBreadcrumb(breadcrumb: {
  category: string;
  message: string;
  level?: string;
  data?: Record<string, any>;
}): void {
  if (!Sentry) return;
  Sentry.addBreadcrumb({
    category: breadcrumb.category,
    message: breadcrumb.message,
    level: breadcrumb.level ?? 'info',
    data: breadcrumb.data,
  });
}

/**
 * Error boundary fallback component
 * 
 * @example
 * ```tsx
 * import { ErrorBoundary } from '@sentry/nextjs';
 * 
 * <ErrorBoundary fallback={ErrorFallback}>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
export function ErrorFallback({
  error,
  resetError,
}: {
  error: Error;
  resetError: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md rounded-lg bg-white p-8 shadow-lg">
        <div className="mb-4 flex items-center justify-center">
          <div className="rounded-full bg-red-100 p-3">
            <svg
              className="h-8 w-8 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
        </div>

        <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
          Something went wrong
        </h1>

        <p className="mb-6 text-center text-gray-600">
          We&apos;re sorry for the inconvenience. Our team has been notified and is working on a fix.
        </p>

        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm font-medium text-red-800">Error details:</p>
            <p className="mt-1 text-sm text-red-700">{error.message}</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={resetError}
            className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Try again
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="flex-1 rounded-md bg-gray-200 px-4 py-2 text-gray-900 hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Go home
          </button>
        </div>
      </div>
    </div>
  );
}

export { Sentry };
