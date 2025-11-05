import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react';

import { useDebounce } from '../useDebounce';

describe('useDebounce', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.runOnlyPendingTimers();
        jest.useRealTimers();
    });

    it('should return initial value immediately', () => {
        const { result } = renderHook(() => useDebounce('initial', 500));

        expect(result.current).toBe('initial');
    });

    it('should debounce value changes', () => {
        const { result, rerender } = renderHook(
            ({ value, delay }) => useDebounce(value, delay),
            {
                initialProps: { value: 'initial', delay: 500 },
            },
        );

        expect(result.current).toBe('initial');

        rerender({ value: 'updated', delay: 500 });

        // Value should not change immediately
        expect(result.current).toBe('initial');

        // Fast-forward time
        act(() => {
            jest.advanceTimersByTime(500);
        });

        // Value should now be updated
        expect(result.current).toBe('updated');
    });

    it('should cancel previous timeout on rapid changes', () => {
        const { result, rerender } = renderHook(
            ({ value, delay }) => useDebounce(value, delay),
            {
                initialProps: { value: 'initial', delay: 500 },
            },
        );

        rerender({ value: 'first', delay: 500 });

        act(() => {
            jest.advanceTimersByTime(200);
        });

        rerender({ value: 'second', delay: 500 });

        act(() => {
            jest.advanceTimersByTime(200);
        });

        // Should still be initial
        expect(result.current).toBe('initial');

        act(() => {
            jest.advanceTimersByTime(300);
        });

        // Should now be 'second', skipping 'first'
        expect(result.current).toBe('second');
    });

    it('should respect custom delay', () => {
        const { result, rerender } = renderHook(
            ({ value, delay }) => useDebounce(value, delay),
            {
                initialProps: { value: 'initial', delay: 1000 },
            },
        );

        rerender({ value: 'updated', delay: 1000 });

        act(() => {
            jest.advanceTimersByTime(500);
        });

        expect(result.current).toBe('initial');

        act(() => {
            jest.advanceTimersByTime(500);
        });

        expect(result.current).toBe('updated');
    });

    it('should handle different value types', () => {
        const { result, rerender } = renderHook(
            ({ value, delay }) => useDebounce(value, delay),
            {
                initialProps: { value: 0, delay: 500 },
            },
        );

        rerender({ value: 42, delay: 500 });

        act(() => {
            jest.advanceTimersByTime(500);
        });

        expect(result.current).toBe(42);
    });
});
