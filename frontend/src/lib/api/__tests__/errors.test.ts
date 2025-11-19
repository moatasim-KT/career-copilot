/**
 * @jest-environment jsdom
 */

import {
    type BackendErrorResponse,
    type FrontendError,
    ERROR_CODES,
    statusToErrorCode,
    getDefaultErrorMessage,
    parseBackendError,
    formatFieldErrors,
    isValidationError,
    isAuthError,
    isForbiddenError,
    isServerError,
    isNetworkError,
    shouldRetry,
} from '../types/errors';

describe('Error Types and Utilities', () => {
    describe('statusToErrorCode', () => {
        it('should map common HTTP status codes to error codes', () => {
            expect(statusToErrorCode(0)).toBe(ERROR_CODES.NETWORK_ERROR);
            expect(statusToErrorCode(400)).toBe(ERROR_CODES.BAD_REQUEST);
            expect(statusToErrorCode(401)).toBe(ERROR_CODES.UNAUTHORIZED);
            expect(statusToErrorCode(403)).toBe(ERROR_CODES.FORBIDDEN);
            expect(statusToErrorCode(404)).toBe(ERROR_CODES.NOT_FOUND);
            expect(statusToErrorCode(409)).toBe(ERROR_CODES.CONFLICT);
            expect(statusToErrorCode(422)).toBe(ERROR_CODES.VALIDATION_ERROR);
            expect(statusToErrorCode(500)).toBe(ERROR_CODES.INTERNAL_SERVER_ERROR);
            expect(statusToErrorCode(503)).toBe(ERROR_CODES.SERVICE_UNAVAILABLE);
            expect(statusToErrorCode(504)).toBe(ERROR_CODES.GATEWAY_TIMEOUT);
        });

        it('should handle generic 4xx and 5xx codes', () => {
            expect(statusToErrorCode(418)).toBe(ERROR_CODES.BAD_REQUEST);
            expect(statusToErrorCode(502)).toBe(ERROR_CODES.INTERNAL_SERVER_ERROR);
        });

        it('should return UNKNOWN_ERROR for unrecognized codes', () => {
            expect(statusToErrorCode(200)).toBe(ERROR_CODES.UNKNOWN_ERROR);
            // 999 falls into 5xx range, maps to INTERNAL_SERVER_ERROR
            expect(statusToErrorCode(999)).toBe(ERROR_CODES.INTERNAL_SERVER_ERROR);
        });
    });

    describe('getDefaultErrorMessage', () => {
        it('should return appropriate messages for common status codes', () => {
            expect(getDefaultErrorMessage(0)).toContain('connect to the server');
            expect(getDefaultErrorMessage(400)).toContain('Invalid request');
            expect(getDefaultErrorMessage(401)).toContain('Authentication required');
            expect(getDefaultErrorMessage(403)).toContain('permission');
            expect(getDefaultErrorMessage(404)).toContain('not found');
            expect(getDefaultErrorMessage(422)).toContain('Validation failed');
            expect(getDefaultErrorMessage(500)).toContain('server error');
            expect(getDefaultErrorMessage(503)).toContain('temporarily unavailable');
        });

        it('should return generic messages for unknown codes', () => {
            expect(getDefaultErrorMessage(418)).toContain('client error');
            expect(getDefaultErrorMessage(502)).toContain('server error');
            // 999 falls into 5xx range
            expect(getDefaultErrorMessage(999)).toContain('server error');
        });
    });

    describe('parseBackendError', () => {
        it('should parse standard backend error response', () => {
            const backendError: BackendErrorResponse = {
                request_id: 'req-123',
                timestamp: '2025-11-19T10:00:00Z',
                error_code: 'VALIDATION_ERROR',
                detail: 'Invalid email format',
                field_errors: {
                    email: ['Must be a valid email address'],
                },
                suggestions: ['Check email format', 'Remove special characters'],
            };

            const result = parseBackendError(422, backendError);

            expect(result.status).toBe(422);
            expect(result.code).toBe('VALIDATION_ERROR');
            expect(result.message).toBe('Invalid email format');
            expect(result.fieldErrors).toEqual({ email: ['Must be a valid email address'] });
            expect(result.suggestions).toEqual(['Check email format', 'Remove special characters']);
            expect(result.requestId).toBe('req-123');
            expect(result.raw).toBe(backendError);
        });

        it('should handle backend error with object detail', () => {
            const backendError = {
                request_id: 'req-456',
                timestamp: '2025-11-19T10:00:00Z',
                error_code: 'INTERNAL_ERROR',
                detail: { message: 'Database connection failed', code: 'DB_ERROR' },
            };

            const result = parseBackendError(500, backendError);

            expect(result.status).toBe(500);
            expect(result.code).toBe('INTERNAL_ERROR');
            expect(result.message).toContain('server error'); // Falls back to default message
        });

        it('should handle non-standard error response', () => {
            const nonStandardError = {
                message: 'Something went wrong',
                error: 'Internal error',
            };

            const result = parseBackendError(500, nonStandardError);

            expect(result.status).toBe(500);
            expect(result.code).toBe(ERROR_CODES.INTERNAL_SERVER_ERROR);
            expect(result.message).toBe('Something went wrong');
        });

        it('should handle minimal error data', () => {
            const result = parseBackendError(404, {});

            expect(result.status).toBe(404);
            expect(result.code).toBe(ERROR_CODES.NOT_FOUND);
            expect(result.message).toContain('not found');
        });

        it('should handle null/undefined error data', () => {
            const result = parseBackendError(500, null);

            expect(result.status).toBe(500);
            expect(result.code).toBe(ERROR_CODES.INTERNAL_SERVER_ERROR);
            expect(result.message).toContain('server error');
        });
    });

    describe('formatFieldErrors', () => {
        it('should format field errors into readable string', () => {
            const fieldErrors = {
                email: ['Must be valid email', 'Cannot be empty'],
                password: ['Must be at least 8 characters'],
            };

            const result = formatFieldErrors(fieldErrors);

            expect(result).toContain('email: Must be valid email, Cannot be empty');
            expect(result).toContain('password: Must be at least 8 characters');
        });

        it('should return empty string for undefined field errors', () => {
            expect(formatFieldErrors(undefined)).toBe('');
        });

        it('should handle empty field errors object', () => {
            expect(formatFieldErrors({})).toBe('');
        });
    });

    describe('Error Type Checkers', () => {
        describe('isValidationError', () => {
            it('should identify validation errors by status code', () => {
                expect(isValidationError({ status: 422, code: 'ANY', message: 'test' })).toBe(true);
                expect(isValidationError({ status: 400, code: 'ANY', message: 'test' })).toBe(true);
            });

            it('should identify validation errors by error code', () => {
                expect(isValidationError({
                    status: 200,
                    code: ERROR_CODES.VALIDATION_ERROR,
                    message: 'test'
                })).toBe(true);
            });

            it('should identify validation errors by presence of field errors', () => {
                expect(isValidationError({
                    status: 200,
                    code: 'ANY',
                    message: 'test',
                    fieldErrors: { email: ['invalid'] }
                })).toBe(true);
            });

            it('should return false for non-validation errors', () => {
                expect(isValidationError({ status: 500, code: 'SERVER_ERROR', message: 'test' })).toBe(false);
            });
        });

        describe('isAuthError', () => {
            it('should identify auth errors', () => {
                expect(isAuthError({ status: 401, code: 'ANY', message: 'test' })).toBe(true);
                expect(isAuthError({
                    status: 200,
                    code: ERROR_CODES.UNAUTHORIZED,
                    message: 'test'
                })).toBe(true);
            });

            it('should return false for non-auth errors', () => {
                expect(isAuthError({ status: 403, code: 'FORBIDDEN', message: 'test' })).toBe(false);
            });
        });

        describe('isForbiddenError', () => {
            it('should identify forbidden errors', () => {
                expect(isForbiddenError({ status: 403, code: 'ANY', message: 'test' })).toBe(true);
                expect(isForbiddenError({
                    status: 200,
                    code: ERROR_CODES.FORBIDDEN,
                    message: 'test'
                })).toBe(true);
            });

            it('should return false for non-forbidden errors', () => {
                expect(isForbiddenError({ status: 401, code: 'UNAUTHORIZED', message: 'test' })).toBe(false);
            });
        });

        describe('isServerError', () => {
            it('should identify server errors', () => {
                expect(isServerError({ status: 500, code: 'ANY', message: 'test' })).toBe(true);
                expect(isServerError({ status: 503, code: 'ANY', message: 'test' })).toBe(true);
                expect(isServerError({
                    status: 200,
                    code: ERROR_CODES.INTERNAL_SERVER_ERROR,
                    message: 'test'
                })).toBe(true);
            });

            it('should return false for non-server errors', () => {
                expect(isServerError({ status: 400, code: 'BAD_REQUEST', message: 'test' })).toBe(false);
            });
        });

        describe('isNetworkError', () => {
            it('should identify network errors', () => {
                expect(isNetworkError({ status: 0, code: 'ANY', message: 'test' })).toBe(true);
                expect(isNetworkError({
                    status: 200,
                    code: ERROR_CODES.NETWORK_ERROR,
                    message: 'test'
                })).toBe(true);
            });

            it('should return false for non-network errors', () => {
                expect(isNetworkError({ status: 500, code: 'SERVER_ERROR', message: 'test' })).toBe(false);
            });
        });

        describe('shouldRetry', () => {
            it('should suggest retry for server errors', () => {
                expect(shouldRetry({ status: 500, code: 'SERVER_ERROR', message: 'test' })).toBe(true);
                expect(shouldRetry({ status: 503, code: 'SERVICE_UNAVAILABLE', message: 'test' })).toBe(true);
            });

            it('should suggest retry for network errors', () => {
                expect(shouldRetry({ status: 0, code: 'NETWORK_ERROR', message: 'test' })).toBe(true);
            });

            it('should not suggest retry for client errors', () => {
                expect(shouldRetry({ status: 400, code: 'BAD_REQUEST', message: 'test' })).toBe(false);
                expect(shouldRetry({ status: 401, code: 'UNAUTHORIZED', message: 'test' })).toBe(false);
                expect(shouldRetry({ status: 404, code: 'NOT_FOUND', message: 'test' })).toBe(false);
                expect(shouldRetry({ status: 422, code: 'VALIDATION_ERROR', message: 'test' })).toBe(false);
            });
        });
    });
});
