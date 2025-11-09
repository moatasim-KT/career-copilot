'use client';

import { motion } from 'framer-motion';
import { forwardRef, HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';
import { dotsLoadingVariants } from '@/lib/animations';

export interface DotsLoaderProps extends Omit<HTMLAttributes<HTMLDivElement>, 'children'> {
  /**
   * Size of the dots
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Color of the dots
   */
  color?: 'primary' | 'secondary' | 'white' | 'current';

  /**
   * Label for screen readers
   */
  label?: string;
}

const dotSizes = {
  sm: 'h-1.5 w-1.5',
  md: 'h-2 w-2',
  lg: 'h-3 w-3',
};

const colors = {
  primary: 'bg-primary-600',
  secondary: 'bg-neutral-600',
  white: 'bg-white',
  current: 'bg-current',
};

/**
 * DotsLoader - Three-dot loading animation
 * 
 * Features:
 * - Smooth bouncing animation
 * - Multiple size options
 * - Accessible with ARIA labels
 * - Dark mode support
 * 
 * @example
 * ```tsx
 * // Basic dots loader
 * <DotsLoader />
 * 
 * // Large primary colored dots
 * <DotsLoader size="lg" color="primary" />
 * 
 * // White dots for dark backgrounds
 * <DotsLoader color="white" label="Processing..." />
 * ```
 */
export const DotsLoader = forwardRef<HTMLDivElement, DotsLoaderProps>(
  (
    {
      size = 'md',
      color = 'primary',
      label = 'Loading',
      className,
      ...props
    },
    ref,
  ) => {
    return (
      <div
        ref={ref}
        role="status"
        aria-label={label}
        className={cn('inline-flex items-center justify-center gap-1.5', className)}
        {...props}
      >
        <motion.div
          variants={dotsLoadingVariants.container}
          initial="hidden"
          animate="visible"
          className="flex items-center gap-1.5"
        >
          {[0, 1, 2].map((index) => (
            <motion.div
              key={index}
              variants={dotsLoadingVariants.dot}
              className={cn('rounded-full', dotSizes[size], colors[color])}
            />
          ))}
        </motion.div>

        <span className="sr-only">{label}</span>
      </div>
    );
  },
);

DotsLoader.displayName = 'DotsLoader';

export default DotsLoader;
