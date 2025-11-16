import { X } from 'lucide-react';
import React, { useEffect } from 'react';

import { backdropVariants, drawerVariants } from '@/lib/animations';
import { AnimatePresence, m } from '@/lib/motion';

export interface DrawerProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    position?: 'left' | 'right' | 'top' | 'bottom';
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
    children: React.ReactNode;
}

const positionClasses = {
    left: 'left-0 top-0 h-full',
    right: 'right-0 top-0 h-full',
    top: 'top-0 left-0 w-full',
    bottom: 'bottom-0 left-0 w-full',
};

const sizeClasses = {
    sm: 'w-64',
    md: 'w-96',
    lg: 'w-[32rem]',
    xl: 'w-[48rem]',
    full: 'w-full h-full',
};

export default function Drawer({
    isOpen,
    onClose,
    title,
    position = 'right',
    size = 'md',
    children,
}: DrawerProps) {
    // Prevent background scroll when drawer is open
    useEffect(() => {
        if (!isOpen) return;
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    const posClass = positionClasses[position];
    const sizeClass = position === 'top' || position === 'bottom' ? 'h-96' : sizeClasses[size];

    // Get the appropriate drawer animation variant based on position
    const getDrawerVariant = () => {
        if (position === 'left') return drawerVariants.left;
        if (position === 'bottom') return drawerVariants.bottom;
        return drawerVariants.right; // default to right
    };

    return (
        <AnimatePresence mode="wait">
            {isOpen && (
                <m.div
                    className="fixed inset-0 z-50 flex"
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    variants={backdropVariants}
                    onClick={onClose}
                >
                    {/* Backdrop */}
                    <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
                    
                    {/* Drawer content */}
                    <m.div
                        className={`fixed bg-white dark:bg-gray-900 shadow-xl overflow-y-auto ${posClass} ${sizeClass} ${
                            position === 'left' ? 'rounded-r-lg' : 
                            position === 'right' ? 'rounded-l-lg' : 
                            position === 'top' ? 'rounded-b-lg' : 
                            'rounded-t-lg'
                        }`}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        variants={getDrawerVariant()}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
                            {title && <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h3>}
                            <button 
                                onClick={onClose} 
                                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                                aria-label="Close drawer"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-4">{children}</div>
                    </m.div>
                </m.div>
            )}
        </AnimatePresence>
    );
}
