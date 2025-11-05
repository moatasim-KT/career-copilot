import React from 'react';

import { cn } from '@/lib/utils';

/**
 * Badge component props
 */
export interface BadgeProps {
    /** Badge text content */
    children: React.ReactNode;
    /** Badge variant */
    variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info';
    /** Badge size */
    size?: 'sm' | 'md' | 'lg';
    /** Additional CSS classes */
    className?: string;
    /** Click handler */
    onClick?: () => void;
}

const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    primary: 'bg-blue-100 text-blue-800',
    secondary: 'bg-purple-100 text-purple-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
};

const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
};

/**
 * Badge component for displaying labels, tags, or status indicators
 * 
 * @example
 * ```tsx
 * <Badge variant="success">Active</Badge>
 * <Badge variant="warning" size="sm">Pending</Badge>
 * ```
 */
export default function Badge({
    children,
    variant = 'default',
    size = 'sm',
    className,
    onClick,
}: BadgeProps) {
    return (
        <span
            className={cn(
                'inline-flex items-center font-medium rounded-full',
                variantClasses[variant],
                sizeClasses[size],
                onClick && 'cursor-pointer hover:opacity-80 transition-opacity',
                className,
            )}
            onClick={onClick}
        >
            {children}
        </span>
    );
}
