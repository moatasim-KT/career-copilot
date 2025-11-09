/**
 * Animation variants for Framer Motion
 * 
 * This file contains reusable animation configurations
 * that can be used across the application.
 *
 * Extended: Added rotate, page transitions, spring configs, and duration constants.
 */

import type { Variants } from 'framer-motion';

// Duration constants
export const DURATION = {
    fast: 0.15,
    normal: 0.2,
    slow: 0.3,
};

// Spring configs
export const SPRING = {
    gentle: { type: 'spring', stiffness: 120, damping: 20 },
    bouncy: { type: 'spring', stiffness: 300, damping: 15 },
    stiff: { type: 'spring', stiffness: 500, damping: 30 },
};
/**
 * Rotate animation
 */
export const rotate: Variants = {
    hidden: { rotate: -10, opacity: 0 },
    visible: { rotate: 0, opacity: 1, transition: { duration: DURATION.normal } },
    exit: { rotate: 10, opacity: 0, transition: { duration: DURATION.fast } },
};

/**
 * Page transition variants
 */
export const pageTransition: Variants = {
    initial: { opacity: 0, y: 24 },
    animate: { opacity: 1, y: 0, transition: { duration: DURATION.normal } },
    exit: { opacity: 0, y: -24, transition: { duration: DURATION.fast } },
};

/**
 * Fade in animation from opacity 0 to 1
 */
export const fadeIn: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
};

/**
 * Fade in and move up animation
 */
export const fadeInUp: Variants = {
    hidden: {
        opacity: 0,
        y: 20,
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.3,
            ease: 'easeOut',
        },
    },
};

/**
 * Fade in and move down animation
 */
export const fadeInDown: Variants = {
    hidden: {
        opacity: 0,
        y: -20,
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.3,
            ease: 'easeOut',
        },
    },
};

/**
 * Scale up animation
 */
export const scaleIn: Variants = {
    hidden: {
        opacity: 0,
        scale: 0.9,
    },
    visible: {
        opacity: 1,
        scale: 1,
        transition: {
            duration: 0.2,
            ease: 'easeOut',
        },
    },
};

/**
 * Slide in from left animation
 */
export const slideInLeft: Variants = {
    hidden: {
        opacity: 0,
        x: -20,
    },
    visible: {
        opacity: 1,
        x: 0,
        transition: {
            duration: 0.3,
            ease: 'easeOut',
        },
    },
};

/**
 * Slide in from right animation
 */
export const slideInRight: Variants = {
    hidden: {
        opacity: 0,
        x: 20,
    },
    visible: {
        opacity: 1,
        x: 0,
        transition: {
            duration: 0.3,
            ease: 'easeOut',
        },
    },
};

/**
 * Stagger children animation
 * Use with parent element to animate children in sequence
 */
export const staggerContainer: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
        },
    },
};

/**
 * Animation for list items in a staggered container
 */
export const staggerItem: Variants = {
    hidden: {
        opacity: 0,
        y: 20,
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.3,
            ease: 'easeOut',
        },
    },
};

/**
 * Modal backdrop animation
 */
export const modalBackdrop: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            duration: 0.2,
        },
    },
    exit: {
        opacity: 0,
        transition: {
            duration: 0.2,
        },
    },
};

/**
 * Modal content animation
 */
export const modalContent: Variants = {
    hidden: {
        opacity: 0,
        scale: 0.95,
        y: 20,
    },
    visible: {
        opacity: 1,
        scale: 1,
        y: 0,
        transition: {
            duration: 0.2,
            ease: 'easeOut',
        },
    },
    exit: {
        opacity: 0,
        scale: 0.95,
        y: 20,
        transition: {
            duration: 0.15,
            ease: 'easeIn',
        },
    },
};

/**
 * Button hover animation
 */
export const buttonHover = {
    scale: 1.02,
    transition: {
        duration: 0.15,
        ease: [0.4, 0, 0.2, 1] as const,
    },
};

/**
 * Button tap animation
 */
export const buttonTap = {
    scale: 0.98,
};/**
 * Card hover animation
 */
export const cardHover = {
    y: -4,
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    transition: {
        duration: 0.2,
        ease: [0.4, 0, 0.2, 1] as const,
    },
};

/**
 * Transition preset for smooth animations
 */
export const smoothTransition = {
    duration: 0.3,
    ease: 'easeInOut',
};

/**
 * Transition preset for quick animations
 */
export const quickTransition = {
    duration: 0.15,
    ease: 'easeInOut',
};

/**
 * Transition preset for slow animations
 */
export const slowTransition = {
    duration: 0.5,
    ease: 'easeInOut',
};
