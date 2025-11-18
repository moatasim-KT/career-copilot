'use client';

import React from 'react';

import { m } from '@/lib/motion';
import { cn } from '@/lib/utils';

/**
 * Badge Component
 * 
 * A small badge for displaying counts, status, or labels
 * Commonly used for notification counts, new items, etc.
 */

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  animate?: boolean;
  pulse?: boolean;
}

const variantStyles = {
  default: 'bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300',
  primary: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
  secondary: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  success: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  outline: 'bg-transparent border border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300',
};

const sizeStyles = {
  sm: 'text-xs px-1.5 py-0.5 min-w-[18px]',
  md: 'text-sm px-2 py-0.5 min-w-[20px]',
  lg: 'text-base px-2.5 py-1 min-w-[24px]',
};

export function Badge({
  children,
  variant = 'default',
  size = 'sm',
  className,
  animate = false,
  pulse = false,
  ...rest
}: BadgeProps) {
  const badgeContent = (
    <span
      className={cn(
        'inline-flex items-center justify-center',
        'font-medium rounded-full',
        'transition-colors duration-200',
        variantStyles[variant],
        sizeStyles[size],
        pulse && 'animate-pulse',
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );

  if (animate) {
    return (
      <m.span
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        exit={{ scale: 0 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      >
        {badgeContent}
      </m.span>
    );
  }

  return badgeContent;
}

/**
 * Notification Badge
 * Specialized badge for notification counts
 */
interface NotificationBadgeProps {
  count: number;
  max?: number;
  className?: string;
}

export function NotificationBadge({ count, max = 99, className }: NotificationBadgeProps) {
  if (count === 0) return null;

  const displayCount = count > max ? `${max}+` : count;
  const notificationLabel =
    count > max
      ? `${max} or more unread notifications`
      : `${displayCount} unread notification${count === 1 ? '' : 's'}`;

  return (
    <Badge
      variant="error"
      size="sm"
      animate
      className={cn('absolute -top-1 -right-1', className)}
      role="status"
      aria-label={notificationLabel}
      aria-live="polite"
      aria-atomic="true"
    >
      {displayCount}
    </Badge>
  );
}

/**
 * Status Badge
 * Specialized badge for status indicators
 */
interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'pending' | 'success' | 'error';
  label?: string;
  showDot?: boolean;
  className?: string;
}

export function StatusBadge({ status, label, showDot = true, className }: StatusBadgeProps) {
  const statusConfig = {
    active: { variant: 'success' as const, label: label || 'Active', dotColor: 'bg-green-500' },
    inactive: { variant: 'default' as const, label: label || 'Inactive', dotColor: 'bg-neutral-400' },
    pending: { variant: 'warning' as const, label: label || 'Pending', dotColor: 'bg-yellow-500' },
    success: { variant: 'success' as const, label: label || 'Success', dotColor: 'bg-green-500' },
    error: { variant: 'error' as const, label: label || 'Error', dotColor: 'bg-red-500' },
  };

  const config = statusConfig[status];

  return (
    <Badge
      variant={config.variant}
      size="md"
      className={cn('gap-1.5', className)}
      role="status"
      aria-label={`${config.label} status`}
    >
      {showDot && (
        <span className={cn('w-1.5 h-1.5 rounded-full', config.dotColor)} aria-hidden="true" />
      )}
      {config.label}
    </Badge>
  );
}
