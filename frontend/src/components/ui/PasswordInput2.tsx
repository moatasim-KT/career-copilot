'use client';

import { Eye, EyeOff, Check, X } from 'lucide-react';
import { forwardRef, InputHTMLAttributes, useState } from 'react';

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

        const passwordValue = (value as string) || '';
        const { strength, requirements } = checkPasswordStrength(passwordValue);

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
                    <label htmlFor={props.id} className="mb-1.5 block text-sm font-medium text-neutral-700">
                        {label}
                        {required && <span className="ml-1 text-error-500">*</span>}
                    </label>
                )}

                <div className="relative">
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

                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 transition-colors"
                        tabIndex={-1}
                    >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                </div>

                {/* Strength meter */}
                {showStrength && passwordValue && (
                    <div className="mt-2">
                        <div className="h-1.5 bg-neutral-200 rounded-full overflow-hidden">
                            <div
                                className={cn(
                                    'h-full transition-all duration-300',
                                    strengthColors[strength],
                                    strengthWidths[strength],
                                )}
                            />
                        </div>
                        <p className="mt-1 text-xs text-neutral-600 capitalize">
                            Password strength: <span className="font-medium">{strength}</span>
                        </p>
                    </div>
                )}

                {/* Requirements checklist */}
                {showRequirements && passwordValue && isFocused && (
                    <div className="mt-3 p-3 bg-neutral-50 rounded-lg space-y-1.5">
                        {requirements.map((req, index) => (
                            <div key={index} className="flex items-center gap-2 text-xs">
                                {req.met ? (
                                    <Check className="h-3 w-3 text-success-500 flex-shrink-0" />
                                ) : (
                                    <X className="h-3 w-3 text-neutral-400 flex-shrink-0" />
                                )}
                                <span className={cn(req.met ? 'text-success-600' : 'text-neutral-600')}>
                                    {req.label}
                                </span>
                            </div>
                        ))}
                    </div>
                )}

                {message && <p className={cn('mt-1.5 text-sm', messageColor)}>{message}</p>}
            </div>
        );
    },
);

PasswordInput2.displayName = 'PasswordInput2';

export default PasswordInput2;
