'use client';

import { forwardRef, HTMLAttributes } from 'react';

import { 
  spinnerVariants, 
  smoothSpinnerVariants, 
  pulsingSpinnerVariants, 
} from '@/lib/animations';
import { m } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface Spinner2Props extends Omit<HTMLAttributes<HTMLDivElement>, 'children'> {
  /**
   * Size of the spinner
   */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';

  /**
   * Spinner variant
   */
  variant?: 'default' | 'smooth' | 'pulsing';

  /**
   * Color of the spinner
   */
  color?: 'primary' | 'secondary' | 'white' | 'current';

  /**
   * Label for screen readers
   */
  label?: string;

  /**
   * Show label text below spinner
   */
  showLabel?: boolean;
}

const sizes = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
};

const strokeWidths = {
  xs: 2,
  sm: 2,
  md: 2.5,
  lg: 3,
  xl: 3.5,
};

const colors = {
  primary: 'text-primary-600',
  secondary: 'text-neutral-600',
  white: 'text-white',
  current: 'text-current',
};

const variantAnimations = {
  default: spinnerVariants,
  smooth: smoothSpinnerVariants,
  pulsing: pulsingSpinnerVariants,
};

/**
 * Spinner2 - Enhanced loading spinner with smooth animations
 * 
 * Features:
 * - Multiple size options
 * - Smooth easing curves for natural motion
 * - Pulsing variant for emphasis
 * - Accessible with ARIA labels
 * - Dark mode support
 * 
 * @example
 * ```tsx
 * // Basic spinner
 * <Spinner2 />
 * 
 * // Large smooth spinner with label
 * <Spinner2 size="lg" variant="smooth" showLabel label="Loading data..." />
 * 
 * // Pulsing spinner in primary color
 * <Spinner2 variant="pulsing" color="primary" />
 * 
 * // Small white spinner for dark backgrounds
 * <Spinner2 size="sm" color="white" />
 * ```
 */
export const Spinner2 = forwardRef<HTMLDivElement, Spinner2Props>(
  (
    {
      size = 'md',
      variant = 'smooth',
      color = 'primary',
      label = 'Loading',
      showLabel = false,
      className,
      ...props
    },
    ref,
  ) => {
    const strokeWidth = strokeWidths[size];
    const animation = variantAnimations[variant];

    return (
      <div
        ref={ref}
        role="status"
        aria-label={label}
        className={cn(
          'inline-flex flex-col items-center justify-center gap-2',
          className,
        )}
        {...props}
      >
        <m.svg
          className={cn(sizes[size], colors[color])}
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          variants={animation}
          animate="spin"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth={strokeWidth}
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </m.svg>

        {showLabel && (
          <span className={cn('text-sm font-medium', colors[color])}>
            {label}
          </span>
        )}

        <span className="sr-only">{label}</span>
      </div>
    );
  },
);

Spinner2.displayName = 'Spinner2';

export default Spinner2;
