'use client';

import { X, Loader2 } from 'lucide-react';
import { forwardRef, InputHTMLAttributes, ReactNode, useState } from 'react';

import { cn } from '@/lib/utils';

export interface Input2Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
    /**
     * Input variant
     */
    variant?: 'default' | 'filled' | 'outlined' | 'ghost';

    /**
     * Input size
     */
    inputSize?: 'sm' | 'md' | 'lg';

    /**
     * Input state
     */
    state?: 'default' | 'error' | 'success' | 'disabled';

    /**
     * Show loading spinner
     */
    loading?: boolean;

    /**
     * Prefix icon
     */
    prefixIcon?: ReactNode;

    /**
     * Suffix icon
     */
    suffixIcon?: ReactNode;

    /**
     * Show clear button
     */
    clearable?: boolean;

    /**
     * Label text
     */
    label?: string;

    /**
     * Helper text
     */
    helperText?: string;

    /**
     * Error message
     */
    error?: string;

    /**
     * Success message
     */
    success?: string;

    /**
     * Required field indicator
     */
    required?: boolean;

    /**
     * Callback when clear button is clicked
     */
    onClear?: () => void;
}

const variants = {
    default: 'border border-neutral-300 bg-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
    filled: 'border-0 bg-neutral-100 focus:bg-white focus:ring-2 focus:ring-primary-500/20',
    outlined: 'border-2 border-neutral-300 bg-transparent focus:border-primary-500',
    ghost: 'border-0 bg-transparent hover:bg-neutral-50 focus:bg-neutral-50',
};

const sizes = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-5 text-base',
};

const states = {
    default: '',
    error: 'border-error-500 focus:border-error-500 focus:ring-error-500/20',
    success: 'border-success-500 focus:border-success-500 focus:ring-success-500/20',
    disabled: 'opacity-50 cursor-not-allowed',
};

/**
 * Input2 - Enhanced text input component
 * 
 * @example
 * ```tsx
 * // Basic input
 * <Input2 placeholder="Enter text" />
 * 
 * // With label and error
 * <Input2 label="Email" error="Invalid email address" />
 * 
 * // With icons
 * <Input2 prefixIcon={<Mail />} suffixIcon={<Check />} />
 * 
 * // Clearable with loading
 * <Input2 clearable loading value={value} onChange={setValue} />
 * ```
 */
export const Input2 = forwardRef<HTMLInputElement, Input2Props>(
    (
        {
            variant = 'default',
            inputSize = 'md',
            state = 'default',
            loading = false,
            prefixIcon,
            suffixIcon,
            clearable = false,
            label,
            helperText,
            error,
            success,
            required = false,
            onClear,
            className,
            disabled,
            value,
            ...props
        },
        ref,
    ) => {
        const [isFocused, setIsFocused] = useState(false);

        const finalState = error ? 'error' : success ? 'success' : disabled ? 'disabled' : state;
        const message = error || success || helperText;
        const messageColor = error ? 'text-error-600' : success ? 'text-success-600' : 'text-neutral-500';

        const handleClear = () => {
            if (onClear) {
                onClear();
            }
        };

        return (
            <div className={cn('w-full', className)}>
                {/* Label */}
                {label && (
                    <label
                        htmlFor={props.id}
                        className="mb-1.5 block text-sm font-medium text-neutral-700 dark:text-neutral-300"
                    >
                        {label}
                        {required && <span className="ml-1 text-error-500">*</span>}
                    </label>
                )}

                {/* Input wrapper */}
                <div className="relative">
                    {/* Prefix icon */}
                    {prefixIcon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400">
                            {prefixIcon}
                        </div>
                    )}

                    {/* Input */}
                    <input
                        ref={ref}
                        value={value}
                        disabled={disabled || loading}
                        className={cn(
                            'w-full rounded-lg transition-all duration-200',
                            'placeholder:text-neutral-400',
                            'focus:outline-none',
                            'disabled:cursor-not-allowed disabled:opacity-50',
                            variants[variant],
                            sizes[inputSize],
                            states[finalState],
                            prefixIcon && 'pl-10',
                            (suffixIcon || loading || (clearable && value)) && 'pr-10',
                            isFocused && 'ring-2',
                        )}
                        onFocus={(e) => {
                            setIsFocused(true);
                            props.onFocus?.(e);
                        }}
                        onBlur={(e) => {
                            setIsFocused(false);
                            props.onBlur?.(e);
                        }}
                        {...props}
                    />

                    {/* Suffix content */}
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        {loading && <Loader2 className="h-4 w-4 animate-spin text-neutral-400" />}

                        {!loading && clearable && value && (
                            <button
                                type="button"
                                onClick={handleClear}
                                className="text-neutral-400 hover:text-neutral-600 transition-colors"
                                tabIndex={-1}
                            >
                                <X className="h-4 w-4" />
                            </button>
                        )}

                        {!loading && suffixIcon && <div className="text-neutral-400">{suffixIcon}</div>}
                    </div>
                </div>

                {/* Message */}
                {message && (
                    <p className={cn('mt-1.5 text-sm', messageColor)}>
                        {message}
                    </p>
                )}
            </div>
        );
    },
);

Input2.displayName = 'Input2';

export default Input2;
