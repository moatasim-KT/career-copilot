/**
 * Optimistic Updates Utility
 * 
 * Provides utilities for optimistic UI updates that revert on error.
 * 
 * Usage:
 * ```tsx
 * import { useOptimisticUpdate } from '@/lib/utils/optimistic';
 * 
 * const [items, setItems] = useState(data);
 * const updateItem = useOptimisticUpdate(setItems);
 * 
 * const handleUpdate = async (id: number, newStatus: string) => {
 *   await updateItem(
 *     // Optimistic update function
 *     (items) => items.map(item => 
 *       item.id === id ? { ...item, status: newStatus } : item
 *     ),
 *     // API call
 *     () => apiClient.updateStatus(id, newStatus),
 *     // Error callback (optional)
 *     (error) => toast.error('Failed to update')
 *   );
 * };
 * ```
 */

'use client';

import { useState, useCallback, useRef } from 'react';

type UpdateFn<T> = (current: T) => T;
type AsyncFn = () => Promise<any>;
type ErrorCallback = (error: Error) => void;
type SuccessCallback<T> = (result: T) => void;

export interface OptimisticUpdateOptions<T = any> {
    onError?: ErrorCallback;
    onSuccess?: SuccessCallback<T>;
    revalidate?: () => void | Promise<void>;
}

/**
 * Hook for optimistic updates
 */
export function useOptimisticUpdate<T>(
    setState: React.Dispatch<React.SetStateAction<T>>,
) {
    const previousStateRef = useRef<T | null>(null);
    const [isUpdating, setIsUpdating] = useState(false);

    const update = useCallback(
        async <R = any>(
            optimisticUpdateFn: UpdateFn<T>,
            apiCall: AsyncFn,
            options?: OptimisticUpdateOptions<R>,
        ): Promise<R | null> => {
            setIsUpdating(true);

            // Store current state for rollback
            setState((current) => {
                previousStateRef.current = current;
                return optimisticUpdateFn(current);
            });

            try {
                const result = await apiCall();

                // Success - call success callback if provided
                if (options?.onSuccess) {
                    options.onSuccess(result);
                }

                // Revalidate data if needed
                if (options?.revalidate) {
                    await options.revalidate();
                }

                return result;
            } catch (error) {
                // Rollback on error
                if (previousStateRef.current !== null) {
                    setState(previousStateRef.current);
                }

                // Call error callback if provided
                if (options?.onError) {
                    options.onError(error as Error);
                }

                return null;
            } finally {
                setIsUpdating(false);
                previousStateRef.current = null;
            }
        },
        [setState],
    );

    return { update, isUpdating };
}

/**
 * Standalone optimistic update function
 */
export async function optimisticUpdate<T, R = any>(
    currentState: T,
    setState: (state: T) => void,
    optimisticUpdateFn: UpdateFn<T>,
    apiCall: AsyncFn,
    options?: OptimisticUpdateOptions<R>,
): Promise<R | null> {
    const previousState = currentState;

    // Apply optimistic update
    setState(optimisticUpdateFn(currentState));

    try {
        const result = await apiCall();

        if (options?.onSuccess) {
            options.onSuccess(result);
        }

        if (options?.revalidate) {
            await options.revalidate();
        }

        return result;
    } catch (error) {
        // Rollback
        setState(previousState);

        if (options?.onError) {
            options.onError(error as Error);
        }

        return null;
    }
}

/**
 * Optimistic update for array operations
 */
export class OptimisticArray<T extends { id: number | string }> {
    constructor(
        private items: T[],
        private setItems: (items: T[]) => void,
    ) { }

    /**
     * Add item optimistically
     */
    async add(
        item: T,
        apiCall: () => Promise<T>,
        options?: OptimisticUpdateOptions<T>,
    ): Promise<T | null> {
        const previousItems = this.items;

        // Add optimistically
        this.setItems([...this.items, item]);

        try {
            const result = await apiCall();

            // Replace temporary item with real one
            this.setItems(
                this.items.map((i) => (i.id === item.id ? result : i)),
            );

            if (options?.onSuccess) {
                options.onSuccess(result);
            }

            return result;
        } catch (error) {
            this.setItems(previousItems);

            if (options?.onError) {
                options.onError(error as Error);
            }

            return null;
        }
    }

    /**
     * Update item optimistically
     */
    async update(
        id: number | string,
        updates: Partial<T>,
        apiCall: () => Promise<T>,
        options?: OptimisticUpdateOptions<T>,
    ): Promise<T | null> {
        const previousItems = this.items;

        // Update optimistically
        this.setItems(
            this.items.map((item) =>
                item.id === id ? { ...item, ...updates } : item,
            ),
        );

        try {
            const result = await apiCall();

            // Replace with actual result
            this.setItems(
                this.items.map((item) => (item.id === id ? result : item)),
            );

            if (options?.onSuccess) {
                options.onSuccess(result);
            }

            return result;
        } catch (error) {
            this.setItems(previousItems);

            if (options?.onError) {
                options.onError(error as Error);
            }

            return null;
        }
    }

    /**
     * Delete item optimistically
     */
    async delete(
        id: number | string,
        apiCall: () => Promise<void>,
        options?: OptimisticUpdateOptions<void>,
    ): Promise<boolean> {
        const previousItems = this.items;

        // Delete optimistically
        this.setItems(this.items.filter((item) => item.id !== id));

        try {
            await apiCall();

            if (options?.onSuccess) {
                options.onSuccess(undefined);
            }

            return true;
        } catch (error) {
            this.setItems(previousItems);

            if (options?.onError) {
                options.onError(error as Error);
            }

            return false;
        }
    }
}

/**
 * Create an optimistic array helper
 */
export function useOptimisticArray<T extends { id: number | string }>(
    items: T[],
    setItems: React.Dispatch<React.SetStateAction<T[]>>,
) {
    return new OptimisticArray(items, setItems);
}
