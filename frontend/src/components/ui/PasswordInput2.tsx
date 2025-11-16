'use client';

import { Eye, EyeOff, Check, X } from 'lucide-react';
import { forwardRef, InputHTMLAttributes, useState, useEffect } from 'react';

import { errorMessageVariants, shakeVariants } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface PasswordInput2Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
    label?: string;
    error?: string;
    helperText?: string;
    required?: boolean;
    showStrength?: boolean;
    showRequirements?: boolean;
}

interface PasswordRequirement {
    label: string;
    met: boolean;
}

const checkPasswordStrength = (password: string): { strength: 'weak' | 'fair' | 'strong'; requirements: PasswordRequirement[] } => {
    const requirements: PasswordRequirement[] = [
        { label: 'At least 8 characters', met: password.length >= 8 },
        { label: 'Contains uppercase letter', met: /[A-Z]/.test(password) },
        { label: 'Contains lowercase letter', met: /[a-z]/.test(password) },
        { label: 'Contains number', met: /\d/.test(password) },
        { label: 'Contains special character', met: /[!@#$%^&*(),.?":{}|<>]/.test(password) },
    ];

    const metCount = requirements.filter(r => r.met).length;
    const strength = metCount <= 2 ? 'weak' : metCount <= 3 ? 'fair' : 'strong';

    return { strength, requirements };
};

/**
 * PasswordInput2 - Specialized password input with strength meter
 */
export const PasswordInput2 = forwardRef<HTMLInputElement, PasswordInput2Props>(
    (
        {
            label,
            error,
            helperText,
            required = false,
            showStrength = true,
            showRequirements = false,
            className,
            disabled,
            value,
            onChange,
            ...props
        },
        ref,
    ) => {
        const [showPassword, setShowPassword] = useState(false);
        const [isFocused, setIsFocused] = useState(false);
        const [shouldShake, setShouldShake] = useState(false);
        const [prevError, setPrevError] = useState(error);

        const passwordValue = (value as string) || '';
        const { strength, requirements } = checkPasswordStrength(passwordValue);

        // Trigger shake animation when error changes
        useEffect(() => {
            if (error && error !== prevError) {
                setShouldShake(true);
                const timer = setTimeout(() => setShouldShake(false), 400);
                return () => clearTimeout(timer);
            }
            setPrevError(error);
        }, [error, prevError]);

        const strengthColors = {
            weak: 'bg-error-500',
            fair: 'bg-warning-500',
            strong: 'bg-success-500',
        };

        const strengthWidths = {
            weak: 'w-1/3',
            fair: 'w-2/3',
            strong: 'w-full',
        };

        const message = error || helperText;
        const messageColor = error ? 'text-error-600' : 'text-neutral-500';

        return (
            <div className={cn('w-full', className)}>
                {label && (
                    <m.label 
                        htmlFor={props.id} 
                        className="mb-1.5 block text-sm font-medium text-neutral-700"
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                        {label}
                        {required && <span className="ml-1 text-error-500">*</span>}
                    </m.label>
                )}

                <m.div 
                    className="relative"
                    animate={shouldShake ? 'shake' : 'default'}
                    variants={shakeVariants}
                >
                    <input
                        ref={ref}
                        type={showPassword ? 'text' : 'password'}
                        value={value}
                        disabled={disabled}
                        onChange={onChange}
                        className={cn(
                            'w-full h-10 px-4 pr-10 rounded-lg border transition-all duration-200',
                            'border-neutral-300 bg-white',
                            'focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
                            'focus:outline-none',
                            'disabled:cursor-not-allowed disabled:opacity-50',
                            error && 'border-error-500 focus:border-error-500',
                        )}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        {...props}
                    />

                    <m.button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 transition-colors"
                        tabIndex={-1}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        transition={{ duration: 0.15 }}
                    >
                        <AnimatePresence mode="wait">
                            {showPassword ? (
                                <m.div
                                    key="eyeoff"
                                    initial={{ opacity: 0, rotate: -90 }}
                                    animate={{ opacity: 1, rotate: 0 }}
                                    exit={{ opacity: 0, rotate: 90 }}
                                    transition={{ duration: 0.15 }}
                                >
                                    <EyeOff className="h-4 w-4" />
                                </m.div>
                            ) : (
                                <m.div
                                    key="eye"
                                    initial={{ opacity: 0, rotate: -90 }}
                                    animate={{ opacity: 1, rotate: 0 }}
                                    exit={{ opacity: 0, rotate: 90 }}
                                    transition={{ duration: 0.15 }}
                                >
                                    <Eye className="h-4 w-4" />
                                </m.div>
                            )}
                        </AnimatePresence>
                    </m.button>
                </m.div>

                {/* Strength meter */}
                <AnimatePresence>
                    {showStrength && passwordValue && (
                        <m.div 
                            className="mt-2"
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.2, ease: 'easeOut' }}
                        >
                            <div className="h-1.5 bg-neutral-200 rounded-full overflow-hidden">
                                <m.div
                                    className={cn(
                                        'h-full',
                                        strengthColors[strength],
                                    )}
                                    initial={{ width: 0 }}
                                    animate={{ width: strengthWidths[strength] }}
                                    transition={{ duration: 0.3, ease: 'easeOut' }}
                                />
                            </div>
                            <m.p 
                                className="mt-1 text-xs text-neutral-600 capitalize"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.1, duration: 0.2 }}
                            >
                                Password strength: <span className="font-medium">{strength}</span>
                            </m.p>
                        </m.div>
                    )}
                </AnimatePresence>

                {/* Requirements checklist */}
                <AnimatePresence>
                    {showRequirements && passwordValue && isFocused && (
                        <m.div 
                            className="mt-3 p-3 bg-neutral-50 rounded-lg space-y-1.5"
                            initial={{ opacity: 0, height: 0, y: -10 }}
                            animate={{ opacity: 1, height: 'auto', y: 0 }}
                            exit={{ opacity: 0, height: 0, y: -10 }}
                            transition={{ duration: 0.2, ease: 'easeOut' }}
                        >
                            {requirements.map((req, index) => (
                                <m.div 
                                    key={index} 
                                    className="flex items-center gap-2 text-xs"
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05, duration: 0.2 }}
                                >
                                    <m.div
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        transition={{ delay: index * 0.05 + 0.1, duration: 0.2, type: 'spring' }}
                                    >
                                        {req.met ? (
                                            <Check className="h-3 w-3 text-success-500 flex-shrink-0" />
                                        ) : (
                                            <X className="h-3 w-3 text-neutral-400 flex-shrink-0" />
                                        )}
                                    </m.div>
                                    <span className={cn(req.met ? 'text-success-600' : 'text-neutral-600')}>
                                        {req.label}
                                    </span>
                                </m.div>
                            ))}
                        </m.div>
                    )}
                </AnimatePresence>

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

PasswordInput2.displayName = 'PasswordInput2';

export default PasswordInput2;
