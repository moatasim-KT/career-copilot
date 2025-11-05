'use client';

import { useEffect } from 'react';

import { Button } from '@/components/ui';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log to error reporting service (e.g., Sentry)
        console.error('Application error:', error);

        // You can integrate Sentry here:
        // if (typeof window !== 'undefined') {
        //   Sentry.captureException(error);
        // }
    }, [error]);

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 p-4">
            <div className="max-w-md rounded-lg bg-white p-8 shadow-lg">
                <div className="mb-6 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                        <svg
                            className="h-8 w-8 text-red-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                        </svg>
                    </div>
                    <h2 className="mb-2 text-2xl font-bold text-gray-900">
                        Something went wrong!
                    </h2>
                    <p className="text-gray-600">
                        We&apos;re sorry, but something unexpected happened. Our team has been notified.
                    </p>
                </div>

                {process.env.NODE_ENV === 'development' && (
                    <div className="mb-6 rounded border border-red-200 bg-red-50 p-4">
                        <p className="mb-2 font-mono text-sm font-semibold text-red-800">
                            {error.name}: {error.message}
                        </p>
                        {error.stack && (
                            <pre className="mt-2 max-h-40 overflow-auto text-xs text-red-700">
                                {error.stack}
                            </pre>
                        )}
                    </div>
                )}

                <div className="space-y-2">
                    <Button onClick={reset} className="w-full">
                        Try again
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => (window.location.href = '/')}
                        className="w-full"
                    >
                        Go to homepage
                    </Button>
                </div>

                {error.digest && (
                    <p className="mt-4 text-center text-xs text-gray-400">
                        Error ID: {error.digest}
                    </p>
                )}
            </div>
        </div>
    );
}
