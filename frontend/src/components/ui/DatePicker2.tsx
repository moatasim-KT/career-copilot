'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, X } from 'lucide-react';
import { forwardRef, useState, useRef, useEffect } from 'react';

import { errorMessageVariants, shakeVariants } from '@/lib/animations';
import { cn } from '@/lib/utils';

export interface DatePicker2Props {
    label?: string;
    value?: Date | null;
    onChange?: (date: Date | null) => void;
    minDate?: Date;
    maxDate?: Date;
    range?: boolean;
    startDate?: Date | null;
    endDate?: Date | null;
    onRangeChange?: (start: Date | null, end: Date | null) => void;
    error?: string;
    helperText?: string;
    required?: boolean;
    disabled?: boolean;
    className?: string;
}

function getDaysInMonth(year: number, month: number) {
    return new Date(year, month + 1, 0).getDate();
}

function isSameDay(a: Date, b: Date) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function isInRange(day: Date, start: Date | null, end: Date | null) {
    if (!start || !end) return false;
    return day >= start && day <= end;
}

export const DatePicker2 = forwardRef<HTMLDivElement, DatePicker2Props>(
    (
        {
            label,
            value,
            onChange,
            minDate,
            maxDate,
            range = false,
            startDate,
            endDate,
            onRangeChange,
            error,
            helperText,
            required = false,
            disabled = false,
            className,
        },
        ref,
    ) => {
        const [showCalendar, setShowCalendar] = useState(false);
        const [currentMonth, setCurrentMonth] = useState((value || startDate || new Date()).getMonth());
        const [currentYear, setCurrentYear] = useState((value || startDate || new Date()).getFullYear());
        const [internalStart, setInternalStart] = useState<Date | null>(startDate || null);
        const [internalEnd, setInternalEnd] = useState<Date | null>(endDate || null);
        const [shouldShake, setShouldShake] = useState(false);
        const [prevError, setPrevError] = useState(error);
        const inputRef = useRef<HTMLInputElement>(null);
        const calendarRef = useRef<HTMLDivElement>(null);

        // Trigger shake animation when error changes
        useEffect(() => {
            if (error && error !== prevError) {
                setShouldShake(true);
                const timer = setTimeout(() => setShouldShake(false), 400);
                return () => clearTimeout(timer);
            }
            setPrevError(error);
        }, [error, prevError]);

        useEffect(() => {
            if (!showCalendar) return;
            function handleClick(e: MouseEvent) {
                if (
                    calendarRef.current &&
                    !calendarRef.current.contains(e.target as Node) &&
                    inputRef.current &&
                    !inputRef.current.contains(e.target as Node)
                ) {
                    setShowCalendar(false);
                }
            }
            document.addEventListener('mousedown', handleClick);
            return () => document.removeEventListener('mousedown', handleClick);
        }, [showCalendar]);

        const daysInMonth = getDaysInMonth(currentYear, currentMonth);
        const firstDayOfWeek = new Date(currentYear, currentMonth, 1).getDay();
        const today = new Date();

        function selectDate(day: number) {
            if (disabled) return;
            const selected = new Date(currentYear, currentMonth, day);
            if (minDate && selected < minDate) return;
            if (maxDate && selected > maxDate) return;
            if (range) {
                if (!internalStart || (internalStart && internalEnd)) {
                    setInternalStart(selected);
                    setInternalEnd(null);
                    onRangeChange?.(selected, null);
                } else if (internalStart && !internalEnd) {
                    if (selected < internalStart) {
                        setInternalStart(selected);
                        setInternalEnd(internalStart);
                        onRangeChange?.(selected, internalStart);
                    } else {
                        setInternalEnd(selected);
                        onRangeChange?.(internalStart, selected);
                    }
                }
            } else {
                onChange?.(selected);
                setShowCalendar(false);
            }
        }

        function clearSelection() {
            if (range) {
                setInternalStart(null);
                setInternalEnd(null);
                onRangeChange?.(null, null);
            } else {
                onChange?.(null);
            }
        }

        const message = error || helperText;
        const messageColor = error ? 'text-error-600' : 'text-neutral-500';

        const displayValue = range
            ? internalStart && internalEnd
                ? `${internalStart.toLocaleDateString()} - ${internalEnd.toLocaleDateString()}`
                : internalStart
                    ? `${internalStart.toLocaleDateString()} - ...`
                    : ''
            : value
                ? value.toLocaleDateString()
                : '';

        return (
            <div ref={ref} className={cn('w-full', className)}>
                {label && (
                    <motion.label 
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
                    <input
                        ref={inputRef}
                        type="text"
                        value={displayValue}
                        readOnly
                        disabled={disabled}
                        onClick={() => setShowCalendar(!showCalendar)}
                        className={cn(
                            'w-full h-10 px-4 pr-10 rounded-lg border transition-all duration-200',
                            'border-neutral-300 bg-white',
                            'dark:bg-neutral-800 dark:border-neutral-700',
                            'text-neutral-900 dark:text-neutral-100',
                            'placeholder:text-neutral-400 dark:placeholder-neutral-500',
                            'focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
                            'dark:focus:border-primary-400 dark:focus:ring-primary-400/20',
                            'focus:outline-none',
                            'disabled:cursor-not-allowed disabled:opacity-50',
                            error && 'border-error-500 focus:border-error-500',
                        )}
                        placeholder={range ? 'Select date range' : 'Select date'}
                    />
                    <AnimatePresence>
                        {displayValue && !disabled && (
                            <motion.button
                                type="button"
                                onClick={clearSelection}
                                className="absolute right-8 top-1/2 -translate-y-1/2 text-neutral-400 dark:text-neutral-500 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
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
                    </AnimatePresence>
                    <CalendarIcon className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400 dark:text-neutral-500 pointer-events-none" />

                    {/* Calendar popover with glass morphism */}
                    <AnimatePresence>
                        {showCalendar && (
                            <motion.div 
                                ref={calendarRef} 
                                className="absolute z-50 mt-2 w-full glass rounded-lg shadow-lg p-4"
                                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                                transition={{ duration: 0.15, ease: 'easeOut' }}
                            >
                            <div className="flex items-center justify-between mb-2">
                                <button
                                    type="button"
                                    onClick={() => {
                                        if (currentMonth === 0) {
                                            setCurrentMonth(11);
                                            setCurrentYear(y => y - 1);
                                        } else {
                                            setCurrentMonth(m => m - 1);
                                        }
                                    }}
                                    className="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300"
                                >
                                    <ChevronLeft className="h-4 w-4" />
                                </button>
                                <span className="font-medium text-neutral-700 dark:text-neutral-300">
                                    {new Date(currentYear, currentMonth).toLocaleString('default', { month: 'long', year: 'numeric' })}
                                </span>
                                <button
                                    type="button"
                                    onClick={() => {
                                        if (currentMonth === 11) {
                                            setCurrentMonth(0);
                                            setCurrentYear(y => y + 1);
                                        } else {
                                            setCurrentMonth(m => m + 1);
                                        }
                                    }}
                                    className="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300"
                                >
                                    <ChevronRight className="h-4 w-4" />
                                </button>
                            </div>
                            <div className="grid grid-cols-7 gap-1 mb-1 text-xs text-neutral-500 dark:text-neutral-400">
                                {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(d => (
                                    <div key={d} className="text-center font-medium">
                                        {d}
                                    </div>
                                ))}
                            </div>
                            <div className="grid grid-cols-7 gap-1">
                                {Array.from({ length: firstDayOfWeek }).map((_, i) => (
                                    <div key={i} />
                                ))}
                                {Array.from({ length: daysInMonth }).map((_, i) => {
                                    const day = i + 1;
                                    const dateObj = new Date(currentYear, currentMonth, day);
                                    const isToday = isSameDay(dateObj, today);
                                    const isSelected = range
                                        ? (internalStart && isSameDay(dateObj, internalStart)) || (internalEnd && isSameDay(dateObj, internalEnd))
                                        : value && isSameDay(dateObj, value);
                                    const inRange = range && isInRange(dateObj, internalStart, internalEnd);
                                    const isDisabled =
                                        (minDate && dateObj < minDate) ||
                                        (maxDate && dateObj > maxDate) ||
                                        disabled;
                                    return (
                                        <motion.button
                                            key={day}
                                            type="button"
                                            disabled={isDisabled}
                                            onClick={() => selectDate(day)}
                                            className={cn(
                                                'w-8 h-8 rounded-full flex items-center justify-center text-neutral-700 dark:text-neutral-300',
                                                isToday && 'border border-primary-500 dark:border-primary-400',
                                                isSelected && 'bg-primary-500 dark:bg-primary-600 text-white',
                                                inRange && 'bg-primary-100 dark:bg-primary-900/30',
                                                isDisabled && 'opacity-30 cursor-not-allowed',
                                                !isDisabled && 'hover:bg-primary-50 dark:hover:bg-primary-900/20',
                                            )}
                                            whileHover={!isDisabled ? { scale: 1.1 } : {}}
                                            whileTap={!isDisabled ? { scale: 0.95 } : {}}
                                            transition={{ duration: 0.15 }}
                                        >
                                            {day}
                                        </motion.button>
                                    );
                                })}
                            </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
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

DatePicker2.displayName = 'DatePicker2';

export default DatePicker2;
