'use client';

import { motion } from 'framer-motion';
import { ReactNode, ButtonHTMLAttributes, memo } from 'react';


import { cn } from '@/lib/utils';

/**
 * Props for the Button component
 */
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** The content to render inside the button */
  children: ReactNode;
  /** Visual style variant of the button */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  /** Size of the button */
  size?: 'sm' | 'md' | 'lg';
  /** Shows a loading spinner and disables the button */
  loading?: boolean;
  /** Makes the button full width */
  fullWidth?: boolean;
}

const variantClasses = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500',
  outline: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-blue-500',
  ghost: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:ring-gray-500',
  destructive: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

/**
 * Button component with multiple variants and sizes
 * 
 * @component
 * @example
 * ```tsx
 * <Button variant="primary" size="md" onClick={handleClick}>
 *   Click me
 * </Button>
 * ```
 * 
 * @example
 * ```tsx
 * <Button variant="destructive" loading>
 *   Deleting...
 * </Button>
 * ```
 */
function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  className,
  disabled,
  onClick,
  type = 'button',
  title,
}: ButtonProps) {
  return (
    <motion.button
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
        className,
      )}
      disabled={disabled || loading}
      onClick={onClick}
      type={type}
      title={title}
      
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </motion.button>
  );
}

export default memo(Button);