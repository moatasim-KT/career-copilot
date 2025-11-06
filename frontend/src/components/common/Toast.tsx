/**
 * Toast Notification System
 * 
 * Enterprise-grade toast notification system with queue management,
 * positioning, animations, and accessibility support.
 * 
 * @module components/common/Toast
 */

'use client';

import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';
export type ToastPosition = 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';

export interface Toast {
    id: string;
    type: ToastType;
    title?: string;
    message: string;
    duration?: number;
    action?: {
        label: string;
        onClick: () => void;
    };
}

interface ToastContextValue {
    toasts: Toast[];
    showToast: (toast: Omit<Toast, 'id'>) => string;
    hideToast: (id: string) => void;
    clearAll: () => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

/**
 * Toast Provider Component
 * 
 * Manages toast state and provides context for toast notifications
 * 
 * @example
 * ```tsx
 * function App() {
 *   return (
 *     <ToastProvider position="top-right" maxToasts={5}>
 *       <YourApp />
 *     </ToastProvider>
 *   );
 * }
 * ```
 */
export function ToastProvider({
    children,
    position = 'top-right',
    maxToasts = 5,
}: {
    children: React.ReactNode;
    position?: ToastPosition;
    maxToasts?: number;
}) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = useCallback(
        (toast: Omit<Toast, 'id'>): string => {
            const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const newToast: Toast = {
                id,
                duration: 5000,
                ...toast,
            };

            setToasts((prev) => {
                const updated = [...prev, newToast];
                // Keep only the latest maxToasts
                return updated.slice(-maxToasts);
            });

            // Auto-dismiss after duration
            if (newToast.duration && newToast.duration > 0) {
                setTimeout(() => {
                    hideToast(id);
                }, newToast.duration);
            }

            return id;
        },
        [maxToasts],
    );

    const hideToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, []);

    const clearAll = useCallback(() => {
        setToasts([]);
    }, []);

    const value: ToastContextValue = {
        toasts,
        showToast,
        hideToast,
        clearAll,
    };

    return (
        <ToastContext.Provider value={value}>
            {children}
            <ToastContainer toasts={toasts} position={position} onClose={hideToast} />
        </ToastContext.Provider>
    );
}

/**
 * useToast Hook
 * 
 * Provides access to toast functions
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { success, error, info, warning } = useToast();
 *   
 *   const handleSubmit = async () => {
 *     try {
 *       await submitForm();
 *       success('Form submitted successfully!');
 *     } catch (err) {
 *       error('Failed to submit form');
 *     }
 *   };
 * }
 * ```
 */
export function useToast() {
    const context = useContext(ToastContext);

    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }

    const { showToast, hideToast, clearAll } = context;

    return {
        success: (message: string, title?: string, action?: Toast['action']) =>
            showToast({ type: 'success', message, title, action }),
        error: (message: string, title?: string, action?: Toast['action']) =>
            showToast({ type: 'error', message, title, action }),
        info: (message: string, title?: string, action?: Toast['action']) =>
            showToast({ type: 'info', message, title, action }),
        warning: (message: string, title?: string, action?: Toast['action']) =>
            showToast({ type: 'warning', message, title, action }),
        custom: showToast,
        dismiss: hideToast,
        dismissAll: clearAll,
    };
}

/**
 * Toast Container Component
 * 
 * Renders the toast notifications in the specified position
 */
function ToastContainer({
    toasts,
    position,
    onClose,
}: {
    toasts: Toast[];
    position: ToastPosition;
    onClose: (id: string) => void;
}) {
    const positionClasses = {
        'top-left': 'top-4 left-4',
        'top-center': 'top-4 left-1/2 -translate-x-1/2',
        'top-right': 'top-4 right-4',
        'bottom-left': 'bottom-4 left-4',
        'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
        'bottom-right': 'bottom-4 right-4',
    };

    return (
        <div
            className={`fixed ${positionClasses[position]} z-[9999] pointer-events-none`}
            aria-live="polite"
            aria-atomic="true"
        >
            <div className="flex flex-col gap-2 pointer-events-auto">
                {toasts.map((toast) => (
                    <ToastItem key={toast.id} toast={toast} onClose={onClose} />
                ))}
            </div>
        </div>
    );
}

/**
 * Toast Item Component
 * 
 * Individual toast notification with icon, message, and actions
 */
function ToastItem({ toast, onClose }: { toast: Toast; onClose: (id: string) => void }) {
    const [isExiting, setIsExiting] = useState(false);

    const handleClose = () => {
        setIsExiting(true);
        setTimeout(() => onClose(toast.id), 300);
    };

    const icons = {
        success: CheckCircle,
        error: AlertCircle,
        info: Info,
        warning: AlertTriangle,
    };

    const colors = {
        success: 'bg-green-50 border-green-200 text-green-900',
        error: 'bg-red-50 border-red-200 text-red-900',
        info: 'bg-blue-50 border-blue-200 text-blue-900',
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    };

    const iconColors = {
        success: 'text-green-600',
        error: 'text-red-600',
        info: 'text-blue-600',
        warning: 'text-yellow-600',
    };

    const Icon = icons[toast.type];

    return (
        <div
            className={`
        min-w-[300px] max-w-md rounded-lg border shadow-lg p-4
        ${colors[toast.type]}
        transform transition-all duration-300 ease-in-out
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
      `}
            role="alert"
            aria-live="assertive"
        >
            <div className="flex items-start gap-3">
                <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${iconColors[toast.type]}`} />

                <div className="flex-1 min-w-0">
                    {toast.title && (
                        <h3 className="font-semibold text-sm mb-1">{toast.title}</h3>
                    )}
                    <p className="text-sm">{toast.message}</p>

                    {toast.action && (
                        <button
                            onClick={() => {
                                toast.action!.onClick();
                                handleClose();
                            }}
                            className="mt-2 text-sm font-medium underline hover:no-underline"
                        >
                            {toast.action.label}
                        </button>
                    )}
                </div>

                <button
                    onClick={handleClose}
                    className="flex-shrink-0 p-1 rounded-md hover:bg-black/5 transition-colors"
                    aria-label="Close notification"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}
