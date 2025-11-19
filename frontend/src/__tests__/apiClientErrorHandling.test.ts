/**
 * @jest-environment jsdom
 * 
 * DEPRECATED: This test file tests the legacy APIClient from api.ts
 * See src/lib/api/__tests__/client-errors.test.ts for new error handling tests
 * using the fetchApi function from client.ts
 */

import { apiClient } from '@/lib/api';

describe.skip('APIClient error handling (LEGACY - use client-errors.test.ts instead)', () => {
    const originalFetch = global.fetch;

    beforeEach(() => {
        global.fetch = jest.fn();
    });

    afterEach(() => {
        global.fetch = originalFetch as any;
    });

    it('returns validation error on 400', async () => {
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: false,
            status: 400,
            text: async () => 'Bad Request',
            url: 'http://localhost:8002/api/v1/test',
        } as any);

        const res = await apiClient.get('/api/v1/test');
        expect(res.error).toContain('Bad Request');
    });

    it('returns validation error on 422', async () => {
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: false,
            status: 422,
            text: async () => 'Unprocessable Entity',
            url: 'http://localhost:8002/api/v1/test',
        } as any);

        const res = await apiClient.get('/api/v1/test');
        expect(res.error).toContain('Unprocessable Entity');
    });

    it('returns server error on 500', async () => {
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: false,
            status: 500,
            text: async () => 'Server Error',
            url: 'http://localhost:8002/api/v1/test',
        } as any);

        const res = await apiClient.get('/api/v1/test');
        expect(res.error).toContain('Server Error');
    });
});
