/**
 * Hook for prefetching Next.js routes on hover
 * Improves perceived performance by preloading critical routes
 */

import { useRouter } from 'next/navigation';
import { useCallback, useRef } from 'react';

import { logger } from '@/lib/logger';

interface PrefetchOptions {
  /**
   * Delay in milliseconds before prefetching starts
   * @default 50
   */
  delay?: number;
  
  /**
   * Whether to prefetch on hover
   * @default true
   */
  enabled?: boolean;
}

/**
 * Hook that provides prefetch handlers for Next.js routes
 * 
 * @example
 * ```tsx
 * const { onMouseEnter, onTouchStart } = useRoutePrefetch('/dashboard');
 * 
 * <Link href="/dashboard" onMouseEnter={onMouseEnter} onTouchStart={onTouchStart}>
 *   Dashboard
 * </Link>
 * ```
 */
export function useRoutePrefetch(
  href: string,
  options: PrefetchOptions = {},
) {
  const router = useRouter();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const prefetchedRef = useRef(false);
  
  const { delay = 50, enabled = true } = options;

  const prefetch = useCallback(() => {
    if (!enabled || prefetchedRef.current) return;
    
    try {
      router.prefetch(href);
      prefetchedRef.current = true;
    } catch (error) {
      // Silently fail - prefetch is an optimization, not critical
      logger.debug('Route prefetch failed:', href, error);
    }
  }, [router, href, enabled]);

  const onMouseEnter = useCallback(() => {
    if (!enabled) return;
    
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    // Prefetch after delay
    timeoutRef.current = setTimeout(prefetch, delay);
  }, [prefetch, delay, enabled]);

  const onMouseLeave = useCallback(() => {
    // Clear timeout if user moves away before delay completes
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const onTouchStart = useCallback(() => {
    // On touch devices, prefetch immediately on touch
    if (!enabled) return;
    prefetch();
  }, [prefetch, enabled]);

  return {
    onMouseEnter,
    onMouseLeave,
    onTouchStart,
  };
}

/**
 * Hook for prefetching multiple routes at once
 * Useful for prefetching all critical routes on app load
 * 
 * @example
 * ```tsx
 * usePrefetchRoutes(['/dashboard', '/jobs', '/applications']);
 * ```
 */
export function usePrefetchRoutes(routes: string[], enabled = true) {
  const router = useRouter();

  const prefetchAll = useCallback(() => {
    if (!enabled) return;
    
    routes.forEach((route) => {
      try {
        router.prefetch(route);
      } catch (error) {
        logger.debug('Route prefetch failed:', route, error);
      }
    });
  }, [router, routes, enabled]);

  return { prefetchAll };
}
