'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2 } from 'lucide-react';
import { forwardRef, InputHTMLAttributes, ReactNode, useState, useEffect } from 'react';

import { errorMessageVariants, shakeVariants } from '@/lib/animations';
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
    default: 'border border-neutral-300 bg-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 dark:bg-neutral-800 dark:border-neutral-700 dark:focus:border-primary-400 dark:focus:ring-primary-400/20',
    filled: 'border-0 bg-neutral-100 focus:bg-white focus:ring-2 focus:ring-primary-500/20 dark:bg-neutral-700 dark:focus:bg-neutral-800 dark:focus:ring-primary-400/20',
    outlined: 'border-2 border-neutral-300 bg-transparent focus:border-primary-500 dark:border-neutral-700 dark:focus:border-primary-400',
    ghost: 'border-0 bg-transparent hover:bg-neutral-50 focus:bg-neutral-50 dark:hover:bg-neutral-800 dark:focus:bg-neutral-800',
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
        const [shouldShake, setShouldShake] = useState(false);
        const [prevError, setPrevError] = useState(error);

        const finalState = error ? 'error' : success ? 'success' : disabled ? 'disabled' : state;
        const message = error || success || helperText;
        const messageColor = error ? 'text-error-600' : success ? 'text-success-600' : 'text-neutral-500';

        // Trigger shake animation when error changes
        useEffect(() => {
            if (error && error !== prevError) {
                setShouldShake(true);
                const timer = setTimeout(() => setShouldShake(false), 400);
                return () => clearTimeout(timer);
            }
            setPrevError(error);
        }, [error, prevError]);

        const handleClear = () => {
            if (onClear) {
                onClear();
            }
        };

        return (
            <div className={cn('w-full', className)}>
                {/* Label */}
                {label && (
                    <motion.label
                        htmlFor={props.id}
                        className="mb-1.5 block text-sm font-medium text-neutral-700 dark:text-neutral-300"
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                        {label}
                        {required && <span className="ml-1 text-error-500">*</span>}
                    </motion.label>
                )}

                {/* Input wrapper */}
                <motion.div 
                    className="relative"
                    animate={shouldShake ? 'shake' : 'default'}
                    variants={shakeVariants}
                >
                    {/* Prefix icon */}
                    {prefixIcon && (
                        <motion.div 
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 dark:text-neutral-500"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.2, ease: 'easeOut' }}
                        >
                            {prefixIcon}
                        </motion.div>
                    )}

                    {/* Input */}
                    <input
                        ref={ref}
                        value={value}
                        disabled={disabled || loading}
                        className={cn(
                            'w-full rounded-lg transition-all duration-200',
                            'placeholder:text-neutral-400 dark:placeholder-neutral-500',
                            'text-neutral-900 dark:text-neutral-100',
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
                        <AnimatePresence mode="wait">
                            {loading && (
                                <motion.div
                                    key="loader"
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.8 }}
                                    transition={{ duration: 0.15 }}
                                >
                                    <Loader2 className="h-4 w-4 animate-spin text-neutral-400 dark:text-neutral-500" />
                                </motion.div>
                            )}

                            {!loading && clearable && value && (
                                <motion.button
                                    key="clear"
                                    type="button"
                                    onClick={handleClear}
                                    className="text-neutral-400 hover:text-neutral-600 dark:text-neutral-500 dark:hover:text-neutral-300 transition-colors"
                                    tabIndex={-1}
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.8 }}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    transition={{ duration: 0.15 }}
                                >
                                    <X className="h-4 w-4" />
                                </motion.button>
                            )}

                            {!loading && suffixIcon && (
                                <motion.div 
                                    key="suffix"
                                    className="text-neutral-400 dark:text-neutral-500"
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.2, ease: 'easeOut' }}
                                >
                                    {suffixIcon}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </motion.div>

                {/* Message */}
                <AnimatePresence mode="wait">
                    {message && (
                        <motion.p 
                            key={message}
                            className={cn('mt-1.5 text-sm overflow-hidden', messageColor)}
                            initial="hidden"
                            animate="visible"
                            exit="hidden"
                            variants={errorMessageVariants}
                        >
                            {message}
                        </motion.p>
                    )}
                </AnimatePresence>
            </div>
        );
    },
);

Input2.displayName = 'Input2';

export default Input2;
