'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { forwardRef, SelectHTMLAttributes, ReactNode, useState, useEffect } from 'react';

import { errorMessageVariants, shakeVariants } from '@/lib/animations';
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
    default: 'border border-neutral-300 bg-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 dark:bg-neutral-800 dark:border-neutral-700 dark:focus:border-primary-400 dark:focus:ring-primary-400/20',
    filled: 'border-0 bg-neutral-100 focus:bg-white focus:ring-2 focus:ring-primary-500/20 dark:bg-neutral-700 dark:focus:bg-neutral-800 dark:focus:ring-primary-400/20',
    outlined: 'border-2 border-neutral-300 bg-transparent focus:border-primary-500 dark:border-neutral-700 dark:focus:border-primary-400',
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

        return (
            <div className={cn('w-full', className)}>
                {label && (
                    <motion.label 
                        htmlFor={props.id} 
                        className="mb-1.5 block text-sm font-medium text-neutral-700"
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                        {label}
                        {required && <span className="ml-1 text-error-500">*</span>}
                    </motion.label>
                )}

                <motion.div 
                    className="relative"
                    animate={shouldShake ? 'shake' : 'default'}
                    variants={shakeVariants}
                >
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

                    <select
                        ref={ref}
                        disabled={disabled}
                        className={cn(
                            'w-full rounded-lg transition-all duration-200 appearance-none',
                            'text-neutral-900 dark:text-neutral-100',
                            'focus:outline-none cursor-pointer',
                            'disabled:cursor-not-allowed disabled:opacity-50',
                            variants[variant],
                            sizes[selectSize],
                            error && 'border-error-500 focus:border-error-500',
                            prefixIcon && 'pl-10',
                            'pr-10',
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
                    >
                        {children}
                    </select>

                    <motion.div
                        className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none"
                        animate={{ rotate: isFocused ? 180 : 0 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                        <ChevronDown className="h-4 w-4 text-neutral-400 dark:text-neutral-500" />
                    </motion.div>
                </motion.div>

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

Select2.displayName = 'Select2';

export default Select2;
