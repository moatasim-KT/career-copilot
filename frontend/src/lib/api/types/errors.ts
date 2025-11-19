/**
 * Backend Error Response Types
 * 
 * Type definitions matching the backend ErrorResponse schema
 * from backend/app/schemas/api_models.py
 * 
 * @module lib/api/types/errors
 */

/**
 * Standardized backend error response
 * 
 * Matches FastAPI ErrorResponse schema:
 * - request_id: Correlation ID for tracing
 * - timestamp: ISO timestamp of error
 * - error_code: Short error code string
 * - detail: Human-readable error message
 * - field_errors: Optional validation errors by field
 * - suggestions: Optional list of remediation suggestions
 */
export interface BackendErrorResponse {
    request_id: string;
    timestamp: string;
    error_code: string;
    detail: string | Record<string, any>;
    field_errors?: Record<string, string[]> | null;
    suggestions?: string[] | null;
}

/**
 * Frontend error representation
 * 
 * Normalized error object for use throughout the frontend
 */
export interface FrontendError {
    /** HTTP status code */
    status: number;
    /** Error code from backend or generated */
    code: string;
    /** Human-readable error message */
    message: string;
    /** Validation errors by field name */
    fieldErrors?: Record<string, string[]>;
    /** Suggestions for fixing the error */
    suggestions?: string[];
    /** Request ID for tracing */
    requestId?: string;
    /** Original backend response (for debugging) */
    raw?: BackendErrorResponse;
}

/**
 * Error codes mapped to HTTP status codes
 */
export const ERROR_CODES = {
    // Client errors (4xx)
    BAD_REQUEST: 'BAD_REQUEST',
    UNAUTHORIZED: 'UNAUTHORIZED',
    FORBIDDEN: 'FORBIDDEN',
    NOT_FOUND: 'NOT_FOUND',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    CONFLICT: 'CONFLICT',

    // Server errors (5xx)
    INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
    SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
    GATEWAY_TIMEOUT: 'GATEWAY_TIMEOUT',

    // Network errors
    NETWORK_ERROR: 'NETWORK_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR',

    // Unknown
    UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

/**
 * Map HTTP status code to error code
 */
export function statusToErrorCode(status: number): ErrorCode {
    if (status === 0) return ERROR_CODES.NETWORK_ERROR;
    if (status === 400) return ERROR_CODES.BAD_REQUEST;
    if (status === 401) return ERROR_CODES.UNAUTHORIZED;
    if (status === 403) return ERROR_CODES.FORBIDDEN;
    if (status === 404) return ERROR_CODES.NOT_FOUND;
    if (status === 409) return ERROR_CODES.CONFLICT;
    if (status === 422) return ERROR_CODES.VALIDATION_ERROR;
    if (status === 500) return ERROR_CODES.INTERNAL_SERVER_ERROR;
    if (status === 503) return ERROR_CODES.SERVICE_UNAVAILABLE;
    if (status === 504) return ERROR_CODES.GATEWAY_TIMEOUT;
    if (status >= 400 && status < 500) return ERROR_CODES.BAD_REQUEST;
    if (status >= 500) return ERROR_CODES.INTERNAL_SERVER_ERROR;
    return ERROR_CODES.UNKNOWN_ERROR;
}

/**
 * Get user-friendly error message for status code
 */
export function getDefaultErrorMessage(status: number): string {
    switch (status) {
        case 0:
            return 'Unable to connect to the server. Please check your internet connection.';
        case 400:
            return 'Invalid request. Please check your input and try again.';
        case 401:
            return 'Authentication required. Please log in to continue.';
        case 403:
            return 'You do not have permission to perform this action.';
        case 404:
            return 'The requested resource was not found.';
        case 409:
            return 'This operation conflicts with existing data.';
        case 422:
            return 'Validation failed. Please check your input.';
        case 500:
            return 'An internal server error occurred. Please try again later.';
        case 503:
            return 'The service is temporarily unavailable. Please try again later.';
        case 504:
            return 'The request timed out. Please try again.';
        default:
            if (status >= 400 && status < 500) {
                return 'A client error occurred. Please check your request.';
            }
            if (status >= 500) {
                return 'A server error occurred. Please try again later.';
            }
            return 'An unknown error occurred.';
    }
}

/**
 * Parse backend error response into frontend error
 */
export function parseBackendError(
    status: number,
    responseData: any,
): FrontendError {
    // Check if response matches BackendErrorResponse structure
    const isBackendError =
        responseData &&
        typeof responseData === 'object' &&
        ('error_code' in responseData || 'detail' in responseData);

    if (isBackendError) {
        const backendError = responseData as Partial<BackendErrorResponse>;

        return {
            status,
            code: backendError.error_code || statusToErrorCode(status),
            message:
                typeof backendError.detail === 'string'
                    ? backendError.detail
                    : getDefaultErrorMessage(status),
            fieldErrors: backendError.field_errors || undefined,
            suggestions: backendError.suggestions || undefined,
            requestId: backendError.request_id,
            raw: backendError as BackendErrorResponse,
        };
    }

    // Fallback for non-standard error responses
    const message =
        responseData?.message ||
        responseData?.error ||
        responseData?.detail ||
        getDefaultErrorMessage(status);

    return {
        status,
        code: statusToErrorCode(status),
        message: typeof message === 'string' ? message : getDefaultErrorMessage(status),
    };
}

/**
 * Format field errors for display
 */
export function formatFieldErrors(fieldErrors?: Record<string, string[]>): string {
    if (!fieldErrors) return '';

    return Object.entries(fieldErrors)
        .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
        .join('\n');
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: FrontendError): boolean {
    return (
        error.status === 422 ||
        error.status === 400 ||
        error.code === ERROR_CODES.VALIDATION_ERROR ||
        !!error.fieldErrors
    );
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: FrontendError): boolean {
    return error.status === 401 || error.code === ERROR_CODES.UNAUTHORIZED;
}

/**
 * Check if error is an authorization error
 */
export function isForbiddenError(error: FrontendError): boolean {
    return error.status === 403 || error.code === ERROR_CODES.FORBIDDEN;
}

/**
 * Check if error is a server error
 */
export function isServerError(error: FrontendError): boolean {
    return error.status >= 500 || error.code === ERROR_CODES.INTERNAL_SERVER_ERROR;
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: FrontendError): boolean {
    return error.status === 0 || error.code === ERROR_CODES.NETWORK_ERROR;
}

/**
 * Check if error should trigger a retry
 */
export function shouldRetry(error: FrontendError): boolean {
    // Retry on server errors and network errors
    return isServerError(error) || isNetworkError(error);
}
