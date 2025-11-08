'use client';

import { forwardRef, useEffect, useRef } from 'react';
import { X } from 'lucide-react';
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

        if (!open) return null;

        return (
            <div
                className={cn(
                    'fixed inset-0 z-50 flex bg-black/30',
                    overlayClassName
                )}
                aria-modal="true"
                role="dialog"
                tabIndex={-1}
            >
                <div
                    ref={ref || drawerRef}
                    className={cn(
                        'absolute bg-white dark:bg-neutral-900 shadow-xl outline-none transition-all duration-300',
                        sideStyles[side],
                        sizeStyles[size],
                        'rounded-tl-xl rounded-bl-xl rounded-tr-xl rounded-br-xl',
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
                            aria-label="Close drawer"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    )}
                    {title && (
                        <h2 id={ariaLabelledBy || 'drawer-title'} className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
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
            </div>
        );
    },
);

Drawer2.displayName = 'Drawer2';

export default Drawer2;
