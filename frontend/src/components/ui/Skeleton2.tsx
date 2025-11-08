'use client';

import { forwardRef, HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

export interface Skeleton2Props extends HTMLAttributes<HTMLDivElement> {
  /**
   * Skeleton variant determining shape
   */
  variant?: 'text' | 'circle' | 'rectangle' | 'custom';
  
  /**
   * Animation style
   */
  animation?: 'pulse' | 'shimmer' | 'wave' | 'none';
  
  /**
   * Width (for text and rectangle variants)
   */
  width?: string | number;
  
  /**
   * Height (for all variants)
   */
  height?: string | number;
  
  /**
   * Radius (for custom variant)
   */
  radius?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

const variants = {
  text: 'h-4 rounded-md',
  circle: 'rounded-full aspect-square',
  rectangle: 'rounded-lg',
  custom: '',
};

const radiusValues = {
  none: 'rounded-none',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  full: 'rounded-full',
};

const animations = {
  pulse: 'animate-pulse',
  shimmer: 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
  wave: 'relative overflow-hidden after:absolute after:inset-0 after:translate-x-[-100%] after:animate-[wave_1.5s_infinite] after:bg-gradient-to-r after:from-transparent after:via-white/20 after:to-transparent',
  none: '',
};

/**
 * Skeleton2 - Enhanced base skeleton component with flexible variants
 * 
 * @example
 * ```tsx
 * // Text skeleton
 * <Skeleton2 variant="text" width="200px" />
 * 
 * // Circle skeleton (avatar)
 * <Skeleton2 variant="circle" width={40} height={40} />
 * 
 * // Rectangle with shimmer
 * <Skeleton2 variant="rectangle" width="100%" height={200} animation="shimmer" />
 * 
 * // Custom with className
 * <Skeleton2 variant="custom" radius="xl" className="w-32 h-32" animation="wave" />
 * ```
 */
export const Skeleton2 = forwardRef<HTMLDivElement, Skeleton2Props>(
  (
    {
      variant = 'rectangle',
      animation = 'pulse',
      width,
      height,
      radius,
      className,
      style,
      ...props
    },
    ref,
  ) => {
    const customStyle = {
      ...(width && { width: typeof width === 'number' ? `${width}px` : width }),
      ...(height && { height: typeof height === 'number' ? `${height}px` : height }),
      ...style,
    };

    return (
      <div
        ref={ref}
        role="status"
        aria-label="Loading"
        className={cn(
          'bg-neutral-200 dark:bg-neutral-700',
          variants[variant],
          radius && radiusValues[radius],
          animations[animation],
          className,
        )}
        style={customStyle}
        {...props}
      >
        <span className="sr-only">Loading...</span>
      </div>
    );
  },
);

Skeleton2.displayName = 'Skeleton2';

export default Skeleton2;
