'use client';

import { forwardRef, TextareaHTMLAttributes, useState, useEffect } from 'react';

import { errorMessageVariants, shakeVariants } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface Textarea2Props extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    variant?: 'default' | 'filled' | 'outlined';
    label?: string;
    error?: string;
    helperText?: string;
    required?: boolean;
    showCount?: boolean;
    autoResize?: boolean;
    resize?: 'none' | 'vertical' | 'horizontal' | 'both';
}

const variants = {
    default: 'border border-neutral-300 bg-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 dark:bg-neutral-800 dark:border-neutral-700 dark:focus:border-primary-400 dark:focus:ring-primary-400/20',
    filled: 'border-0 bg-neutral-100 focus:bg-white focus:ring-2 focus:ring-primary-500/20 dark:bg-neutral-700 dark:focus:bg-neutral-800 dark:focus:ring-primary-400/20',
    outlined: 'border-2 border-neutral-300 bg-transparent focus:border-primary-500 dark:border-neutral-700 dark:focus:border-primary-400',
};

const resizeClasses = {
    none: 'resize-none',
    vertical: 'resize-y',
    horizontal: 'resize-x',
    both: 'resize',
};

/**
 * Textarea2 - Enhanced multi-line text input
 */
export const Textarea2 = forwardRef<HTMLTextAreaElement, Textarea2Props>(
    (
        {
            variant = 'default',
            label,
            error,
            helperText,
            required = false,
            showCount = false,
            autoResize = false,
            resize = 'vertical',
            className,
            disabled,
            maxLength,
            value,
            onChange,
            ...props
        },
        ref,
    ) => {
        const [charCount, setCharCount] = useState((value as string)?.length || 0);
        const [isFocused, setIsFocused] = useState(false);
        const [shouldShake, setShouldShake] = useState(false);
        const [prevError, setPrevError] = useState(error);

        const message = error || helperText;
        const messageColor = error ? 'text-error-600' : 'text-neutral-500';

        // Trigger shake animation when error changes
        useEffect(() => {
            if (error && error !== prevError) {
                setShouldShake(true);
                const timer = setTimeout(() => setShouldShake(false), 400);
                return () => clearTimeout(timer);
            }
            setPrevError(error);
        }, [error, prevError]);

        const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
            setCharCount(e.target.value.length);

            if (autoResize) {
                e.target.style.height = 'auto';
                e.target.style.height = `${e.target.scrollHeight}px`;
            }

            onChange?.(e);
        };

        return (
            <div className={cn('w-full', className)}>
                <div className="flex items-center justify-between mb-1.5">
                    {label && (
                        <m.label 
                            htmlFor={props.id} 
                            className="text-sm font-medium text-neutral-700"
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.2, ease: 'easeOut' }}
                        >
                            {label}
                            {required && <span className="ml-1 text-error-500">*</span>}
                        </m.label>
                    )}

                    {showCount && maxLength && (
                        <m.span 
                            className="text-xs text-neutral-500 dark:text-neutral-400"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.2, delay: 0.1 }}
                        >
                            {charCount}/{maxLength}
                        </m.span>
                    )}
                </div>

                <m.div
                    animate={shouldShake ? 'shake' : 'default'}
                    variants={shakeVariants}
                >
                    <textarea
                        ref={ref}
                        value={value}
                        disabled={disabled}
                        maxLength={maxLength}
                        onChange={handleChange}
                        className={cn(
                            'w-full rounded-lg px-4 py-2.5 text-sm transition-all duration-200',
                            'placeholder:text-neutral-400 dark:placeholder-neutral-500',
                            'text-neutral-900 dark:text-neutral-100',
                            'focus:outline-none',
                            'disabled:cursor-not-allowed disabled:opacity-50',
                            'min-h-[80px]',
                            variants[variant],
                            autoResize ? 'resize-none' : resizeClasses[resize],
                            error && 'border-error-500 focus:border-error-500',
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
                </m.div>

                <AnimatePresence mode="wait">
                    {message && (
                        <m.p 
                            key={message}
                            className={cn('mt-1.5 text-sm overflow-hidden', messageColor)}
                            initial="hidden"
                            animate="visible"
                            exit="hidden"
                            variants={errorMessageVariants}
                        >
                            {message}
                        </m.p>
                    )}
                </AnimatePresence>
            </div>
        );
    },
);

Textarea2.displayName = 'Textarea2';

export default Textarea2;
