/**
 * @jest-environment jsdom
 */

import { fetchApi } from '../client';
import { ERROR_CODES } from '../types/errors';

// Mock fetch globally
global.fetch = jest.fn();

describe('API Client Error Handling Integration', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Clear localStorage
        localStorage.clear();
    });

    describe('Backend ErrorResponse Parsing', () => {
        it('should parse standard backend error response (422 validation)', async () => {
            const mockError = {
                request_id: 'req-123',
                timestamp: '2025-11-19T10:00:00Z',
                error_code: 'VALIDATION_ERROR',
                detail: 'Invalid email format',
                field_errors: {
                    email: ['Must be a valid email address'],
                    password: ['Must be at least 8 characters'],
                },
                suggestions: ['Check email format', 'Use a stronger password'],
            };

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 422,
                statusText: 'Unprocessable Entity',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => mockError,
            });

            const response = await fetchApi('/test/endpoint', { method: 'POST' });

            expect(response.status).toBe(422);
            expect(response.error).toBeDefined();
            expect(response.error?.code).toBe('VALIDATION_ERROR');
            expect(response.error?.message).toBe('Invalid email format');
            expect(response.error?.fieldErrors).toEqual({
                email: ['Must be a valid email address'],
                password: ['Must be at least 8 characters'],
            });
            expect(response.error?.suggestions).toEqual(['Check email format', 'Use a stronger password']);
            expect(response.error?.requestId).toBe('req-123');
        });

        it('should parse backend error response (401 unauthorized)', async () => {
            const mockError = {
                request_id: 'req-456',
                timestamp: '2025-11-19T10:00:00Z',
                error_code: 'UNAUTHORIZED',
                detail: 'Invalid or expired token',
                suggestions: ['Please log in again'],
            };

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 401,
                statusText: 'Unauthorized',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => mockError,
            });

            const response = await fetchApi('/test/endpoint');

            expect(response.status).toBe(401);
            expect(response.error).toBeDefined();
            expect(response.error?.code).toBe('UNAUTHORIZED');
            expect(response.error?.message).toBe('Invalid or expired token');
            expect(response.error?.suggestions).toEqual(['Please log in again']);
        });

        it('should parse backend error response (403 forbidden)', async () => {
            const mockError = {
                request_id: 'req-789',
                timestamp: '2025-11-19T10:00:00Z',
                error_code: 'FORBIDDEN',
                detail: 'You do not have access to this resource',
            };

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 403,
                statusText: 'Forbidden',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => mockError,
            });

            const response = await fetchApi('/test/endpoint');

            expect(response.status).toBe(403);
            expect(response.error).toBeDefined();
            expect(response.error?.code).toBe('FORBIDDEN');
            expect(response.error?.message).toBe('You do not have access to this resource');
        });

        it('should parse backend error response (404 not found)', async () => {
            const mockError = {
                request_id: 'req-101',
                timestamp: '2025-11-19T10:00:00Z',
                error_code: 'NOT_FOUND',
                detail: 'Job with ID 999 not found',
            };

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 404,
                statusText: 'Not Found',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => mockError,
            });

            const response = await fetchApi('/jobs/999');

            expect(response.status).toBe(404);
            expect(response.error).toBeDefined();
            expect(response.error?.code).toBe('NOT_FOUND');
            expect(response.error?.message).toBe('Job with ID 999 not found');
        });

        it('should parse backend error response (500 internal server error)', async () => {
            const mockError = {
                request_id: 'req-202',
                timestamp: '2025-11-19T10:00:00Z',
                error_code: 'INTERNAL_SERVER_ERROR',
                detail: 'Database connection failed',
                suggestions: ['Try again later', 'Contact support if problem persists'],
            };

            // Mock multiple calls for retry logic (500 errors are retried)
            const mockResponse = {
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => mockError,
            };

            (global.fetch as jest.Mock)
                .mockResolvedValueOnce(mockResponse)
                .mockResolvedValueOnce(mockResponse)
                .mockResolvedValueOnce(mockResponse);

            const response = await fetchApi('/test/endpoint');

            expect(response.status).toBe(500);
            expect(response.error).toBeDefined();
            expect(response.error?.code).toBe('INTERNAL_SERVER_ERROR');
            expect(response.error?.message).toBe('Database connection failed');
            expect(response.error?.suggestions).toEqual(['Try again later', 'Contact support if problem persists']);
        });
    });

    describe('Non-Standard Error Response Handling', () => {
        it('should handle error response with only detail field', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => ({ detail: 'Invalid request parameters' }),
            });

            const response = await fetchApi('/test/endpoint');

            expect(response.status).toBe(400);
            expect(response.error).toBeDefined();
            expect(response.error?.code).toBe(ERROR_CODES.BAD_REQUEST);
            expect(response.error?.message).toBe('Invalid request parameters');
        });

        it('should handle error response with message field', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => ({ message: 'Something went wrong' }),
            });

            const response = await fetchApi('/test/endpoint');

            expect(response.status).toBe(400);
            expect(response.error).toBeDefined();
            expect(response.error?.message).toBe('Something went wrong');
        });

        it('should fallback to default message for unrecognized error format', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => ({ unknown_field: 'value' }),
            });

            const response = await fetchApi('/test/endpoint');

            expect(response.status).toBe(400);
            expect(response.error).toBeDefined();
            expect(response.error?.message).toContain('Invalid request');
        });
    });

    describe('Network Error Handling', () => {
        it('should handle network errors', async () => {
            (global.fetch as jest.Mock).mockRejectedValueOnce(new TypeError('Failed to fetch'));

            const response = await fetchApi('/test/endpoint');

            expect(response.status).toBe(0);
            expect(response.error).toBeDefined();
            expect(response.error?.code).toBe(ERROR_CODES.NETWORK_ERROR);
            expect(response.error?.message).toContain('connect to the server');
        });

        it('should handle fetch rejections', async () => {
            (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network request failed'));

            const response = await fetchApi('/test/endpoint');

            expect(response.error).toBeDefined();
            expect(response.status).toBe(0);
        });
    });

    describe('Success Response Handling', () => {
        it('should return data for successful response', async () => {
            const mockData = { id: 1, name: 'Test Job', company: 'Test Company' };

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => mockData,
            });

            const response = await fetchApi('/jobs/1');

            expect(response.status).toBe(200);
            expect(response.data).toEqual(mockData);
            expect(response.error).toBeUndefined();
        });

        it('should handle 201 created responses', async () => {
            const mockData = { id: 2, status: 'created' };

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 201,
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => mockData,
            });

            const response = await fetchApi('/applications', { method: 'POST' });

            expect(response.status).toBe(201);
            expect(response.data).toEqual(mockData);
            expect(response.error).toBeUndefined();
        });

        it('should handle 204 no content responses', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 204,
                headers: new Headers(),
            });

            const response = await fetchApi('/applications/1', { method: 'DELETE' });

            expect(response.status).toBe(204);
            expect(response.error).toBeUndefined();
        });
    });

    describe('Authentication Header Injection', () => {
        it('should not add auth header when requiresAuth is false', async () => {
            localStorage.setItem('auth_token', 'test-token');

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => ({}),
            });

            await fetchApi('/test/endpoint', { requiresAuth: false });

            const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
            const headers = fetchCall[1].headers;
            expect(headers.Authorization).toBeUndefined();
        });

        it('should add auth header when requiresAuth is true', async () => {
            localStorage.setItem('auth_token', 'test-token-123');

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                headers: new Headers({ 'content-type': 'application/json' }),
                json: async () => ({}),
            });

            await fetchApi('/test/endpoint', { requiresAuth: true });

            const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
            const headers = fetchCall[1].headers;
            expect(headers.Authorization).toBe('Bearer test-token-123');
        });
    });
});
