'use client';

import { forwardRef, HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

export interface SkeletonTextProps extends HTMLAttributes<HTMLDivElement> {
    /**
     * Variant determines the height and styling
     */
    variant?: 'heading' | 'paragraph' | 'caption';

    /**
     * Width as percentage of container
     */
    width?: 'full' | '3/4' | '1/2' | '1/4' | string;

    /**
     * Animation style
     */
    animation?: 'pulse' | 'shimmer' | 'none';

    /**
     * Number of lines to render (for paragraph variant)
     */
    lines?: number;
}

const variants = {
    heading: 'h-8 rounded-lg',
    paragraph: 'h-4 rounded-md',
    caption: 'h-3 rounded-sm',
};

const widths = {
    full: 'w-full',
    '3/4': 'w-3/4',
    '1/2': 'w-1/2',
    '1/4': 'w-1/4',
};

const animations = {
    pulse: 'animate-pulse',
    shimmer: 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
    none: '',
};

/**
 * SkeletonText - Text loading placeholder component
 * 
 * @example
 * ```tsx
 * // Single line heading
 * <SkeletonText variant="heading" width="3/4" />
 * 
 * // Multiple paragraph lines
 * <SkeletonText variant="paragraph" lines={3} />
 * 
 * // Caption with shimmer animation
 * <SkeletonText variant="caption" animation="shimmer" width="1/2" />
 * ```
 */
export const SkeletonText = forwardRef<HTMLDivElement, SkeletonTextProps>(
    (
        {
            variant = 'paragraph',
            width = 'full',
            animation = 'pulse',
            lines = 1,
            className,
            ...props
        },
        ref,
    ) => {
        // Handle custom width values (e.g., "200px", "50%")
        const widthClass = widths[width as keyof typeof widths] || '';
        const customWidth = !widths[width as keyof typeof widths] ? { width } : {};

        // For single line
        if (lines === 1) {
            return (
                <div
                    ref={ref}
                    role="status"
                    aria-label="Loading text"
                    className={cn(
                        'bg-neutral-200 dark:bg-neutral-700',
                        variants[variant],
                        widthClass,
                        animations[animation],
                        className,
                    )}
                    style={customWidth}
                    {...props}
                >
                    <span className="sr-only">Loading...</span>
                </div>
            );
        }

        // For multiple lines
        return (
            <div
                ref={ref}
                role="status"
                aria-label={`Loading ${lines} lines of text`}
                className={cn('space-y-2', className)}
                {...props}
            >
                {Array.from({ length: lines }).map((_, index) => {
                    // Make last line shorter for natural appearance
                    const isLastLine = index === lines - 1;
                    const lineWidth = isLastLine && width === 'full' ? '3/4' : width;
                    const lineWidthClass = widths[lineWidth as keyof typeof widths] || widthClass;

                    return (
                        <div
                            key={index}
                            className={cn(
                                'bg-neutral-200 dark:bg-neutral-700',
                                variants[variant],
                                lineWidthClass,
                                animations[animation],
                            )}
                            style={isLastLine && !widths[lineWidth as keyof typeof widths] ? { width: '75%' } : customWidth}
                        />
                    );
                })}
                <span className="sr-only">Loading...</span>
            </div>
        );
    },
);

SkeletonText.displayName = 'SkeletonText';

export default SkeletonText;
