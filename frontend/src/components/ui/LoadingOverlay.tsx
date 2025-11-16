'use client';

import { ReactNode, forwardRef } from 'react';

import { loadingOverlayVariants } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
import { cn } from '@/lib/utils';

import DotsLoader from './DotsLoader';
import Spinner2 from './Spinner2';

export interface LoadingOverlayProps {
  /**
   * Whether the overlay is visible
   */
  visible: boolean;

  /**
   * Loading indicator type
   */
  indicator?: 'spinner' | 'dots' | 'custom';

  /**
   * Custom loading indicator
   */
  customIndicator?: ReactNode;

  /**
   * Loading message
   */
  message?: string;

  /**
   * Whether to blur the background
   */
  blur?: boolean;

  /**
   * Whether to make the overlay full screen
   */
  fullScreen?: boolean;

  /**
   * Background opacity (0-1)
   */
  opacity?: number;

  /**
   * Additional CSS classes
   */
  className?: string;
}

/**
 * LoadingOverlay - Full-screen or container loading overlay
 * 
 * Features:
 * - Smooth fade in/out with backdrop blur
 * - Multiple indicator types
 * - Optional loading message
 * - Full-screen or container-relative positioning
 * - Accessible with ARIA labels
 * 
 * @example
 * ```tsx
 * // Basic full-screen overlay
 * <LoadingOverlay visible={isLoading} />
 * 
 * // With message and dots loader
 * <LoadingOverlay
 *   visible={isLoading}
 *   indicator="dots"
 *   message="Loading your data..."
 * />
 * 
 * // Container-relative with custom indicator
 * <div className="relative">
 *   <LoadingOverlay
 *     visible={isLoading}
 *     fullScreen={false}
 *     indicator="custom"
 *     customIndicator={<MyCustomLoader />}
 *   />
 *   <div>Container content</div>
 * </div>
 * 
 * // With blur effect
 * <LoadingOverlay
 *   visible={isLoading}
 *   blur
 *   message="Processing..."
 * />
 * ```
 */
export const LoadingOverlay = forwardRef<HTMLDivElement, LoadingOverlayProps>(
  (
    {
      visible,
      indicator = 'spinner',
      customIndicator,
      message,
      blur = true,
      fullScreen = true,
      opacity = 0.8,
      className,
    },
    ref,
  ) => {
    const renderIndicator = () => {
      if (indicator === 'custom' && customIndicator) {
        return customIndicator;
      }

      if (indicator === 'dots') {
        return <DotsLoader size="lg" color="primary" label={message || 'Loading'} />;
      }

      return (
        <Spinner2
          size="lg"
          variant="smooth"
          color="primary"
          label={message || 'Loading'}
        />
      );
    };

    return (
      <AnimatePresence>
        {visible && (
          <m.div
            ref={ref}
            variants={loadingOverlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={cn(
              'z-50 flex flex-col items-center justify-center gap-4',
              fullScreen ? 'fixed inset-0' : 'absolute inset-0',
              className,
            )}
            style={{
              backgroundColor: `rgba(255, 255, 255, ${opacity})`,
              backdropFilter: blur ? 'blur(4px)' : undefined,
            }}
            role="status"
            aria-live="polite"
            aria-busy="true"
          >
            {/* Dark mode background */}
            <div className="absolute inset-0 bg-neutral-900/80 dark:bg-neutral-950/90" />

            {/* Content */}
            <div className="relative z-10 flex flex-col items-center justify-center gap-4">
              {renderIndicator()}

              {message && (
                <m.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1, duration: 0.3 }}
                  className="text-sm font-medium text-neutral-700 dark:text-neutral-300"
                >
                  {message}
                </m.p>
              )}
            </div>
          </m.div>
        )}
      </AnimatePresence>
    );
  },
);

LoadingOverlay.displayName = 'LoadingOverlay';

export default LoadingOverlay;
