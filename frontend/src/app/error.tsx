/**
 * Next.js Error Page
 * 
 * Global error handler for Next.js app router.
 * Catches errors in server and client components.
 * 
 * @module app/error
 */

'use client';

import { AlertCircle, RefreshCw, Home, Bug } from 'lucide-react';
import { useEffect } from 'react';

import { classifyError, formatErrorForLogging } from '@/lib/errorHandling';
import { logger } from '@/lib/logger';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      logger.error('Error page:', error);
    }

    // Log error for monitoring
    const errorLog = formatErrorForLogging(error, {
      component: 'Error Page',
      metadata: {
        digest: error.digest,
      },
    });

    // In production, send to Sentry or similar
    if (process.env.NODE_ENV === 'production') {
      logger.error('[Error Monitoring]', errorLog);
    }
  }, [error]);

  const errorType = classifyError(error);
  const showTechnicalDetails = process.env.NODE_ENV === 'development';

  const handleReportIssue = () => {
    const issueData = {
      error: error.message,
      digest: error.digest,
      stack: error.stack,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };

    // Copy to clipboard
    navigator.clipboard.writeText(JSON.stringify(issueData, null, 2));
    alert('Error details copied to clipboard. Please share with support.');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900 px-4 py-8">
      <div className="max-w-lg w-full bg-white dark:bg-neutral-800 rounded-lg shadow-lg p-8">
        {/* Error Icon */}
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 dark:bg-red-900/30 rounded-full">
          <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
        </div>

        {/* Error Title */}
        <h1 className="mt-4 text-2xl font-semibold text-center text-gray-900 dark:text-white">
          Something went wrong
        </h1>

        {/* Error Message */}
        <p className="mt-3 text-base text-center text-gray-600 dark:text-gray-300">
          We encountered an unexpected error. Please try again or return to the homepage.
        </p>

        {/* Technical details (development only) */}
        {showTechnicalDetails && (
          <div className="mt-4 p-4 bg-gray-100 dark:bg-neutral-700 rounded-md">
            <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Error Type: {errorType}
            </p>
            <p className="text-xs font-mono text-gray-700 dark:text-gray-300 break-all">
              {error.message}
            </p>
            {error.digest && (
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                Digest: {error.digest}
              </p>
            )}
            {error.stack && (
              <details className="mt-2">
                <summary className="text-xs text-gray-600 dark:text-gray-400 cursor-pointer">
                  Stack trace
                </summary>
                <pre className="mt-2 text-xs text-gray-600 dark:text-gray-400 overflow-auto max-h-40">
                  {error.stack}
                </pre>
              </details>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="mt-6 space-y-3">
          {/* Retry button */}
          <button
            onClick={reset}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2.5 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>

          {/* Go home button */}
          <button
            onClick={() => (window.location.href = '/dashboard')}
            className="w-full flex items-center justify-center gap-2 bg-gray-100 dark:bg-neutral-700 text-gray-700 dark:text-gray-300 py-2.5 px-4 rounded-md hover:bg-gray-200 dark:hover:bg-neutral-600 transition-colors font-medium"
          >
            <Home className="h-4 w-4" />
            Go to Dashboard
          </button>

          {/* Report issue button */}
          <button
            onClick={handleReportIssue}
            className="w-full flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 py-2 px-4 rounded-md hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors text-sm"
          >
            <Bug className="h-4 w-4" />
            Report Issue
          </button>
        </div>

        {/* Help text */}
        <p className="mt-6 text-xs text-center text-gray-500 dark:text-gray-400">
          If this problem persists, please contact support with the error details.
        </p>
      </div>
    </div>
  );
}
