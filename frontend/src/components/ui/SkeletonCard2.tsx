'use client';

import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface SkeletonCard2Props extends HTMLAttributes<HTMLDivElement> {
    /**
     * Card variant determining structure
     */
    variant?: 'simple' | 'withImage' | 'withAvatar';

    /**
     * Card size
     */
    size?: 'sm' | 'md' | 'lg' | 'xl';

    /**
     * Animation style
     */
    animation?: 'pulse' | 'shimmer' | 'none';

    /**
     * Show header placeholder
     */
    showHeader?: boolean;

    /**
     * Show footer placeholder
     */
    showFooter?: boolean;

    /**
     * Number of content lines
     */
    lines?: number;
}

const sizes = {
    sm: 'p-4 space-y-3',
    md: 'p-6 space-y-4',
    lg: 'p-8 space-y-5',
    xl: 'p-10 space-y-6',
};

const animations = {
    pulse: 'animate-pulse',
    shimmer: 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
    none: '',
};

/**
 * SkeletonCard2 - Card loading placeholder component
 * 
 * @example
 * ```tsx
 * // Simple card
 * <SkeletonCard2 variant="simple" size="md" />
 * 
 * // Card with image
 * <SkeletonCard2 variant="withImage" animation="shimmer" />
 * 
 * // Card with avatar and footer
 * <SkeletonCard2 variant="withAvatar" showFooter lines={3} />
 * ```
 */
export const SkeletonCard2 = forwardRef<HTMLDivElement, SkeletonCard2Props>(
    (
        {
            variant = 'simple',
            size = 'md',
            animation = 'pulse',
            showHeader = true,
            showFooter = false,
            lines = 3,
            className,
            ...props
        },
        ref
    ) => {
        const animationClass = animations[animation];

        return (
            <div
                ref={ref}
                role="status"
                aria-label="Loading card"
                className={cn(
                    'bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700',
                    sizes[size],
                    className
                )}
                {...props}
            >
                {/* Image placeholder (for withImage variant) */}
                {variant === 'withImage' && (
                    <div
                        className={cn(
                            'w-full h-48 bg-neutral-200 dark:bg-neutral-700 rounded-lg mb-4',
                            animationClass
                        )}
                    />
                )}

                {/* Header with avatar (for withAvatar variant) */}
                {variant === 'withAvatar' && showHeader && (
                    <div className="flex items-center gap-3 mb-4">
                        <div
                            className={cn(
                                'w-10 h-10 bg-neutral-200 dark:bg-neutral-700 rounded-full flex-shrink-0',
                                animationClass
                            )}
                        />
                        <div className="flex-1 space-y-2">
                            <div
                                className={cn(
                                    'h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4',
                                    animationClass
                                )}
                            />
                            <div
                                className={cn(
                                    'h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-1/2',
                                    animationClass
                                )}
                            />
                        </div>
                    </div>
                )}

                {/* Simple header (for simple variant) */}
                {variant === 'simple' && showHeader && (
                    <div className="space-y-2 mb-4">
                        <div
                            className={cn(
                                'h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4',
                                animationClass
                            )}
                        />
                        <div
                            className={cn(
                                'h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-1/2',
                                animationClass
                            )}
                        />
                    </div>
                )}

                {/* Content lines */}
                <div className="space-y-2">
                    {Array.from({ length: lines }).map((_, index) => {
                        const isLastLine = index === lines - 1;
                        const width = isLastLine ? 'w-2/3' : 'w-full';

                        return (
                            <div
                                key={index}
                                className={cn(
                                    'h-4 bg-neutral-200 dark:bg-neutral-700 rounded',
                                    width,
                                    animationClass
                                )}
                            />
                        );
                    })}
                </div>

                {/* Footer */}
                {showFooter && (
                    <div className="flex items-center gap-2 mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
                        <div
                            className={cn(
                                'h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-20',
                                animationClass
                            )}
                        />
                        <div
                            className={cn(
                                'h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-24',
                                animationClass
                            )}
                        />
                    </div>
                )}

                <span className="sr-only">Loading...</span>
            </div>
        );
    }
);

SkeletonCard2.displayName = 'SkeletonCard2';

export default SkeletonCard2;
