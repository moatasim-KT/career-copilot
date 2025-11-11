# Sentry Error Monitoring Integration Guide

This guide explains how Sentry is integrated into the Career Copilot application for comprehensive error tracking and monitoring.

## Overview

Sentry is configured to:
- Capture and track errors in production
- Provide user context for debugging
- Track performance metrics
- Record session replays for error scenarios
- Filter out non-critical errors

## Configuration Files

### 1. `sentry.server.config.ts`
Server-side Sentry configuration for API routes and server components.

### 2. `sentry.edge.config.ts`
Edge runtime configuration for middleware and edge functions.

### 3. `src/lib/sentry.tsx`
Client-side Sentry utilities and helper functions.

## Environment Variables

Add these to your `.env.local` file:

```env
# Sentry DSN (Data Source Name)
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn-here

# Sentry Auth Token (for source maps upload)
SENTRY_AUTH_TOKEN=your-auth-token-here

# Sentry Organization and Project
SENTRY_ORG=your-org-name
SENTRY_PROJECT=your-project-name

# App Version (for release tracking)
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Usage

### Automatic Error Capture

Errors are automatically captured in:
- React components (via ErrorBoundary)
- API routes (via Sentry middleware)
- Async operations (via error handling utility)

### Manual Error Capture

```typescript
import { captureException, captureMessage } from '@/lib/sentry';

// Capture exception
try {
  await riskyOperation();
} catch (error) {
  captureException(error, {
    tags: { feature: 'job-application' },
    extra: { applicationData: data },
  });
}

// Capture message
captureMessage('User reached application limit', {
  level: 'warning',
  tags: { feature: 'job-application' },
});
```

### User Context

Set user context after authentication:

```typescript
import { setUserContext, clearUserContext } from '@/lib/sentry';

// On login
setUserContext({
  id: user.id,
  email: user.email,
  username: user.username,
});

// On logout
clearUserContext();
```

### Custom Context

Add custom context for debugging:

```typescript
import { setContext } from '@/lib/sentry';

setContext('job_application', {
  jobId: '123',
  company: 'Acme Corp',
  status: 'submitted',
});
```

### Performance Tracking

Track performance of critical operations:

```typescript
import { startTransaction } from '@/lib/sentry';

const transaction = startTransaction('job-search', 'http.request');
try {
  const results = await searchJobs(query);
  transaction.setStatus('ok');
} catch (error) {
  transaction.setStatus('internal_error');
  throw error;
} finally {
  transaction.finish();
}
```

### Breadcrumbs

Add breadcrumbs for debugging context:

```typescript
import { addBreadcrumb } from '@/lib/sentry';

addBreadcrumb({
  category: 'navigation',
  message: 'User navigated to job details',
  level: 'info',
  data: { jobId: '123' },
});
```

## Error Filtering

Sentry is configured to ignore:
- Browser extension errors
- Network errors (handled separately)
- Third-party script errors
- Non-critical warnings in development

## Source Maps

Source maps are automatically uploaded to Sentry during production builds to enable readable stack traces.

### Build Configuration

In `next.config.js`:

```javascript
const { withSentryConfig } = require('@sentry/nextjs');

module.exports = withSentryConfig(
  {
    // Your Next.js config
  },
  {
    // Sentry webpack plugin options
    silent: true,
    org: process.env.SENTRY_ORG,
    project: process.env.SENTRY_PROJECT,
  },
  {
    // Sentry SDK options
    widenClientFileUpload: true,
    transpileClientSDK: true,
    tunnelRoute: '/monitoring',
    hideSourceMaps: true,
    disableLogger: true,
  }
);
```

## Alerting Rules

Configure alerts in Sentry dashboard:

1. **Critical Errors**: Alert immediately for 5xx errors
2. **High Error Rate**: Alert when error rate exceeds 1% of requests
3. **New Issues**: Alert on first occurrence of new error types
4. **Performance Degradation**: Alert when response time exceeds thresholds

## Testing

### Test Error Capture

```typescript
// Trigger test error
import { captureMessage } from '@/lib/sentry';

captureMessage('Test error from Career Copilot', {
  level: 'info',
  tags: { test: 'true' },
});
```

### Verify in Sentry Dashboard

1. Go to Sentry dashboard
2. Navigate to Issues
3. Look for test error
4. Verify user context and breadcrumbs

## Best Practices

1. **Set User Context**: Always set user context after authentication
2. **Add Breadcrumbs**: Add breadcrumbs for important user actions
3. **Use Tags**: Tag errors with feature names for easy filtering
4. **Add Extra Data**: Include relevant data for debugging
5. **Filter Noise**: Configure ignore rules for non-actionable errors
6. **Monitor Performance**: Track performance of critical operations
7. **Review Regularly**: Review Sentry dashboard weekly

## Troubleshooting

### Errors Not Appearing in Sentry

1. Check DSN is configured correctly
2. Verify environment is production
3. Check network requests in browser DevTools
4. Verify Sentry SDK is initialized

### Source Maps Not Working

1. Check auth token is configured
2. Verify organization and project names
3. Check build logs for upload errors
4. Ensure source maps are generated

### Too Many Errors

1. Review and update ignore rules
2. Filter out browser extension errors
3. Adjust sample rates
4. Focus on critical errors first

## Resources

- [Sentry Next.js Documentation](https://docs.sentry.io/platforms/javascript/guides/nextjs/)
- [Sentry Error Filtering](https://docs.sentry.io/platforms/javascript/configuration/filtering/)
- [Sentry Performance Monitoring](https://docs.sentry.io/platforms/javascript/performance/)
- [Sentry Session Replay](https://docs.sentry.io/platforms/javascript/session-replay/)
