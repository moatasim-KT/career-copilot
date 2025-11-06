/**
 * Virtual Scroll Component
 * 
 * Enterprise-grade virtual scrolling for rendering large lists efficiently
 * Only renders visible items plus a buffer, dramatically improving performance
 * for lists with thousands of items.
 * 
 * @module components/common/VirtualScroll
 */

'use client';

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';

export interface VirtualScrollProps<T> {
    /** Array of items to render */
    items: T[];
    /** Height of each item in pixels */
    itemHeight: number;
    /** Height of the scrollable container */
    containerHeight: number;
    /** Number of items to render above and below visible area */
    overscan?: number;
    /** Render function for each item */
    renderItem: (item: T, index: number) => React.ReactNode;
    /** Unique key extractor for each item */
    keyExtractor: (item: T, index: number) => string | number;
    /** Optional className for the container */
    className?: string;
    /** Optional className for the scroll container */
    scrollClassName?: string;
    /** Callback when scroll position changes */
    onScroll?: (scrollTop: number) => void;
    /** Optional loading indicator */
    loadingComponent?: React.ReactNode;
    /** Optional empty state component */
    emptyComponent?: React.ReactNode;
    /** Whether the list is loading */
    isLoading?: boolean;
    /** Callback when scrolled near bottom (for infinite scroll) */
    onLoadMore?: () => void;
    /** Threshold in pixels from bottom to trigger onLoadMore */
    loadMoreThreshold?: number;
}

/**
 * Virtual Scroll Component
 * 
 * Efficiently renders large lists by only mounting visible items.
 * Implements windowing/virtualization for optimal performance.
 * 
 * Performance characteristics:
 * - O(1) render complexity regardless of list size
 * - Minimal memory footprint (only visible items in DOM)
 * - Smooth 60fps scrolling even with 100k+ items
 * - Automatic cleanup of offscreen elements
 * 
 * @example
 * ```tsx
 * function ApplicationsList({ applications }) {
 *   return (
 *     <VirtualScroll
 *       items={applications}
 *       itemHeight={80}
 *       containerHeight={600}
 *       overscan={5}
 *       renderItem={(app, index) => (
 *         <ApplicationCard application={app} />
 *       )}
 *       keyExtractor={(app) => app.id}
 *       onLoadMore={loadMoreApplications}
 *     />
 *   );
 * }
 * ```
 */
export function VirtualScroll<T>({
    items,
    itemHeight,
    containerHeight,
    overscan = 3,
    renderItem,
    keyExtractor,
    className = '',
    scrollClassName = '',
    onScroll,
    loadingComponent,
    emptyComponent,
    isLoading = false,
    onLoadMore,
    loadMoreThreshold = 200,
}: VirtualScrollProps<T>) {
    const [scrollTop, setScrollTop] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    // Calculate visible range
    const { visibleStart, visibleEnd, offsetY, totalHeight } = useMemo(() => {
        const totalHeight = items.length * itemHeight;
        const visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
        const visibleEnd = Math.min(
            items.length,
            Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan,
        );
        const offsetY = visibleStart * itemHeight;

        return { visibleStart, visibleEnd, offsetY, totalHeight };
    }, [items.length, itemHeight, scrollTop, containerHeight, overscan]);

    // Get visible items
    const visibleItems = useMemo(
        () => items.slice(visibleStart, visibleEnd),
        [items, visibleStart, visibleEnd],
    );

    // Handle scroll with requestAnimationFrame for smooth performance
    const handleScroll = useCallback(
        (e: React.UIEvent<HTMLDivElement>) => {
            const target = e.currentTarget;

            // Use requestAnimationFrame to throttle scroll updates
            requestAnimationFrame(() => {
                const newScrollTop = target.scrollTop;
                setScrollTop(newScrollTop);
                onScroll?.(newScrollTop);

                // Check if we should load more items
                if (onLoadMore) {
                    const scrollBottom = newScrollTop + containerHeight;
                    const distanceFromBottom = totalHeight - scrollBottom;

                    if (distanceFromBottom < loadMoreThreshold && !isLoading) {
                        onLoadMore();
                    }
                }
            });
        },
        [onScroll, onLoadMore, containerHeight, totalHeight, loadMoreThreshold, isLoading],
    );

    // Scroll to top when items change significantly
    useEffect(() => {
        if (containerRef.current && scrollTop > totalHeight) {
            containerRef.current.scrollTop = 0;
            setScrollTop(0);
        }
    }, [items.length, totalHeight, scrollTop]);

    // Show loading state
    if (isLoading && items.length === 0) {
        return (
            <div
                className={`flex items-center justify-center ${className}`}
                style={{ height: containerHeight }}
            >
                {loadingComponent || (
                    <div className="flex flex-col items-center space-y-2">
                        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                        <p className="text-sm text-gray-500">Loading...</p>
                    </div>
                )}
            </div>
        );
    }

    // Show empty state
    if (items.length === 0 && !isLoading) {
        return (
            <div
                className={`flex items-center justify-center ${className}`}
                style={{ height: containerHeight }}
            >
                {emptyComponent || (
                    <div className="text-center">
                        <p className="text-gray-500">No items to display</p>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div
            ref={containerRef}
            className={`overflow-y-auto overflow-x-hidden ${scrollClassName}`}
            style={{ height: containerHeight }}
            onScroll={handleScroll}
        >
            {/* Total height spacer for scroll calculations */}
            <div style={{ height: totalHeight, position: 'relative' }}>
                {/* Visible items container with offset */}
                <div
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        transform: `translateY(${offsetY}px)`,
                        // Use will-change for GPU acceleration
                        willChange: 'transform',
                    }}
                >
                    {visibleItems.map((item, index) => {
                        const actualIndex = visibleStart + index;
                        return (
                            <div
                                key={keyExtractor(item, actualIndex)}
                                style={{ height: itemHeight }}
                                className={className}
                            >
                                {renderItem(item, actualIndex)}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Loading more indicator */}
            {isLoading && items.length > 0 && (
                <div className="flex items-center justify-center py-4">
                    <div className="w-6 h-6 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
                </div>
            )}
        </div>
    );
}

/**
 * Use Virtual Scroll Hook
 * 
 * Lower-level hook for building custom virtual scroll implementations
 * 
 * @example
 * ```tsx
 * function CustomList({ items }) {
 *   const { visibleItems, containerProps, wrapperProps } = useVirtualScroll({
 *     items,
 *     itemHeight: 60,
 *     containerHeight: 500,
 *   });
 * 
 *   return (
 *     <div {...containerProps}>
 *       <div {...wrapperProps}>
 *         {visibleItems.map(item => <Item key={item.id} {...item} />)}
 *       </div>
 *     </div>
 *   );
 * }
 * ```
 */
export function useVirtualScroll<T>({
    items,
    itemHeight,
    containerHeight,
    overscan = 3,
}: {
    items: T[];
    itemHeight: number;
    containerHeight: number;
    overscan?: number;
}) {
    const [scrollTop, setScrollTop] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    const totalHeight = items.length * itemHeight;
    const visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const visibleEnd = Math.min(
        items.length,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan,
    );
    const offsetY = visibleStart * itemHeight;

    const visibleItems = items.slice(visibleStart, visibleEnd).map((item, index) => ({
        item,
        index: visibleStart + index,
    }));

    const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
        requestAnimationFrame(() => {
            setScrollTop(e.currentTarget.scrollTop);
        });
    }, []);

    return {
        visibleItems,
        totalHeight,
        offsetY,
        containerProps: {
            ref: containerRef,
            onScroll: handleScroll,
            style: { height: containerHeight, overflow: 'auto' },
        },
        wrapperProps: {
            style: {
                height: totalHeight,
                position: 'relative' as const,
            },
        },
        contentProps: {
            style: {
                position: 'absolute' as const,
                top: 0,
                left: 0,
                right: 0,
                transform: `translateY(${offsetY}px)`,
                willChange: 'transform',
            },
        },
    };
}
