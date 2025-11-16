'use client';

import { forwardRef, HTMLAttributes } from 'react';

import { progressBarVariants } from '@/lib/animations';
import { m } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface ProgressBarProps extends Omit<HTMLAttributes<HTMLDivElement>, 'children'> {
  /**
   * Progress value (0-100) for determinate progress
   * If undefined, shows indeterminate progress
   */
  value?: number;

  /**
   * Size of the progress bar
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Color of the progress bar
   */
  color?: 'primary' | 'success' | 'warning' | 'error';

  /**
   * Whether to show the percentage label
   */
  showLabel?: boolean;

  /**
   * Label for screen readers
   */
  label?: string;
}

const sizes = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

const colors = {
  primary: 'bg-primary-600',
  success: 'bg-success-600',
  warning: 'bg-warning-600',
  error: 'bg-error-600',
};

const backgroundColors = {
  primary: 'bg-primary-100 dark:bg-primary-900/20',
  success: 'bg-success-100 dark:bg-success-900/20',
  warning: 'bg-warning-100 dark:bg-warning-900/20',
  error: 'bg-error-100 dark:bg-error-900/20',
};

/**
 * ProgressBar - Determinate and indeterminate progress indicator
 * 
 * Features:
 * - Determinate progress with percentage
 * - Smooth indeterminate animation
 * - Multiple sizes and colors
 * - Optional percentage label
 * - Accessible with ARIA attributes
 * 
 * @example
 * ```tsx
 * // Indeterminate progress
 * <ProgressBar />
 * 
 * // Determinate progress with label
 * <ProgressBar value={65} showLabel />
 * 
 * // Large success progress bar
 * <ProgressBar value={100} size="lg" color="success" />
 * 
 * // Custom styling
 * <ProgressBar
 *   value={45}
 *   color="warning"
 *   className="w-full"
 *   label="Upload progress"
 * />
 * ```
 */
export const ProgressBar = forwardRef<HTMLDivElement, ProgressBarProps>(
  (
    {
      value,
      size = 'md',
      color = 'primary',
      showLabel = false,
      label = 'Progress',
      className,
      ...props
    },
    ref,
  ) => {
    const isIndeterminate = value === undefined;
    const clampedValue = value !== undefined ? Math.min(Math.max(value, 0), 100) : 0;

    return (
      <div
        ref={ref}
        className={cn('w-full', className)}
        {...props}
      >
        {showLabel && !isIndeterminate && (
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
              {label}
            </span>
            <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
              {Math.round(clampedValue)}%
            </span>
          </div>
        )}

        <div
          role="progressbar"
          aria-label={label}
          aria-valuenow={isIndeterminate ? undefined : clampedValue}
          aria-valuemin={0}
          aria-valuemax={100}
          className={cn(
            'relative w-full overflow-hidden rounded-full',
            sizes[size],
            backgroundColors[color],
          )}
        >
          {isIndeterminate ? (
            // Indeterminate progress
            <m.div
              className={cn(
                'absolute inset-y-0 w-1/3 rounded-full',
                colors[color],
              )}
              variants={progressBarVariants}
              animate="indeterminate"
            />
          ) : (
            // Determinate progress
            <m.div
              className={cn(
                'h-full rounded-full',
                colors[color],
              )}
              initial={{ width: 0 }}
              animate={{ width: `${clampedValue}%` }}
              transition={{
                duration: 0.5,
                ease: [0, 0, 0.2, 1],
              }}
            />
          )}
        </div>
      </div>
    );
  },
);

ProgressBar.displayName = 'ProgressBar';

export default ProgressBar;
