import { useState, useCallback } from 'react';

/**
 * Generic async state management hook
 * @template T - The type of data being fetched
 * @returns Object containing loading, error, data states and execute function
 */
export function useAsync<T>() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<T | null>(null);

    /**
     * Execute an async function and manage its state
     * @param asyncFunction - The async function to execute
     */
    const execute = useCallback(async (asyncFunction: () => Promise<T>) => {
        setLoading(true);
        setError(null);

        try {
            const result = await asyncFunction();
            setData(result);
            return result;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'An error occurred';
            setError(errorMessage);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const reset = useCallback(() => {
        setLoading(false);
        setError(null);
        setData(null);
    }, []);

    return { loading, error, data, execute, reset };
}
