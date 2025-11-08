'use client';

import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface SkeletonAvatar2Props extends HTMLAttributes<HTMLDivElement> {
    /**
     * Avatar shape
     */
    shape?: 'circle' | 'square' | 'rounded';

    /**
     * Avatar size
     */
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

    /**
     * Animation style
     */
    animation?: 'pulse' | 'shimmer' | 'none';
}

const shapes = {
    circle: 'rounded-full',
    square: 'rounded-none',
    rounded: 'rounded-lg',
};

const sizes = {
    xs: 'w-6 h-6',
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
    '2xl': 'w-20 h-20',
};

const animations = {
    pulse: 'animate-pulse',
    shimmer: 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
    none: '',
};

/**
 * SkeletonAvatar2 - Avatar loading placeholder component
 * 
 * @example
 * ```tsx
 * // Circle avatar
 * <SkeletonAvatar2 shape="circle" size="md" />
 * 
 * // Square avatar with shimmer
 * <SkeletonAvatar2 shape="square" size="lg" animation="shimmer" />
 * 
 * // Rounded avatar
 * <SkeletonAvatar2 shape="rounded" size="xl" />
 * ```
 */
export const SkeletonAvatar2 = forwardRef<HTMLDivElement, SkeletonAvatar2Props>(
    (
        {
            shape = 'circle',
            size = 'md',
            animation = 'pulse',
            className,
            ...props
        },
        ref
    ) => {
        return (
            <div
                ref={ref}
                role="status"
                aria-label="Loading avatar"
                className={cn(
                    'bg-neutral-200 dark:bg-neutral-700 flex-shrink-0',
                    shapes[shape],
                    sizes[size],
                    animations[animation],
                    className
                )}
                {...props}
            >
                <span className="sr-only">Loading...</span>
            </div>
        );
    }
);

SkeletonAvatar2.displayName = 'SkeletonAvatar2';

export default SkeletonAvatar2;
