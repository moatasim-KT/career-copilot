'use client';

import { usePathname } from 'next/navigation';
import React from 'react';

import { pageTransition } from '@/lib/animations';
import { AnimatePresence, m, MotionProvider } from '@/lib/motion';

interface PageTransitionProps {
    children: React.ReactNode;
}

/**
 * PageTransition component
 * 
 * Wraps page content with AnimatePresence to provide smooth transitions
 * between route changes. Uses the current pathname as the key to trigger
 * animations when navigating between pages.
 * 
 * Features:
 * - Fade in/out with subtle vertical movement
 * - Wait mode ensures exit animation completes before enter animation
 * - Automatically detects route changes via usePathname
 */
export default function PageTransition({ children }: PageTransitionProps) {
    const pathname = usePathname();

    return (
        <MotionProvider>
            <AnimatePresence mode="wait" initial={false}>
                <m.div
                    key={pathname}
                    variants={pageTransition}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    style={{ minHeight: '100vh' }}
                >
                    {children}
                </m.div>
            </AnimatePresence>
        </MotionProvider>
    );
}
