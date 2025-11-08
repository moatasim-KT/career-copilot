'use client';

import { forwardRef, SelectHTMLAttributes, ReactNode } from 'react';
import { ChevronDown } from 'lucide-react';

import { cn } from '@/lib/utils';

export interface Select2Props extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
    variant?: 'default' | 'filled' | 'outlined';
    selectSize?: 'sm' | 'md' | 'lg';
    label?: string;
    error?: string;
    helperText?: string;
    required?: boolean;
    prefixIcon?: ReactNode;
    children: ReactNode;
}

const variants = {
    default: 'border border-neutral-300 bg-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
    filled: 'border-0 bg-neutral-100 focus:bg-white focus:ring-2 focus:ring-primary-500/20',
    outlined: 'border-2 border-neutral-300 bg-transparent focus:border-primary-500',
};

const sizes = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-5 text-base',
};

/**
 * Select2 - Enhanced dropdown select component
 */
export const Select2 = forwardRef<HTMLSelectElement, Select2Props>(
    (
        {
            variant = 'default',
            selectSize = 'md',
            label,
            error,
            helperText,
            required = false,
            prefixIcon,
            className,
            disabled,
            children,
            ...props
        },
        ref,
    ) => {
        const message = error || helperText;
        const messageColor = error ? 'text-error-600' : 'text-neutral-500';

        return (
            <div className={cn('w-full', className)}>
                {label && (
                    <label htmlFor={props.id} className="mb-1.5 block text-sm font-medium text-neutral-700">
                        {label}
                        {required && <span className="ml-1 text-error-500">*</span>}
                    </label>
                )}

                <div className="relative">
                    {prefixIcon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400">
                            {prefixIcon}
                        </div>
                    )}

                    <select
                        ref={ref}
                        disabled={disabled}
                        className={cn(
                            'w-full rounded-lg transition-all duration-200 appearance-none',
                            'focus:outline-none cursor-pointer',
                            'disabled:cursor-not-allowed disabled:opacity-50',
                            variants[variant],
                            sizes[selectSize],
                            error && 'border-error-500 focus:border-error-500',
                            prefixIcon && 'pl-10',
                            'pr-10',
                        )}
                        {...props}
                    >
                        {children}
                    </select>

                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400 pointer-events-none" />
                </div>

                {message && <p className={cn('mt-1.5 text-sm', messageColor)}>{message}</p>}
            </div>
        );
    },
);

Select2.displayName = 'Select2';

export default Select2;
