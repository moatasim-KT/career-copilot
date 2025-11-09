'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ReactNode, forwardRef, HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';
import {
  skeletonToContentVariants,
  contentFromSkeletonVariants,
} from '@/lib/animations';

export interface LoadingTransitionProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Whether content is loading
   */
  loading: boolean;

  /**
   * Skeleton component to show while loading
   */
  skeleton: ReactNode;

  /**
   * Actual content to show when loaded
   */
  children: ReactNode;

  /**
   * Delay before showing content (in seconds)
   */
  delay?: number;

  /**
   * Custom transition duration (in seconds)
   */
  duration?: number;
}

/**
 * LoadingTransition - Smooth skeleton to content crossfade
 * 
 * Features:
 * - Smooth crossfade between skeleton and content
 * - Prevents layout shift
 * - Accessible loading states
 * - Customizable timing
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <LoadingTransition
 *   loading={isLoading}
 *   skeleton={<Skeleton2 height={100} />}
 * >
 *   <div>Actual content here</div>
 * </LoadingTransition>
 * 
 * // With custom timing
 * <LoadingTransition
 *   loading={isLoading}
 *   skeleton={<JobCardSkeleton />}
 *   delay={0.2}
 *   duration={0.4}
 * >
 *   <JobCard job={job} />
 * </LoadingTransition>
 * ```
 */
export const LoadingTransition = forwardRef<HTMLDivElement, LoadingTransitionProps>(
  (
    {
      loading,
      skeleton,
      children,
      delay = 0.1,
      duration = 0.3,
      className,
      ...props
    },
    ref,
  ) => {
    return (
      <div
        ref={ref}
        className={cn('relative', className)}
        {...props}
      >
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="skeleton"
              variants={skeletonToContentVariants}
              initial="content"
              animate="skeleton"
              exit="content"
              transition={{ duration }}
            >
              {skeleton}
            </motion.div>
          ) : (
            <motion.div
              key="content"
              variants={contentFromSkeletonVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              transition={{ duration, delay }}
            >
              {children}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  },
);

LoadingTransition.displayName = 'LoadingTransition';

export default LoadingTransition;
