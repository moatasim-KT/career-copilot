/**
 * Global Error Page
 * 
 * Catches errors in the root layout.
 * This is a fallback for critical errors.
 * 
 * @module app/global-error
 */

'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-neutral-50 px-4 py-8">
          <div className="max-w-lg w-full bg-white rounded-lg shadow-lg p-8">
            {/* Error Icon */}
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
              <AlertCircle className="h-6 w-6 text-red-600" />
            </div>

            {/* Error Title */}
            <h1 className="mt-4 text-2xl font-semibold text-center text-gray-900">
              Critical Error
            </h1>

            {/* Error Message */}
            <p className="mt-3 text-base text-center text-gray-600">
              A critical error occurred. Please refresh the page to continue.
            </p>

            {/* Action button */}
            <div className="mt-6">
              <button
                onClick={reset}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2.5 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh Page
              </button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
