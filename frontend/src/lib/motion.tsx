/**
 * Optimized Framer Motion exports using LazyMotion pattern
 * 
 * This module uses LazyMotion to reduce the initial bundle size by ~50-100KB.
 * Instead of importing the full motion library, we lazy-load only the features
 * we need (domAnimation).
 * 
 * Usage:
 * ```tsx
 * import { m, AnimatePresence, MotionProvider } from '@/lib/motion';
 * 
 * // Wrap your app or component tree with MotionProvider
 * <MotionProvider>
 *   <AnimatePresence>
 *     <m.div animate={{ opacity: 1 }}>Content</m.div>
 *   </AnimatePresence>
 * </MotionProvider>
 * ```
 */

import { LazyMotion, domAnimation, m as motion, AnimatePresence } from 'framer-motion';
import type { Variants, MotionProps } from 'framer-motion';

/**
 * Optimized motion component using lazy-loaded features.
 * Use `m` instead of `motion` for all animations.
 */
export { motion as m };

/**
 * AnimatePresence for exit animations.
 * Can be used directly without LazyMotion wrapper.
 */
export { AnimatePresence };

/**
 * Type exports for TypeScript support
 */
export type { Variants, MotionProps };

/**
 * MotionProvider component that wraps your app/component tree.
 * This enables lazy-loading of animation features, reducing bundle size.
 * 
 * Place this at the root of your component tree or around animated sections.
 * 
 * @example
 * ```tsx
 * <MotionProvider>
 *   <YourComponent />
 * </MotionProvider>
 * ```
 */
export function MotionProvider({ children }: { children: React.ReactNode }) {
    return (
        <LazyMotion features={domAnimation} strict>
            {children}
        </LazyMotion>
    );
}

/**
 * Convenience hook to use motion in a component that's already wrapped with MotionProvider.
 * Returns the optimized motion component.
 */
export const useMotion = () => motion;
