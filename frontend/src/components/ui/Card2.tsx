
'use client';

import { motion } from 'framer-motion';
import { ReactNode, forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  elevation?: 0 | 1 | 2 | 3 | 4 | 5;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  interactive?: boolean;
  gradient?: boolean;
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

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      elevation = 1,
      padding = 'md',
      hover = false,
      interactive = false,
      gradient = false,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <motion.div
        ref={ref}
        className={cn(
          'bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700',
          'transition-all duration-200',
          elevations[elevation],
          paddings[padding],
          hover && 'hover:shadow-lg hover:-translate-y-0.5',
          interactive && 'cursor-pointer',
          gradient && 'relative overflow-hidden',
          className
        )}
        whileHover={hover ? { y: -2 } : undefined}
        {...props}
      >
        {gradient && (
          <div className="absolute inset-0 bg-gradient-to-br from-primary-50 to-transparent opacity-50 pointer-events-none" />
        )}
        <div className="relative">{children}</div>
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('mb-4 space-y-1.5', className)}>{children}</div>
);

export const CardTitle = ({ children, className }: { children: ReactNode; className?: string }) => (
  <h3 className={cn('text-xl font-semibold text-neutral-900 dark:text-neutral-100', className)}>
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
