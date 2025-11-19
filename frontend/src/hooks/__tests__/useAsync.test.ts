import { renderHook, waitFor } from '@testing-library/react';

import { useAsync } from '../useAsync';

describe('useAsync', () => {
    it('should initialize with correct default values', () => {
        const { result } = renderHook(() => useAsync());

        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBe(null);
        expect(result.current.data).toBe(null);
    });

    it('should set loading to true during execution', async () => {
        const { result } = renderHook(() => useAsync<string>());

        const asyncFn = () => new Promise<string>((resolve) => {
            setTimeout(() => resolve('success'), 100);
        });

        result.current.execute(asyncFn);

        await waitFor(() => {
            expect(result.current.loading).toBe(true);
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });
    });

    it('should set data on successful execution', async () => {
        const { result } = renderHook(() => useAsync<string>());

        const asyncFn = () => Promise.resolve('test data');

        await result.current.execute(asyncFn);

        await waitFor(() => {
            expect(result.current.data).toBe('test data');
            expect(result.current.error).toBe(null);
            expect(result.current.loading).toBe(false);
        });
    });

    it('should set error on failed execution', async () => {
        const { result } = renderHook(() => useAsync<string>());

        const asyncFn = () => Promise.reject(new Error('Test error'));

        try {
            await result.current.execute(asyncFn);
        } catch (err) {
            // Expected to throw
        }

        await waitFor(() => {
            expect(result.current.error).toBe('Test error');
            expect(result.current.data).toBe(null);
            expect(result.current.loading).toBe(false);
        });
    });

    it('should handle non-Error exceptions', async () => {
        const { result } = renderHook(() => useAsync<string>());

        const asyncFn = () => Promise.reject('String error');

        try {
            await result.current.execute(asyncFn);
        } catch (err) {
            // Expected to throw
        }

        await waitFor(() => {
            expect(result.current.error).toBe('An error occurred');
            expect(result.current.loading).toBe(false);
        });
    });

    it('should reset state when reset is called', async () => {
        const { result } = renderHook(() => useAsync<string>());

        const asyncFn = () => Promise.resolve('test data');

        await result.current.execute(asyncFn);

        await waitFor(() => {
            expect(result.current.data).toBe('test data');
        });

        await waitFor(() => {
            result.current.reset();
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.error).toBe(null);
            expect(result.current.data).toBe(null);
        });
    });
});
