'use client';

import React from 'react';

import { cn } from '@/lib/utils';

/**
 * Status indicator props
 */
export interface StatusIndicatorProps {
  /** Status variant determining color and glow */
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  /** Size of the indicator */
  size?: 'sm' | 'md' | 'lg';
  /** Whether to show pulse animation */
  pulse?: boolean;
  /** Optional label text */
  label?: string;
  /** Whether to show as a dot only (no label) */
  dotOnly?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Accessible label for screen readers */
  ariaLabel?: string;
}

const sizeClasses = {
  sm: {
    dot: 'w-2 h-2',
    text: 'text-xs',
    padding: 'px-2 py-1',
  },
  md: {
    dot: 'w-2.5 h-2.5',
    text: 'text-sm',
    padding: 'px-3 py-1.5',
  },
  lg: {
    dot: 'w-3 h-3',
    text: 'text-base',
    padding: 'px-4 py-2',
  },
};

/**
 * StatusIndicator component for displaying status with colored dots and optional glow effects
 * 
 * @example
 * ```tsx
 * // Dot only with pulse
 * <StatusIndicator variant="success" pulse />
 * 
 * // With label
 * <StatusIndicator variant="warning" label="Pending" />
 * 
 * // Large with label
 * <StatusIndicator variant="error" label="Failed" size="lg" />
 * ```
 */
export default function StatusIndicator({
  variant = 'neutral',
  size = 'md',
  pulse = false,
  label,
  dotOnly = false,
  className,
  ariaLabel,
}: StatusIndicatorProps) {
  const sizeConfig = sizeClasses[size];

  // Dot only mode
  if (dotOnly || !label) {
    return (
      <span
        className={cn(
          'status-dot',
          `status-dot-${variant}`,
          sizeConfig.dot,
          pulse && 'status-dot-pulse',
          className
        )}
        role="status"
        aria-label={ariaLabel || `Status: ${variant}`}
      />
    );
  }

  // Full indicator with label
  return (
    <span
      className={cn(
        'status-indicator',
        `status-indicator-${variant}`,
        sizeConfig.padding,
        sizeConfig.text,
        pulse && 'status-dot-pulse',
        className
      )}
      role="status"
      aria-label={ariaLabel || `Status: ${label}`}
    >
      <span
        className={cn(
          'status-dot',
          `status-dot-${variant}`,
          sizeConfig.dot
        )}
        aria-hidden="true"
      />
      <span>{label}</span>
    </span>
  );
}
