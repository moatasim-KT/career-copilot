'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { forwardRef, useEffect, useRef } from 'react';

import { backdropVariants, modalVariants, slideVariants } from '@/lib/animations';
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

        // Detect if mobile device for slide-in from bottom
        const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

        return (
            <AnimatePresence mode="wait">
                {open && (
                    <motion.div
                        className={cn(
                            'fixed inset-0 z-50 flex items-center justify-center',
                            overlayClassName,
                        )}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        variants={backdropVariants}
                        onClick={onClose}
                        aria-modal="true"
                        role="dialog"
                        tabIndex={-1}
                    >
                        {/* Backdrop with glass morphism */}
                        <div className="absolute inset-0 glass" />
                        
                        {/* Modal content */}
                        <motion.div
                            ref={ref || modalRef}
                            className={cn(
                                'relative w-full rounded-xl bg-white dark:bg-neutral-900 shadow-xl outline-none',
                                'focus:outline-none mx-4',
                                sizes[size],
                                className,
                            )}
                            initial="hidden"
                            animate="visible"
                            exit="exit"
                            variants={isMobile ? slideVariants.up : modalVariants}
                            onClick={(e) => e.stopPropagation()}
                            tabIndex={-1}
                            aria-labelledby={ariaLabelledBy}
                            aria-describedby={ariaDescribedBy}
                        >
                            {showClose && (
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="absolute right-4 top-4 text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300 focus:outline-none transition-colors"
                                    aria-label="Close modal"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            )}
                            <div className="p-6">
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
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        );
    },
);

Modal2.displayName = 'Modal2';

export default Modal2;
