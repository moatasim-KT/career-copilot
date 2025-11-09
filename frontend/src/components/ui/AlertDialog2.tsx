'use client';

import { X, AlertTriangle } from 'lucide-react';
import { forwardRef, useEffect, useRef } from 'react';

import { cn } from '@/lib/utils';

export interface AlertDialog2Props {
    open: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title?: string;
    description?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    children?: React.ReactNode;
    danger?: boolean;
    className?: string;
    overlayClassName?: string;
    initialFocusRef?: React.RefObject<HTMLElement>;
    ariaLabelledBy?: string;
    ariaDescribedBy?: string;
}

export const AlertDialog2 = forwardRef<HTMLDivElement, AlertDialog2Props>(
    (
        {
            open,
            onClose,
            onConfirm,
            title,
            description,
            confirmLabel = 'Confirm',
            cancelLabel = 'Cancel',
            children,
            danger = false,
            className,
            overlayClassName,
            initialFocusRef,
            ariaLabelledBy,
            ariaDescribedBy,
        },
        ref,
    ) => {
        const dialogRef = useRef<HTMLDivElement>(null);

        // Focus trap
        useEffect(() => {
            if (!open) return;
            const previouslyFocused = document.activeElement as HTMLElement;
            const focusEl = initialFocusRef?.current || dialogRef.current;
            focusEl?.focus();
            return () => {
                previouslyFocused?.focus();
            };
        }, [open, initialFocusRef]);

        // Escape key to close
        useEffect(() => {
            if (!open) return;
            function handleKey(e: KeyboardEvent) {
                if (e.key === 'Escape') onClose();
            }
            window.addEventListener('keydown', handleKey);
            return () => window.removeEventListener('keydown', handleKey);
        }, [open, onClose]);

        if (!open) return null;

        return (
            <div
                className={cn(
                    'fixed inset-0 z-50 flex items-center justify-center bg-black/40',
                    overlayClassName,
                )}
                aria-modal="true"
                role="alertdialog"
                tabIndex={-1}
            >
                <div
                    ref={ref || dialogRef}
                    className={cn(
                        'relative w-full max-w-md rounded-lg bg-white dark:bg-neutral-900 shadow-lg outline-none',
                        'focus:outline-none',
                        className,
                    )}
                    tabIndex={-1}
                    aria-labelledby={ariaLabelledBy}
                    aria-describedby={ariaDescribedBy}
                >
                    <button
                        type="button"
                        onClick={onClose}
                        className="absolute right-3 top-3 text-neutral-400 hover:text-neutral-700 focus:outline-none"
                        aria-label="Close dialog"
                    >
                        <X className="h-5 w-5" />
                    </button>
                    <div className="flex items-center gap-3 mb-3">
                        <AlertTriangle className={cn('h-6 w-6', danger ? 'text-error-500' : 'text-warning-500')} />
                        <h2 id={ariaLabelledBy || 'alert-title'} className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                            {title}
                        </h2>
                    </div>
                    {description && (
                        <p id={ariaDescribedBy || 'alert-desc'} className="mb-4 text-neutral-600 dark:text-neutral-300">
                            {description}
                        </p>
                    )}
                    {children}
                    <div className="mt-6 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg bg-neutral-100 text-neutral-700 hover:bg-neutral-200 focus:outline-none"
                        >
                            {cancelLabel}
                        </button>
                        <button
                            type="button"
                            onClick={onConfirm}
                            className={cn(
                                'px-4 py-2 rounded-lg text-white font-semibold focus:outline-none',
                                danger ? 'bg-error-600 hover:bg-error-700' : 'bg-primary-600 hover:bg-primary-700',
                            )}
                        >
                            {confirmLabel}
                        </button>
                    </div>
                </div>
            </div>
        );
    },
);

AlertDialog2.displayName = 'AlertDialog2';

export default AlertDialog2;
