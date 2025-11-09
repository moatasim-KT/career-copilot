'use client';

import { X } from 'lucide-react';
import { forwardRef, useEffect, useRef } from 'react';

import { cn } from '@/lib/utils';

export interface Dialog2Props {
    open: boolean;
    onClose: () => void;
    title?: string;
    description?: string;
    children: React.ReactNode;
    size?: 'sm' | 'md' | 'lg';
    showClose?: boolean;
    className?: string;
    overlayClassName?: string;
    initialFocusRef?: React.RefObject<HTMLElement>;
    ariaLabelledBy?: string;
    ariaDescribedBy?: string;
}

const sizes = {
    sm: 'max-w-xs',
    md: 'max-w-md',
    lg: 'max-w-lg',
};

export const Dialog2 = forwardRef<HTMLDivElement, Dialog2Props>(
    (
        {
            open,
            onClose,
            title,
            description,
            children,
            size = 'md',
            showClose = true,
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
                    'fixed inset-0 z-50 flex items-center justify-center bg-black/30',
                    overlayClassName,
                )}
                aria-modal="true"
                role="dialog"
                tabIndex={-1}
            >
                <div
                    ref={ref || dialogRef}
                    className={cn(
                        'relative w-full rounded-lg bg-white dark:bg-neutral-900 shadow-lg outline-none',
                        'focus:outline-none',
                        sizes[size],
                        className,
                    )}
                    tabIndex={-1}
                    aria-labelledby={ariaLabelledBy}
                    aria-describedby={ariaDescribedBy}
                >
                    {showClose && (
                        <button
                            type="button"
                            onClick={onClose}
                            className="absolute right-3 top-3 text-neutral-400 hover:text-neutral-700 focus:outline-none"
                            aria-label="Close dialog"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    )}
                    {title && (
                        <h2 id={ariaLabelledBy || 'dialog-title'} className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                            {title}
                        </h2>
                    )}
                    {description && (
                        <p id={ariaDescribedBy || 'dialog-desc'} className="mb-4 text-neutral-600 dark:text-neutral-300">
                            {description}
                        </p>
                    )}
                    <div>{children}</div>
                </div>
            </div>
        );
    },
);

Dialog2.displayName = 'Dialog2';

export default Dialog2;
