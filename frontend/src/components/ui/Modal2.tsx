'use client';

import { forwardRef, useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Modal2Props {
    open: boolean;
    onClose: () => void;
    title?: string;
    description?: string;
    children: React.ReactNode;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    showClose?: boolean;
    className?: string;
    overlayClassName?: string;
    initialFocusRef?: React.RefObject<HTMLElement>;
    ariaLabelledBy?: string;
    ariaDescribedBy?: string;
}

const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
};

export const Modal2 = forwardRef<HTMLDivElement, Modal2Props>(
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
        const modalRef = useRef<HTMLDivElement>(null);

        // Focus trap
        useEffect(() => {
            if (!open) return;
            const previouslyFocused = document.activeElement as HTMLElement;
            const focusEl = initialFocusRef?.current || modalRef.current;
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

        // Prevent background scroll
        useEffect(() => {
            if (!open) return;
            document.body.style.overflow = 'hidden';
            return () => {
                document.body.style.overflow = '';
            };
        }, [open]);

        if (!open) return null;

        return (
            <div
                className={cn(
                    'fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm',
                    overlayClassName
                )}
                aria-modal="true"
                role="dialog"
                tabIndex={-1}
            >
                <div
                    ref={ref || modalRef}
                    className={cn(
                        'relative w-full rounded-xl bg-white dark:bg-neutral-900 shadow-xl outline-none',
                        'focus:outline-none',
                        sizes[size],
                        className
                    )}
                    tabIndex={-1}
                    aria-labelledby={ariaLabelledBy}
                    aria-describedby={ariaDescribedBy}
                >
                    {showClose && (
                        <button
                            type="button"
                            onClick={onClose}
                            className="absolute right-4 top-4 text-neutral-400 hover:text-neutral-700 focus:outline-none"
                            aria-label="Close modal"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    )}
                    {title && (
                        <h2 id={ariaLabelledBy || 'modal-title'} className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                            {title}
                        </h2>
                    )}
                    {description && (
                        <p id={ariaDescribedBy || 'modal-desc'} className="mb-4 text-neutral-600 dark:text-neutral-300">
                            {description}
                        </p>
                    )}
                    <div>{children}</div>
                </div>
            </div>
        );
    },
);

Modal2.displayName = 'Modal2';

export default Modal2;
