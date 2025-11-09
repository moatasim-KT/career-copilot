'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { forwardRef, useEffect, useRef } from 'react';

import { backdropVariants, drawerVariants } from '@/lib/animations';
import { cn } from '@/lib/utils';

export interface Drawer2Props {
    open: boolean;
    onClose: () => void;
    title?: string;
    description?: string;
    children: React.ReactNode;
    side?: 'left' | 'right' | 'top' | 'bottom';
    size?: 'sm' | 'md' | 'lg' | 'xl';
    showClose?: boolean;
    className?: string;
    overlayClassName?: string;
    initialFocusRef?: React.RefObject<HTMLElement>;
    ariaLabelledBy?: string;
    ariaDescribedBy?: string;
}

const sideStyles = {
    left: 'left-0 top-0 h-full',
    right: 'right-0 top-0 h-full',
    top: 'top-0 left-0 w-full',
    bottom: 'bottom-0 left-0 w-full',
};

const sizeStyles = {
    sm: 'w-64 h-64',
    md: 'w-96 h-96',
    lg: 'w-[32rem] h-[32rem]',
    xl: 'w-[48rem] h-[48rem]',
};

export const Drawer2 = forwardRef<HTMLDivElement, Drawer2Props>(
    (
        {
            open,
            onClose,
            title,
            description,
            children,
            side = 'right',
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
        const drawerRef = useRef<HTMLDivElement>(null);

        // Focus trap
        useEffect(() => {
            if (!open) return;
            const previouslyFocused = document.activeElement as HTMLElement;
            const focusEl = initialFocusRef?.current || drawerRef.current;
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

        // Get the appropriate drawer animation variant based on side
        const getDrawerVariant = () => {
            if (side === 'left') return drawerVariants.left;
            if (side === 'bottom') return drawerVariants.bottom;
            return drawerVariants.right; // default to right
        };

        return (
            <AnimatePresence mode="wait">
                {open && (
                    <motion.div
                        className={cn(
                            'fixed inset-0 z-50 flex',
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
                        {/* Backdrop */}
                        <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
                        
                        {/* Drawer content */}
                        <motion.div
                            ref={ref || drawerRef}
                            className={cn(
                                'absolute bg-white dark:bg-neutral-900 shadow-xl outline-none overflow-y-auto',
                                sideStyles[side],
                                side === 'left' || side === 'right' ? sizeStyles[size] : 'h-auto max-h-[80vh]',
                                side === 'left' && 'rounded-r-xl',
                                side === 'right' && 'rounded-l-xl',
                                side === 'top' && 'rounded-b-xl',
                                side === 'bottom' && 'rounded-t-xl',
                                className,
                            )}
                            initial="hidden"
                            animate="visible"
                            exit="exit"
                            variants={getDrawerVariant()}
                            onClick={(e) => e.stopPropagation()}
                            tabIndex={-1}
                            aria-labelledby={ariaLabelledBy}
                            aria-describedby={ariaDescribedBy}
                        >
                            <div className="p-6">
                                {showClose && (
                                    <button
                                        type="button"
                                        onClick={onClose}
                                        className="absolute right-4 top-4 text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300 focus:outline-none transition-colors"
                                        aria-label="Close drawer"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                )}
                                {title && (
                                    <h2 id={ariaLabelledBy || 'drawer-title'} className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2 pr-8">
                                        {title}
                                    </h2>
                                )}
                                {description && (
                                    <p id={ariaDescribedBy || 'drawer-desc'} className="mb-4 text-neutral-600 dark:text-neutral-300">
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

Drawer2.displayName = 'Drawer2';

export default Drawer2;
