import { NextResponse as _NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
class SentryExampleAPIError extends Error {
  constructor(message: string | undefined) {
    super(message);
    this.name = 'SentryExampleAPIError';
  }
}
// A faulty API route to test Sentry's error monitoring
export function GET() {
  // Intentionally raise an error to exercise Sentry/backend monitoring in the example.
  throw new SentryExampleAPIError('This error is raised on the backend called by the example page.');
}
