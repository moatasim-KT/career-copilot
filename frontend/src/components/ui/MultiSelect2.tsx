'use client';

import { X, Check } from 'lucide-react';
import { forwardRef, useState, useRef, useEffect } from 'react';

import { errorMessageVariants, shakeVariants } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface MultiSelect2Option {
    value: string;
    label: string;
}

export interface MultiSelect2Props {
    options: MultiSelect2Option[];
    value?: string[];
    onChange?: (value: string[]) => void;
    label?: string;
    placeholder?: string;
    error?: string;
    helperText?: string;
    required?: boolean;
    maxSelection?: number;
    searchable?: boolean;
    disabled?: boolean;
    className?: string;
}

/**
 * MultiSelect2 - Multi-selection dropdown with chips
 */
export const MultiSelect2 = forwardRef<HTMLDivElement, MultiSelect2Props>(
    (
        {
            options,
            value = [],
            onChange,
            label,
            placeholder = 'Select options...',
            error,
            helperText,
            required = false,
            maxSelection,
            searchable = true,
            disabled = false,
            className,
        },
        ref,
    ) => {
        const [isOpen, setIsOpen] = useState(false);
        const [searchQuery, setSearchQuery] = useState('');
        const [shouldShake, setShouldShake] = useState(false);
        const [prevError, setPrevError] = useState(error);
        const containerRef = useRef<HTMLDivElement>(null);

        // Trigger shake animation when error changes
        useEffect(() => {
            if (error && error !== prevError) {
                setShouldShake(true);
                const timer = setTimeout(() => setShouldShake(false), 400);
                return () => clearTimeout(timer);
            }
            setPrevError(error);
        }, [error, prevError]);

        const filteredOptions = searchable
            ? options.filter(opt =>
                opt.label.toLowerCase().includes(searchQuery.toLowerCase()),
            )
            : options;

        const toggleOption = (optionValue: string) => {
            if (disabled) return;

            const newValue = value.includes(optionValue)
                ? value.filter(v => v !== optionValue)
                : maxSelection && value.length >= maxSelection
                    ? value
                    : [...value, optionValue];

            onChange?.(newValue);
        };

        const selectAll = () => {
            if (disabled) return;
            const allValues = maxSelection
                ? options.slice(0, maxSelection).map(opt => opt.value)
                : options.map(opt => opt.value);
            onChange?.(allValues);
        };

        const clearAll = () => {
            if (disabled) return;
            onChange?.([]);
        };

        useEffect(() => {
            const handleClickOutside = (event: MouseEvent) => {
                if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                    setIsOpen(false);
                }
            };

            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }, []);

        const message = error || helperText;
        const messageColor = error ? 'text-error-600' : 'text-neutral-500';

        return (
            <div ref={ref} className={cn('w-full', className)}>
                {label && (
                    <m.label 
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
                    ref={containerRef} 
                    className="relative"
                    animate={shouldShake ? 'shake' : 'default'}
                    variants={shakeVariants}
                >
                    {/* Selected chips display */}
                    <m.div
                        onClick={() => !disabled && setIsOpen(!isOpen)}
                        className={cn(
                            'min-h-[40px] px-3 py-2 rounded-lg border transition-all cursor-pointer',
                            'border-neutral-300 bg-white hover:border-neutral-400',
                            'dark:bg-neutral-800 dark:border-neutral-700 dark:hover:border-neutral-600',
                            disabled && 'opacity-50 cursor-not-allowed',
                            error && 'border-error-500',
                            isOpen && 'border-primary-500 ring-2 ring-primary-500/20 dark:border-primary-400 dark:ring-primary-400/20',
                        )}
                        whileTap={!disabled ? { scale: 0.995 } : {}}
                        transition={{ duration: 0.15 }}
                    >
                        {value.length === 0 ? (
                            <span className="text-neutral-400 dark:text-neutral-500 text-sm">{placeholder}</span>
                        ) : (
                            <div className="flex flex-wrap gap-1.5">
                                <AnimatePresence mode="popLayout">
                                    {value.map((val, index) => {
                                        const option = options.find(opt => opt.value === val);
                                        return option ? (
                                            <m.span
                                                key={val}
                                                className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded text-xs font-medium"
                                                initial={{ opacity: 0, scale: 0.8 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                exit={{ opacity: 0, scale: 0.8 }}
                                                transition={{ duration: 0.15, delay: index * 0.02 }}
                                                layout
                                            >
                                                {option.label}
                                                <m.button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        toggleOption(val);
                                                    }}
                                                    className="hover:text-primary-900 dark:hover:text-primary-100"
                                                    whileHover={{ scale: 1.2 }}
                                                    whileTap={{ scale: 0.9 }}
                                                >
                                                    <X className="h-3 w-3" />
                                                </m.button>
                                            </m.span>
                                        ) : null;
                                    })}
                                </AnimatePresence>
                            </div>
                        )}
                    </m.div>

                    {/* Dropdown with glass morphism */}
                    <AnimatePresence>
                        {isOpen && !disabled && (
                            <m.div 
                                className="absolute z-50 w-full mt-2 glass rounded-lg shadow-lg max-h-60 overflow-hidden"
                                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                                transition={{ duration: 0.15, ease: 'easeOut' }}
                            >
                            {/* Search input */}
                            {searchable && (
                                <div className="p-2 border-b border-neutral-200 dark:border-neutral-700">
                                    <input
                                        type="text"
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        placeholder="Search..."
                                        className="w-full px-3 py-1.5 text-sm border border-neutral-300 dark:border-neutral-700 rounded focus:outline-none focus:border-primary-500 dark:focus:border-primary-400 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder-neutral-500"
                                    />
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-2 p-2 border-b border-neutral-200 dark:border-neutral-700">
                                <button
                                    type="button"
                                    onClick={selectAll}
                                    className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
                                >
                                    Select All
                                </button>
                                <button
                                    type="button"
                                    onClick={clearAll}
                                    className="text-xs text-neutral-600 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300"
                                >
                                    Clear All
                                </button>
                            </div>

                            {/* Options list */}
                            <div className="max-h-40 overflow-y-auto">
                                {filteredOptions.length === 0 ? (
                                    <div className="p-4 text-sm text-neutral-500 dark:text-neutral-400 text-center">
                                        No options found
                                    </div>
                                ) : (
                                    filteredOptions.map((option, index) => (
                                        <m.div
                                            key={option.value}
                                            onClick={() => toggleOption(option.value)}
                                            className={cn(
                                                'flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors',
                                                'hover:bg-neutral-50 dark:hover:bg-neutral-700',
                                                value.includes(option.value) && 'bg-primary-50 dark:bg-primary-900/20',
                                            )}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: index * 0.02, duration: 0.15 }}
                                        >
                                            <m.div
                                                className={cn(
                                                    'w-4 h-4 rounded border flex items-center justify-center',
                                                    value.includes(option.value)
                                                        ? 'bg-primary-600 border-primary-600 dark:bg-primary-500 dark:border-primary-500'
                                                        : 'border-neutral-300 dark:border-neutral-600',
                                                )}
                                                animate={{
                                                    scale: value.includes(option.value) ? [1, 1.2, 1] : 1,
                                                }}
                                                transition={{ duration: 0.2 }}
                                            >
                                                <AnimatePresence>
                                                    {value.includes(option.value) && (
                                                        <m.div
                                                            initial={{ scale: 0, rotate: -90 }}
                                                            animate={{ scale: 1, rotate: 0 }}
                                                            exit={{ scale: 0, rotate: 90 }}
                                                            transition={{ duration: 0.15 }}
                                                        >
                                                            <Check className="h-3 w-3 text-white" />
                                                        </m.div>
                                                    )}
                                                </AnimatePresence>
                                            </m.div>
                                            <span className="text-sm text-neutral-900 dark:text-neutral-100">{option.label}</span>
                                        </m.div>
                                    ))
                                )}
                            </div>

                            {/* Max selection indicator */}
                            {maxSelection && (
                                <div className="p-2 border-t border-neutral-200 dark:border-neutral-700 text-xs text-neutral-500 dark:text-neutral-400">
                                    {value.length}/{maxSelection} selected
                                </div>
                            )}
                            </m.div>
                        )}
                    </AnimatePresence>
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

MultiSelect2.displayName = 'MultiSelect2';

export default MultiSelect2;
