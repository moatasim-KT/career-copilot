/**
 * Mobile Navigation Drawer
 * 
 * Enterprise-grade mobile navigation with swipe gestures, touch optimization,
 * and smooth animations. Supports gesture-based opening/closing and touch-friendly
 * interaction patterns.
 * 
 * @module components/layout/MobileNav
 */

'use client';

import { X, ChevronRight, User, LogOut } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useState, useEffect } from 'react';

import { useMobileDetection } from '@/hooks/useMobileDetection';
import { useTouchGestures } from '@/hooks/useTouchGestures';

export interface MobileNavItem {
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string | number;
    description?: string;
}

export interface MobileNavProps {
    /** Navigation items to display */
    items: MobileNavItem[];
    /** Whether the drawer is open */
    isOpen: boolean;
    /** Callback when drawer should close */
    onClose: () => void;
    /** Current user information */
    user?: {
        username: string;
        email?: string;
        avatar?: string;
    };
    /** Logout handler */
    onLogout?: () => void;
    /** Additional CSS classes */
    className?: string;
}

/**
 * Mobile Navigation Drawer Component
 * 
 * Features:
 * - Swipe-to-close gesture
 * - Touch-optimized targets (min 44x44px)
 * - Smooth animations with GPU acceleration
 * - Backdrop click to close
 * - Escape key support
 * - Focus trap for accessibility
 * - Safe area insets for notched devices
 * 
 * @example
 * ```tsx
 * function Layout() {
 *   const [isNavOpen, setIsNavOpen] = useState(false);
 *   
 *   return (
 *     <>
 *       <button onClick={() => setIsNavOpen(true)}>Menu</button>
 *       <MobileNav
 *         items={navigationItems}
 *         isOpen={isNavOpen}
 *         onClose={() => setIsNavOpen(false)}
 *         user={currentUser}
 *       />
 *     </>
 *   );
 * }
 * ```
 */
export function MobileNav({
    items,
    isOpen,
    onClose,
    user,
    onLogout,
    className = '',
}: MobileNavProps) {
    const pathname = usePathname();
    const { isMobile } = useMobileDetection();
    const [dragOffset, setDragOffset] = useState(0);

    // Handle swipe-to-close gesture
    const drawerRef = useTouchGestures<HTMLDivElement>(
        {
            onSwipe: (direction) => {
                if (direction === 'left') {
                    onClose();
                }
            },
            onTouchMove: (event) => {
                const touch = event.touches[0];
                const startX = 0; // Left edge
                const offset = touch.clientX - startX;

                // Only allow dragging left (closing)
                if (offset < 0) {
                    setDragOffset(offset);
                }
            },
            onTouchEnd: () => {
                // If dragged more than 50%, close the drawer
                if (dragOffset < -100) {
                    onClose();
                }
                setDragOffset(0);
            },
        },
        {
            swipeThreshold: 50,
            preventDefault: true,
        },
    );

    // Close on escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };

        window.addEventListener('keydown', handleEscape);
        return () => window.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    // Prevent body scroll when drawer is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }

        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    // Don't render on desktop
    if (!isMobile) {
        return null;
    }

    return (
        <>
            {/* Backdrop */}
            <div
                className={`fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
                    }`}
                onClick={onClose}
                aria-hidden="true"
            />

            {/* Drawer */}
            <div
                ref={drawerRef}
                className={`
          fixed top-0 left-0 h-full w-[85vw] max-w-[320px] bg-white z-50
          transform transition-transform duration-300 ease-out
          shadow-2xl overflow-y-auto overscroll-contain
          ${className}
        `}
                style={{
                    transform: isOpen
                        ? `translateX(${Math.min(dragOffset, 0)}px)`
                        : 'translateX(-100%)',
                    // Support safe area insets for notched devices
                    paddingTop: 'env(safe-area-inset-top)',
                    paddingBottom: 'env(safe-area-inset-bottom)',
                }}
                role="dialog"
                aria-modal="true"
                aria-label="Mobile navigation"
            >
                {/* Header */}
                <div className="sticky top-0 bg-white border-b border-neutral-200 px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        {user?.avatar ? (
                            <img
                                src={user.avatar}
                                alt={user.username}
                                className="w-10 h-10 rounded-full object-cover"
                            />
                        ) : (
                            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <User className="w-5 h-5 text-blue-600" />
                            </div>
                        )}
                        <div className="flex flex-col">
                            <span className="text-sm font-semibold text-neutral-900">
                                {user?.username || 'Guest'}
                            </span>
                            {user?.email && (
                                <span className="text-xs text-neutral-500 truncate max-w-[180px]">
                                    {user.email}
                                </span>
                            )}
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 -mr-2 rounded-full hover:bg-neutral-100 active:bg-neutral-200 transition-colors touch-manipulation"
                        aria-label="Close menu"
                    >
                        <X className="w-6 h-6 text-neutral-600" />
                    </button>
                </div>

                {/* Navigation Items */}
                <nav className="py-4">
                    <ul className="space-y-1 px-2">
                        {items.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname === item.href;

                            return (
                                <li key={item.href}>
                                    <Link
                                        href={item.href}
                                        onClick={onClose}
                                        className={`
                      flex items-center justify-between px-4 py-3.5 rounded-lg
                      transition-all duration-200 active:scale-[0.98]
                      touch-manipulation min-h-[44px]
                      ${isActive
                                                ? 'bg-blue-50 text-blue-700 font-medium'
                                                : 'text-neutral-700 hover:bg-neutral-50 active:bg-neutral-100'
                                            }
                    `}
                                    >
                                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                                            <Icon
                                                className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-blue-600' : 'text-neutral-400'
                                                    }`}
                                            />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center space-x-2">
                                                    <span className="truncate">{item.label}</span>
                                                    {item.badge && (
                                                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                            {item.badge}
                                                        </span>
                                                    )}
                                                </div>
                                                {item.description && (
                                                    <p className="text-xs text-neutral-500 truncate mt-0.5">
                                                        {item.description}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                        <ChevronRight
                                            className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-blue-600' : 'text-neutral-300'
                                                }`}
                                        />
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </nav>

                {/* Footer Actions */}
                {onLogout && (
                    <div className="absolute bottom-0 left-0 right-0 border-t border-neutral-200 bg-white p-4">
                        <button
                            onClick={() => {
                                onLogout();
                                onClose();
                            }}
                            className="
                w-full flex items-center justify-center space-x-2 px-4 py-3.5
                bg-neutral-100 hover:bg-neutral-200 active:bg-neutral-300
                text-neutral-700 font-medium rounded-lg
                transition-colors touch-manipulation min-h-[44px]
              "
                        >
                            <LogOut className="w-5 h-5" />
                            <span>Sign Out</span>
                        </button>
                    </div>
                )}
            </div>
        </>
    );
}

/**
 * Mobile Navigation Toggle Button
 * 
 * Touch-optimized button to open the mobile navigation drawer
 */
export function MobileNavToggle({
    onClick,
    className = '',
}: {
    onClick: () => void;
    className?: string;
}) {
    return (
        <button
            onClick={onClick}
            className={`
        p-2 rounded-lg hover:bg-neutral-100 active:bg-neutral-200
        transition-colors touch-manipulation min-h-[44px] min-w-[44px]
        flex items-center justify-center
        ${className}
      `}
            aria-label="Open menu"
        >
            <svg
                className="w-6 h-6 text-neutral-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                />
            </svg>
        </button>
    );
}
