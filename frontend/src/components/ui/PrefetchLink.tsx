/**
 * Enhanced Link component with automatic route prefetching
 * Prefetches routes on hover to improve perceived performance
 */

import Link from 'next/link';
import { ComponentProps } from 'react';

import { useRoutePrefetch } from '@/hooks/useRoutePrefetch';

interface PrefetchLinkProps extends ComponentProps<typeof Link> {
  /**
   * Whether to enable prefetching
   * @default true
   */
  prefetch?: boolean;
  
  /**
   * Delay in milliseconds before prefetching starts
   * @default 50
   */
  prefetchDelay?: number;
}

/**
 * Link component with automatic route prefetching on hover
 * 
 * @example
 * ```tsx
 * <PrefetchLink href="/dashboard">
 *   Go to Dashboard
 * </PrefetchLink>
 * ```
 */
export function PrefetchLink({
  href,
  prefetch = true,
  prefetchDelay = 50,
  onMouseEnter,
  onMouseLeave,
  onTouchStart,
  ...props
}: PrefetchLinkProps) {
  const prefetchHandlers = useRoutePrefetch(
    typeof href === 'string' ? href : href.pathname || '',
    { 
      enabled: prefetch,
      delay: prefetchDelay 
    }
  );

  return (
    <Link
      href={href}
      onMouseEnter={(e) => {
        prefetchHandlers.onMouseEnter();
        onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        prefetchHandlers.onMouseLeave();
        onMouseLeave?.(e);
      }}
      onTouchStart={(e) => {
        prefetchHandlers.onTouchStart();
        onTouchStart?.(e);
      }}
      {...props}
    />
  );
}
