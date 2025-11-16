
'use client';

import { ReactNode, forwardRef, HTMLAttributes } from 'react';

import { fadeInUp, staggerItem } from '@/lib/animations';
import { m } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  elevation?: 0 | 1 | 2 | 3 | 4 | 5;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  interactive?: boolean;
  gradient?: boolean;
  // New props for enhanced hover effects
  featured?: boolean; // Adds glow effect for featured/premium cards
  gradientBorder?: boolean; // Adds animated gradient border using pseudo-element
  glowColor?: 'primary' | 'success' | 'warning' | 'error'; // Color of the glow effect
  // Animation controls
  animateOnMount?: boolean; // whether to play entrance animation on mount
  entrance?: 'fade' | 'slideUp' | 'scale';
  index?: number; // optional index for staggered lists
}

const elevations = {
  0: '',
  1: 'shadow-sm',
  2: 'shadow-md',
  3: 'shadow-lg',
  4: 'shadow-xl',
  5: 'shadow-2xl',
};

const paddings = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
  xl: 'p-10',
};

// Glow colors for featured cards
const glowColors = {
  primary: 'shadow-primary-500/50 dark:shadow-primary-400/50',
  success: 'shadow-success-500/50 dark:shadow-success-400/50',
  warning: 'shadow-warning-500/50 dark:shadow-warning-400/50',
  error: 'shadow-error-500/50 dark:shadow-error-400/50',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      elevation = 1,
      padding = 'md',
      hover = false,
      interactive = false,
      gradient = false,
      featured = false,
      gradientBorder = false,
      glowColor = 'primary',
      animateOnMount = true,
      entrance = 'fade',
      index = 0,
      className,
      ...props
    },
    ref,
  ) => {
    // choose variant based on entrance prop
    let variants = undefined as any;
    if (animateOnMount) {
      // small mapping; default to fadeInUp variant from animations
      variants = entrance === 'scale' ? undefined : fadeInUp;
    }

    const transition = animateOnMount ? { duration: 0.28, delay: index ? index * 0.06 : 0 } : undefined;

    // Enhanced hover animation with smooth shadow expansion
    const hoverAnimation = hover
      ? {
        y: -6,
        scale: 1.02,
        transition: {
          duration: 0.2,
          ease: 'easeOut',
        },
      }
      : undefined;

    return (
      <div className={cn(gradientBorder && 'relative p-[2px] rounded-xl group')}>
        {/* Gradient border background - only visible on hover */}
        {gradientBorder && (
          <div
            className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{
              background:
                'linear-gradient(135deg, rgb(59 130 246) 0%, rgb(147 197 253) 50%, rgb(59 130 246) 100%)',
              backgroundSize: '200% 200%',
              animation: 'gradient-shift 3s ease infinite',
            }}
          />
        )}

        <m.div
          ref={ref}
          className={cn(
            'bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700',
            'transition-all duration-200',
            elevations[elevation],
            paddings[padding],
            // Enhanced hover effects with smooth shadow expansion
            hover && ['hover:shadow-xl dark:hover:shadow-2xl', 'hover:-translate-y-1'],
            // Glow effect for featured/premium cards
            featured && [
              'shadow-lg',
              `hover:shadow-2xl hover:${glowColors[glowColor]}`,
              'ring-1 ring-primary-200 dark:ring-primary-800',
            ],
            interactive && 'cursor-pointer',
            gradient && 'relative overflow-hidden',
            // For gradient border, ensure the card is positioned relative to the wrapper
            gradientBorder && 'relative',
            className,
          )}
          variants={variants || staggerItem}
          initial={animateOnMount ? 'hidden' : undefined}
          animate={animateOnMount ? 'visible' : undefined}
          transition={transition}
          whileHover={hoverAnimation}
          {...(props as any)}
        >
          {gradient && (
            <div className="absolute inset-0 bg-gradient-to-br from-primary-50 to-transparent opacity-50 pointer-events-none dark:from-primary-950 dark:opacity-30" />
          )}

          <div className="relative">{children}</div>
        </m.div>
      </div>
    );
  },
);

Card.displayName = 'Card';

export { Card as Card2 };

export const CardHeader = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('mb-4 space-y-1.5', className)}>{children}</div>
);

export const CardTitle = ({ children, className }: { children: ReactNode; className?: string }) => (
  <h3 className={cn('text-lg md:text-2xl font-semibold text-neutral-900 dark:text-neutral-100', className)}>
    {children}
  </h3>
);

export const CardDescription = ({ children, className }: { children: ReactNode; className?: string }) => (
  <p className={cn('text-sm text-neutral-600 dark:text-neutral-400', className)}>{children}</p>
);

export const CardContent = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('space-y-4', className)}>{children}</div>
);

export const CardFooter = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('mt-6 flex items-center justify-between', className)}>{children}</div>
);

export default Card;
