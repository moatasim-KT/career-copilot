
'use client';

import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { forwardRef, ReactNode, ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success' | 'link';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  loadingText?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500 shadow-sm',
  secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200 focus-visible:ring-neutral-500',
  outline: 'border-2 border-neutral-300 bg-transparent hover:bg-neutral-50 focus-visible:ring-primary-500',
  ghost: 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900',
  destructive: 'bg-error-600 text-white hover:bg-error-700 focus-visible:ring-error-500 shadow-sm',
  success: 'bg-success-600 text-white hover:bg-success-700 focus-visible:ring-success-500 shadow-sm',
  link: 'text-primary-600 underline-offset-4 hover:underline',
};

const sizes = {
  xs: 'h-7 px-2.5 text-xs rounded-md',
  sm: 'h-8 px-3 text-sm rounded-md',
  md: 'h-10 px-4 text-sm rounded-lg',
  lg: 'h-11 px-6 text-base rounded-lg',
  xl: 'h-12 px-8 text-base rounded-xl',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      loading = false,
      loadingText,
      icon,
      iconPosition = 'left',
      fullWidth = false,
      className,
      disabled,
      type = 'button',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <motion.button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium',
          'transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          variants[variant],
          sizes[size],
          fullWidth && 'w-full',
          className
        )}
        whileHover={!isDisabled ? { scale: 1.02 } : undefined}
        whileTap={!isDisabled ? { scale: 0.98 } : undefined}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {!loading && icon && iconPosition === 'left' && icon}
        {loading && loadingText ? loadingText : children}
        {!loading && icon && iconPosition === 'right' && icon}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
