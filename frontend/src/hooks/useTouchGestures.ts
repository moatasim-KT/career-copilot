/**
 * Touch Gestures Hook
 * 
 * Enterprise-grade touch gesture detection for mobile interfaces
 * Supports swipe, pinch, long-press, and multi-touch gestures
 * 
 * @module hooks/useTouchGestures
 */

'use client';

import { useRef, useEffect, useCallback } from 'react';

export type SwipeDirection = 'up' | 'down' | 'left' | 'right';

export interface TouchGestureHandlers {
    /** Called when a swipe gesture is detected */
    onSwipe?: (direction: SwipeDirection, distance: number) => void;
    /** Called when a tap is detected */
    onTap?: (x: number, y: number) => void;
    /** Called when a long press is detected */
    onLongPress?: (x: number, y: number) => void;
    /** Called when a pinch gesture is detected */
    onPinch?: (scale: number) => void;
    /** Called when touch starts */
    onTouchStart?: (event: TouchEvent) => void;
    /** Called when touch moves */
    onTouchMove?: (event: TouchEvent) => void;
    /** Called when touch ends */
    onTouchEnd?: (event: TouchEvent) => void;
}

export interface TouchGestureOptions {
    /** Minimum distance (in px) for a swipe to be detected */
    swipeThreshold?: number;
    /** Maximum time (in ms) for a tap to be detected */
    tapThreshold?: number;
    /** Minimum time (in ms) for a long press to be detected */
    longPressThreshold?: number;
    /** Whether to prevent default touch behavior */
    preventDefault?: boolean;
    /** Whether to stop event propagation */
    stopPropagation?: boolean;
}

interface TouchPoint {
    x: number;
    y: number;
    time: number;
}

const DEFAULT_OPTIONS: Required<TouchGestureOptions> = {
    swipeThreshold: 50,
    tapThreshold: 300,
    longPressThreshold: 500,
    preventDefault: false,
    stopPropagation: false,
};

/**
 * Touch Gestures Hook
 * 
 * @param handlers - Gesture event handlers
 * @param options - Configuration options
 * @returns Ref to attach to the target element
 * 
 * @example
 * ```tsx
 * function SwipeableCard() {
 *   const cardRef = useTouchGestures({
 *     onSwipe: (direction) => {
 *       if (direction === 'left') deleteCard();
 *       if (direction === 'right') archiveCard();
 *     },
 *     onLongPress: () => openContextMenu(),
 *   }, {
 *     swipeThreshold: 100,
 *   });
 * 
 *   return <div ref={cardRef}>Swipe me!</div>;
 * }
 * ```
 */
export function useTouchGestures<T extends HTMLElement = HTMLDivElement>(
    handlers: TouchGestureHandlers = {},
    options: TouchGestureOptions = {},
) {
    const elementRef = useRef<T>(null);
    const startPoint = useRef<TouchPoint | null>(null);
    const longPressTimer = useRef<NodeJS.Timeout | null>(null);
    const initialDistance = useRef<number>(0);

    const opts = { ...DEFAULT_OPTIONS, ...options };

    /**
     * Calculate distance between two touch points
     */
    const getTouchDistance = useCallback((touch1: Touch, touch2: Touch): number => {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }, []);

    /**
     * Handle touch start
     */
    const handleTouchStart = useCallback(
        (event: TouchEvent) => {
            if (opts.preventDefault) event.preventDefault();
            if (opts.stopPropagation) event.stopPropagation();

            handlers.onTouchStart?.(event);

            const touch = event.touches[0];
            startPoint.current = {
                x: touch.clientX,
                y: touch.clientY,
                time: Date.now(),
            };

            // Handle multi-touch for pinch
            if (event.touches.length === 2) {
                initialDistance.current = getTouchDistance(event.touches[0], event.touches[1]);
            }

            // Set up long press detection
            if (handlers.onLongPress) {
                longPressTimer.current = setTimeout(() => {
                    if (startPoint.current) {
                        handlers.onLongPress!(startPoint.current.x, startPoint.current.y);
                    }
                }, opts.longPressThreshold);
            }
        },
        [handlers, opts, getTouchDistance],
    );

    /**
     * Handle touch move
     */
    const handleTouchMove = useCallback(
        (event: TouchEvent) => {
            if (opts.preventDefault) event.preventDefault();
            if (opts.stopPropagation) event.stopPropagation();

            handlers.onTouchMove?.(event);

            // Cancel long press if finger moves
            if (longPressTimer.current) {
                clearTimeout(longPressTimer.current);
                longPressTimer.current = null;
            }

            // Handle pinch gesture
            if (event.touches.length === 2 && handlers.onPinch) {
                const currentDistance = getTouchDistance(event.touches[0], event.touches[1]);
                const scale = currentDistance / initialDistance.current;
                handlers.onPinch(scale);
            }
        },
        [handlers, opts, getTouchDistance],
    );

    /**
     * Handle touch end
     */
    const handleTouchEnd = useCallback(
        (event: TouchEvent) => {
            if (opts.preventDefault) event.preventDefault();
            if (opts.stopPropagation) event.stopPropagation();

            handlers.onTouchEnd?.(event);

            // Clear long press timer
            if (longPressTimer.current) {
                clearTimeout(longPressTimer.current);
                longPressTimer.current = null;
            }

            if (!startPoint.current) return;

            const touch = event.changedTouches[0];
            const endPoint = {
                x: touch.clientX,
                y: touch.clientY,
                time: Date.now(),
            };

            const deltaX = endPoint.x - startPoint.current.x;
            const deltaY = endPoint.y - startPoint.current.y;
            const deltaTime = endPoint.time - startPoint.current.time;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

            // Detect tap
            if (
                distance < opts.swipeThreshold &&
                deltaTime < opts.tapThreshold &&
                handlers.onTap
            ) {
                handlers.onTap(endPoint.x, endPoint.y);
            }

            // Detect swipe
            if (distance >= opts.swipeThreshold && handlers.onSwipe) {
                const absX = Math.abs(deltaX);
                const absY = Math.abs(deltaY);

                let direction: SwipeDirection;
                if (absX > absY) {
                    direction = deltaX > 0 ? 'right' : 'left';
                } else {
                    direction = deltaY > 0 ? 'down' : 'up';
                }

                handlers.onSwipe(direction, distance);
            }

            startPoint.current = null;
            initialDistance.current = 0;
        },
        [handlers, opts],
    );

    useEffect(() => {
        const element = elementRef.current;
        if (!element) return;

        element.addEventListener('touchstart', handleTouchStart, { passive: !opts.preventDefault });
        element.addEventListener('touchmove', handleTouchMove, { passive: !opts.preventDefault });
        element.addEventListener('touchend', handleTouchEnd, { passive: !opts.preventDefault });

        return () => {
            element.removeEventListener('touchstart', handleTouchStart);
            element.removeEventListener('touchmove', handleTouchMove);
            element.removeEventListener('touchend', handleTouchEnd);

            if (longPressTimer.current) {
                clearTimeout(longPressTimer.current);
            }
        };
    }, [handleTouchStart, handleTouchMove, handleTouchEnd, opts.preventDefault]);

    return elementRef;
}

/**
 * Swipeable List Item Hook
 * 
 * Specialized hook for swipeable list items with action buttons
 * 
 * @example
 * ```tsx
 * function SwipeableListItem({ item, onDelete, onArchive }) {
 *   const { ref, swipeOffset, isRevealed } = useSwipeableItem({
 *     onSwipeLeft: onDelete,
 *     onSwipeRight: onArchive,
 *   });
 * 
 *   return (
 *     <div ref={ref} style={{ transform: `translateX(${swipeOffset}px)` }}>
 *       <div>Item Content</div>
 *       {isRevealed && <button>Delete</button>}
 *     </div>
 *   );
 * }
 * ```
 */
export function useSwipeableItem(handlers: {
    onSwipeLeft?: () => void;
    onSwipeRight?: () => void;
    threshold?: number;
}) {
    const ref = useRef<HTMLDivElement>(null);
    const swipeOffset = useRef(0);
    const isRevealed = useRef(false);

    const gestureRef = useTouchGestures<HTMLDivElement>(
        {
            onSwipe: (direction, distance) => {
                if (direction === 'left' && distance > (handlers.threshold || 100)) {
                    handlers.onSwipeLeft?.();
                    isRevealed.current = true;
                } else if (direction === 'right' && distance > (handlers.threshold || 100)) {
                    handlers.onSwipeRight?.();
                    isRevealed.current = true;
                }
            },
            onTouchMove: (event) => {
                const touch = event.touches[0];
                swipeOffset.current = touch.clientX;
            },
        },
        { swipeThreshold: handlers.threshold || 100 },
    );

    return {
        ref: gestureRef,
        swipeOffset: swipeOffset.current,
        isRevealed: isRevealed.current,
    };
}
