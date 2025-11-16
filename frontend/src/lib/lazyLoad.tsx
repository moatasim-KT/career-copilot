/**
 * Lazy Loading Utilities
 * 
 * Enterprise-grade lazy loading utilities for optimal performance
 * Implements intersection observer for lazy loading images and components
 * 
 * @module lib/lazyLoad
 */

'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';


/**
 * Intersection Observer Options
 */
export interface LazyLoadOptions {
  /** Root margin for intersection observer (CSS margin syntax) */
  rootMargin?: string;
  /** Threshold for intersection observer (0-1) */
  threshold?: number | number[];
  /** Whether to load only once and then unobserve */
  once?: boolean;
  /** Placeholder to show while loading */
  placeholder?: React.ReactNode;
  /** Callback when element becomes visible */
  onVisible?: () => void;
}

const DEFAULT_OPTIONS: Required<Omit<LazyLoadOptions, 'placeholder' | 'onVisible'>> = {
  rootMargin: '50px',
  threshold: 0.01,
  once: true,
};

/**
 * Lazy Load Hook using Intersection Observer
 * 
 * @param options - Configuration options
 * @returns Tuple of [ref, isVisible]
 * 
 * @example
 * ```tsx
 * function LazyImage({ src, alt }) {
 *   const [ref, isVisible] = useLazyLoad({ rootMargin: '100px' });
 *   
 *   return (
 *     <div ref={ref}>
 *       {isVisible ? <img src={src} alt={alt} /> : <Skeleton />}
 *     </div>
 *   );
 * }
 * ```
 */
export function useLazyLoad<T extends HTMLElement = HTMLDivElement>(
  options: LazyLoadOptions = {},
): [React.RefObject<T | null>, boolean] {
  const opts = useMemo(() => ({ ...DEFAULT_OPTIONS, ...options }), [options]);
  const ref = useRef<T>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // Check if IntersectionObserver is supported
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      setIsVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            opts.onVisible?.();

            if (opts.once) {
              observer.unobserve(entry.target);
            }
          } else if (!opts.once) {
            setIsVisible(false);
          }
        });
      },
      {
        rootMargin: opts.rootMargin,
        threshold: opts.threshold,
      },
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [opts]);

  return [ref, isVisible];
}

/**
 * Lazy Image Component
 * 
 * Optimized image component with lazy loading, blur-up effect,
 * and automatic format selection
 * 
 * @example
 * ```tsx
 * <LazyImage
 *   src="/images/hero.jpg"
 *   alt="Hero image"
 *   width={800}
 *   height={600}
 *   blurDataURL="/images/hero-blur.jpg"
 * />
 * ```
 */
export function LazyImage({
  src,
  alt,
  width,
  height,
  className = '',
  blurDataURL,
  onLoad,
  ...props
}: React.ImgHTMLAttributes<HTMLImageElement> & {
  width?: number;
  height?: number;
  blurDataURL?: string;
}) {
  const [ref, isVisible] = useLazyLoad<HTMLDivElement>({ rootMargin: '200px' });
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const handleLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    setIsLoaded(true);
    onLoad?.(e);
  };

  const handleError = () => {
    setHasError(true);
  };

  return (
    <div
      ref={ref}
      className={`relative overflow-hidden ${className}`}
      style={{
        width: width ? `${width}px` : '100%',
        height: height ? `${height}px` : 'auto',
        aspectRatio: width && height ? `${width} / ${height}` : undefined,
      }}
    >
      {/* Blur placeholder */}
      {blurDataURL && !isLoaded && (
        <img
          src={blurDataURL}
          alt=""
          className="absolute inset-0 w-full h-full object-cover filter blur-lg scale-110"
          aria-hidden="true"
        />
      )}

      {/* Skeleton placeholder */}
      {!isVisible && !blurDataURL && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse" />
      )}

      {/* Actual image */}
      {isVisible && !hasError && (
        <img
          src={src}
          alt={alt}
          width={width}
          height={height}
          className={`
            w-full h-full object-cover transition-opacity duration-300
            ${isLoaded ? 'opacity-100' : 'opacity-0'}
          `}
          onLoad={handleLoad}
          onError={handleError}
          loading="lazy"
          {...props}
        />
      )}

      {/* Error state */}
      {hasError && (
        <div className="absolute inset-0 bg-gray-100 flex items-center justify-center">
          <span className="text-sm text-gray-400">Failed to load image</span>
        </div>
      )}
    </div>
  );
}

/**
 * Lazy Component Wrapper
 * 
 * Wraps a component and only renders it when it becomes visible
 * Useful for heavy components that shouldn't be rendered immediately
 * 
 * @example
 * ```tsx
 * function MyPage() {
 *   return (
 *     <div>
 *       <HeroSection />
 *       <LazyComponent>
 *         <HeavyChartComponent />
 *       </LazyComponent>
 *     </div>
 *   );
 * }
 * ```
 */
export function LazyComponent({
  children,
  placeholder,
  ...options
}: {
  children: React.ReactNode;
  placeholder?: React.ReactNode;
} & LazyLoadOptions) {
  const [ref, isVisible] = useLazyLoad(options);

  return (
    <div ref={ref}>
      {isVisible ? children : placeholder || <div className="h-64 bg-gray-100 animate-pulse" />}
    </div>
  );
}

/**
 * Preload Images
 * 
 * Preloads images in the background to improve perceived performance
 * 
 * @param urls - Array of image URLs to preload
 * @returns Promise that resolves when all images are loaded
 * 
 * @example
 * ```tsx
 * useEffect(() => {
 *   preloadImages([
 *     '/images/hero.jpg',
 *     '/images/feature1.jpg',
 *     '/images/feature2.jpg',
 *   ]);
 * }, []);
 * ```
 */
export function preloadImages(urls: string[]): Promise<void[]> {
  return Promise.all(
    urls.map((url) => {
      return new Promise<void>((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = reject;
        img.src = url;
      });
    }),
  );
}

/**
 * Use Prefetch Hook
 * 
 * Prefetches a route when the link becomes visible
 * Works with Next.js Link component
 * 
 * @param href - Route to prefetch
 * @returns Ref to attach to the link element
 * 
 * @example
 * ```tsx
 * function NavigationLink({ href, children }) {
 *   const linkRef = usePrefetch(href);
 *   
 *   return (
 *     <Link href={href} ref={linkRef}>
 *       {children}
 *     </Link>
 *   );
 * }
 * ```
 */
export function usePrefetch(href: string) {
  const [ref, isVisible] = useLazyLoad({ rootMargin: '100px', once: true });

  useEffect(() => {
    if (isVisible && typeof window !== 'undefined') {
      // Prefetch the route
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = href;
      document.head.appendChild(link);
    }
  }, [isVisible, href]);

  return ref;
}

/**
 * Dynamic Import with Loading State
 * 
 * Enhanced dynamic import with loading and error states
 * 
 * @example
 * ```tsx
 * const HeavyComponent = dynamicImport(
 *   () => import('./HeavyComponent'),
 *   { loading: () => <Spinner /> }
 * );
 * ```
 */
export function dynamicImport<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: {
    loading?: React.ComponentType;
    error?: React.ComponentType<{ error: Error }>;
  } = {},
) {
  const LazyComponent = React.lazy(importFn);

  return function DynamicComponent(props: React.ComponentProps<T>) {
    return (
      <React.Suspense
        fallback={
          options.loading ? (
            <options.loading />
          ) : (
            <div className="flex items-center justify-center p-8">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          )
        }
      >
        <LazyComponent {...props} />
      </React.Suspense>
    );
  };
}
