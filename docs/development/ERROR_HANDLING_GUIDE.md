# Error Handling Guide

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

## Overview

Career Copilot uses a normalized error handling system that provides consistent error responses across the frontend, with clear mappings to backend error formats.

## Architecture

### Backend Error Response Format

The backend returns standardized `ErrorResponse` objects (defined in `backend/app/schemas/api_models.py`):

```python
class ErrorResponse(BaseModel):
    request_id: str          # Correlation ID for tracing
    timestamp: str           # ISO timestamp
    error_code: str          # Short error code (e.g., "VALIDATION_ERROR")
    detail: Any              # Human-readable error message
    field_errors: Dict[str, Any] | None  # Validation errors by field
    suggestions: List[str] | None        # Remediation suggestions
```

### Frontend Error Types

The frontend normalizes all errors into `FrontendError` objects (defined in `frontend/src/lib/api/types/errors.ts`):

```typescript
interface FrontendError {
  status: number;                      // HTTP status code
  code: string;                        // Error code
  message: string;                     // Human-readable message
  fieldErrors?: Record<string, string[]>; // Validation errors
  suggestions?: string[];              // Fix suggestions
  requestId?: string;                  // Request ID for tracing
  raw?: BackendErrorResponse;          // Original response
}
```

## Usage Patterns

### Basic API Call with Error Handling

```typescript
import { fetchApi } from '@/lib/api/client';
import { isValidationError, formatFieldErrors } from '@/lib/api/types/errors';

async function createApplication(data: ApplicationData) {
  const response = await fetchApi<Application>('/applications', {
    method: 'POST',
    body: JSON.stringify(data),
  });

  if (response.error) {
    const error = response.error;
    
    if (isValidationError(error)) {
      // Handle validation errors
      console.error('Validation failed:', formatFieldErrors(error.fieldErrors));
      
      // Show field-specific errors in UI
      Object.entries(error.fieldErrors || {}).forEach(([field, errors]) => {
        showFieldError(field, errors[0]);
      });
    } else {
      // Handle other errors
      showToast(error.message, 'error');
    }
    
    return null;
  }

  return response.data;
}
```

### Checking Error Types

```typescript
import {
  isValidationError,
  isAuthError,
  isForbiddenError,
  isServerError,
  isNetworkError,
} from '@/lib/api/types/errors';

if (isAuthError(error)) {
  // Redirect to login
  router.push('/login');
}

if (isValidationError(error)) {
  // Show validation errors
  displayFieldErrors(error.fieldErrors);
}

if (isServerError(error)) {
  // Show generic error + retry option
  showErrorWithRetry(error.message);
}

if (isNetworkError(error)) {
  // Show connectivity error
  showNetworkError();
}
```

### Displaying Error Messages

```typescript
// Simple error display
if (response.error) {
  toast.error(response.error.message);
}

// With suggestions
if (response.error?.suggestions) {
  toast.error(response.error.message, {
    description: response.error.suggestions.join('\n'),
  });
}

// With field errors
if (response.error?.fieldErrors) {
  const fieldErrorText = formatFieldErrors(response.error.fieldErrors);
  toast.error(response.error.message, {
    description: fieldErrorText,
  });
}
```

### Error Logging and Debugging

```typescript
if (response.error) {
  logger.error('API call failed', {
    endpoint: '/applications',
    status: response.error.status,
    code: response.error.code,
    requestId: response.error.requestId,
    message: response.error.message,
  });
  
  // In development, log full error details
  if (process.env.NODE_ENV === 'development') {
    console.error('Full error:', response.error.raw);
  }
}
```

## Error Codes

The system uses standardized error codes (see `ERROR_CODES` in `frontend/src/lib/api/types/errors.ts`):

### Client Errors (4xx)
- `BAD_REQUEST` (400) - Invalid request
- `UNAUTHORIZED` (401) - Authentication required
- `FORBIDDEN` (403) - Permission denied
- `NOT_FOUND` (404) - Resource not found
- `VALIDATION_ERROR` (422) - Validation failed
- `CONFLICT` (409) - Resource conflict

### Server Errors (5xx)
- `INTERNAL_SERVER_ERROR` (500) - Server error
- `SERVICE_UNAVAILABLE` (503) - Service down
- `GATEWAY_TIMEOUT` (504) - Request timeout

### Network Errors
- `NETWORK_ERROR` (0) - Cannot reach server
- `TIMEOUT_ERROR` (408) - Request timed out

## Retry Logic

The API client automatically retries certain errors:

- **Server errors (5xx)**: Retried up to 3 times with exponential backoff
- **Network errors**: Retried up to 3 times with exponential backoff
- **Client errors (4xx)**: Not retried (fix the request instead)

```typescript
import { shouldRetry } from '@/lib/api/types/errors';

if (shouldRetry(error)) {
  // This error will be automatically retried by the API client
  // Shows: 500, 503, 504, or network errors (status 0)
}
```

## Common Error Scenarios

### Scenario 1: Form Validation Errors

```typescript
async function handleSubmit(formData: FormData) {
  const response = await fetchApi('/applications', {
    method: 'POST',
    body: JSON.stringify(formData),
  });

  if (response.error && isValidationError(response.error)) {
    // Backend returned 422 with field_errors
    setErrors(response.error.fieldErrors || {});
    
    // Show user-friendly message
    toast.error('Please fix the errors in the form');
    return;
  }

  if (response.error) {
    // Other error
    toast.error(response.error.message);
    return;
  }

  // Success
  toast.success('Application submitted!');
  router.push('/applications');
}
```

### Scenario 2: Authentication Errors

```typescript
const response = await fetchApi('/profile', {
  requiresAuth: true,
});

if (response.error && isAuthError(response.error)) {
  // Token expired or invalid
  toast.error('Session expired. Please log in again.');
  
  // Clear auth data
  localStorage.removeItem('auth_token');
  
  // Redirect to login with return URL
  router.push(`/login?returnUrl=${encodeURIComponent(router.pathname)}`);
  return;
}
```

### Scenario 3: Not Found Errors

```typescript
const response = await fetchApi(`/jobs/${jobId}`);

if (response.error?.status === 404) {
  // Show 404 page or message
  setNotFound(true);
  return;
}
```

### Scenario 4: Server Errors with Retry

```typescript
async function loadDashboardData() {
  const response = await fetchApi('/dashboard/stats');

  if (response.error && isServerError(response.error)) {
    // Already retried 3 times automatically
    toast.error('Unable to load dashboard. Please try again.', {
      action: {
        label: 'Retry',
        onClick: () => loadDashboardData(),
      },
    });
    return;
  }

  setDashboardData(response.data);
}
```

### Scenario 5: Network Errors

```typescript
const response = await fetchApi('/jobs/matches');

if (response.error && isNetworkError(response.error)) {
  // No connection to server
  showOfflineBanner('You appear to be offline. Please check your connection.');
  return;
}
```

## Testing Error Handling

### Unit Tests

```typescript
import { parseBackendError, isValidationError } from '@/lib/api/types/errors';

describe('Error parsing', () => {
  it('should parse validation errors', () => {
    const backendError = {
      request_id: 'req-123',
      timestamp: '2025-11-19T10:00:00Z',
      error_code: 'VALIDATION_ERROR',
      detail: 'Invalid email',
      field_errors: {
        email: ['Must be valid email'],
      },
    };

    const error = parseBackendError(422, backendError);

    expect(error.status).toBe(422);
    expect(error.code).toBe('VALIDATION_ERROR');
    expect(error.message).toBe('Invalid email');
    expect(isValidationError(error)).toBe(true);
  });
});
```

### Integration Tests

```typescript
import { fetchApi } from '@/lib/api/client';

describe('API error handling', () => {
  it('should handle 422 validation errors', async () => {
    // Mock fetch to return validation error
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({
        request_id: 'req-123',
        error_code: 'VALIDATION_ERROR',
        detail: 'Invalid data',
        field_errors: { email: ['Required'] },
      }),
    });

    const response = await fetchApi('/test');

    expect(response.error?.status).toBe(422);
    expect(response.error?.fieldErrors).toEqual({ email: ['Required'] });
  });
});
```

## Best Practices

1. **Always check for errors** before accessing `response.data`
2. **Use type-checking helpers** (`isValidationError`, `isAuthError`, etc.) instead of checking status codes directly
3. **Show user-friendly messages** using `error.message` (already translated/formatted)
4. **Display field errors** for validation failures using `formatFieldErrors`
5. **Log errors properly** with `requestId` for debugging
6. **Handle authentication errors** by redirecting to login
7. **Provide retry options** for server and network errors
8. **Don't retry client errors** (4xx) - they need request fixes

## Related Files

- **Type definitions**: `frontend/src/lib/api/types/errors.ts`
- **API client**: `frontend/src/lib/api/client.ts`
- **Backend schema**: `backend/app/schemas/api_models.py`
- **Tests**: `frontend/src/lib/api/__tests__/errors.test.ts`
- **Integration tests**: `frontend/src/lib/api/__tests__/client-errors.test.ts`

## Migration from Legacy Error Handling

If you have code using the old error format (`error: string`), migrate to:

```typescript
// Before
if (response.error) {
  console.error(response.error); // Just a string
}

// After
if (response.error) {
  console.error(response.error.message); // Use .message property
  
  // Access additional error info
  if (response.error.fieldErrors) {
    // Handle validation errors
  }
  if (response.error.suggestions) {
    // Show suggestions to user
  }
}
```

The API client is backward compatible - `response.error` is now a `FrontendError` object instead of a string, but TypeScript will guide you through the migration.
