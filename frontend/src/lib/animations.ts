/**
 * Animation System
 * 
 * Centralized animation variants and configurations for Framer Motion.
 * Provides consistent animations across the application.
 */

import { Variants, Transition } from 'framer-motion';

/**
 * Fade animation variants
 */
export const fadeVariants: Variants = {
  hidden: { 
    opacity: 0 
  },
  visible: { 
    opacity: 1, 
    transition: { 
      duration: 0.2,
      ease: 'easeOut'
    } 
  },
  exit: { 
    opacity: 0, 
    transition: { 
      duration: 0.15,
      ease: 'easeIn'
    } 
  }
};

/**
 * Slide animation variants
 */
export const slideVariants = {
  left: {
    hidden: { 
      x: -20, 
      opacity: 0 
    },
    visible: { 
      x: 0, 
      opacity: 1,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    }
  },
  right: {
    hidden: { 
      x: 20, 
      opacity: 0 
    },
    visible: { 
      x: 0, 
      opacity: 1,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    }
  },
  up: {
    hidden: { 
      y: 20, 
      opacity: 0 
    },
    visible: { 
      y: 0, 
      opacity: 1,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    }
  },
  down: {
    hidden: { 
      y: -20, 
      opacity: 0 
    },
    visible: { 
      y: 0, 
      opacity: 1,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    }
  }
};

/**
 * Scale animation variants
 */
export const scaleVariants: Variants = {
  hidden: { 
    scale: 0.95, 
    opacity: 0 
  },
  visible: { 
    scale: 1, 
    opacity: 1,
    transition: {
      duration: 0.2,
      ease: 'easeOut'
    }
  },
  exit: { 
    scale: 0.95, 
    opacity: 0,
    transition: {
      duration: 0.15,
      ease: 'easeIn'
    }
  }
};

/**
 * Stagger container for animating children sequentially
 */
export const staggerContainer: Variants = {
  hidden: { 
    opacity: 0 
  },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.05
    }
  }
};

/**
 * Stagger item for use within staggerContainer
 */
export const staggerItem: Variants = {
  hidden: { 
    y: 20, 
    opacity: 0 
  },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.3,
      ease: 'easeOut'
    }
  }
};

/**
 * Spring animation configurations
 */
export const springConfigs = {
  gentle: { 
    type: 'spring' as const, 
    stiffness: 100, 
    damping: 15 
  },
  bouncy: { 
    type: 'spring' as const, 
    stiffness: 300, 
    damping: 20 
  },
  stiff: { 
    type: 'spring' as const, 
    stiffness: 400, 
    damping: 30 
  },
  smooth: {
    type: 'spring' as const,
    stiffness: 200,
    damping: 25
  }
};

/**
 * Duration constants (in seconds)
 */
export const durations = {
  fast: 0.15,
  normal: 0.2,
  slow: 0.3,
  slower: 0.5
};

/**
 * Easing functions
 */
export const easings = {
  easeIn: [0.4, 0, 1, 1],
  easeOut: [0, 0, 0.2, 1],
  easeInOut: [0.4, 0, 0.2, 1],
  sharp: [0.4, 0, 0.6, 1]
};

/**
 * Hover animation for interactive elements
 */
export const hoverScale: Transition = {
  scale: 1.02,
  transition: {
    duration: durations.fast,
    ease: 'easeOut'
  }
};

/**
 * Tap animation for buttons
 */
export const tapScale: Transition = {
  scale: 0.98,
  transition: {
    duration: durations.fast,
    ease: 'easeIn'
  }
};

/**
 * List item animation variants
 */
export const listItemVariants: Variants = {
  hidden: { 
    x: -10, 
    opacity: 0 
  },
  visible: (index: number) => ({
    x: 0,
    opacity: 1,
    transition: {
      delay: index * 0.05,
      duration: 0.3,
      ease: 'easeOut'
    }
  })
};

/**
 * Modal/Dialog animation variants
 */
export const modalVariants: Variants = {
  hidden: { 
    scale: 0.95, 
    opacity: 0,
    y: 20
  },
  visible: { 
    scale: 1, 
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.2,
      ease: 'easeOut'
    }
  },
  exit: { 
    scale: 0.95, 
    opacity: 0,
    y: 20,
    transition: {
      duration: 0.15,
      ease: 'easeIn'
    }
  }
};

/**
 * Backdrop animation variants
 */
export const backdropVariants: Variants = {
  hidden: { 
    opacity: 0 
  },
  visible: { 
    opacity: 1,
    transition: {
      duration: 0.2
    }
  },
  exit: { 
    opacity: 0,
    transition: {
      duration: 0.15
    }
  }
};

/**
 * Drawer animation variants
 */
export const drawerVariants = {
  left: {
    hidden: { x: '-100%' },
    visible: { 
      x: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30
      }
    },
    exit: { 
      x: '-100%',
      transition: {
        duration: 0.2,
        ease: 'easeIn'
      }
    }
  },
  right: {
    hidden: { x: '100%' },
    visible: { 
      x: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30
      }
    },
    exit: { 
      x: '100%',
      transition: {
        duration: 0.2,
        ease: 'easeIn'
      }
    }
  },
  bottom: {
    hidden: { y: '100%' },
    visible: { 
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30
      }
    },
    exit: { 
      y: '100%',
      transition: {
        duration: 0.2,
        ease: 'easeIn'
      }
    }
  }
};

/**
 * Skeleton loading animation
 */
export const skeletonVariants: Variants = {
  initial: {
    backgroundPosition: '200% 0'
  },
  animate: {
    backgroundPosition: '-200% 0',
    transition: {
      duration: 1.5,
      ease: 'linear',
      repeat: Infinity
    }
  }
};

/**
 * Success checkmark animation
 */
export const checkmarkVariants: Variants = {
  hidden: {
    pathLength: 0,
    opacity: 0
  },
  visible: {
    pathLength: 1,
    opacity: 1,
    transition: {
      pathLength: {
        duration: 0.5,
        ease: 'easeOut'
      },
      opacity: {
        duration: 0.2
      }
    }
  }
};

/**
 * Error shake animation
 */
export const shakeVariants: Variants = {
  shake: {
    x: [0, -10, 10, -10, 10, 0],
    transition: {
      duration: 0.4
    }
  }
};

/**
 * Pulse animation for notifications
 */
export const pulseVariants: Variants = {
  pulse: {
    scale: [1, 1.05, 1],
    transition: {
      duration: 0.6,
      repeat: Infinity,
      repeatDelay: 1
    }
  }
};

/**
 * Rotate animation for loading spinners
 */
export const rotateVariants: Variants = {
  rotate: {
    rotate: 360,
    transition: {
      duration: 1,
      ease: 'linear',
      repeat: Infinity,
    },
  },
};

/**
 * Fade in up animation (commonly used for cards and content)
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
