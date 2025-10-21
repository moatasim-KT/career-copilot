import { useState, useEffect, useCallback } from 'react'

/**
 * Progressive loading utilities for better performance
 */

// Intersection Observer for lazy loading
export class LazyLoader {
  private observer: IntersectionObserver | null = null
  private callbacks = new Map<Element, () => void>()

  constructor(options: IntersectionObserverInit = {}) {
    if (typeof window !== 'undefined' && 'IntersectionObserver' in window) {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const callback = this.callbacks.get(entry.target)
            if (callback) {
              callback()
              this.unobserve(entry.target)
            }
          }
        })
      }, {
        rootMargin: '50px',
        threshold: 0.1,
        ...options,
      })
    }
  }

  observe(element: Element, callback: () => void) {
    if (!this.observer) {
      // Fallback for browsers without IntersectionObserver
      callback()
      return
    }

    this.callbacks.set(element, callback)
    this.observer.observe(element)
  }

  unobserve(element: Element) {
    if (this.observer) {
      this.observer.unobserve(element)
      this.callbacks.delete(element)
    }
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect()
      this.callbacks.clear()
    }
  }
}

// Global lazy loader instance
export const globalLazyLoader = new LazyLoader()

/**
 * Hook for lazy loading components
 */
export function useLazyLoad<T>(
  loadFn: () => Promise<T>,
  dependencies: any[] = []
): {
  data: T | null
  loading: boolean
  error: Error | null
  load: () => void
} {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const load = useCallback(async () => {
    if (loading) return

    setLoading(true)
    setError(null)

    try {
      const result = await loadFn()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setLoading(false)
    }
  }, [loadFn, loading])

  return { data, loading, error, load }
}

/**
 * Hook for progressive image loading
 */
export function useProgressiveImage(src: string, placeholder?: string) {
  const [currentSrc, setCurrentSrc] = useState(placeholder || '')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!src) return

    const img = new Image()
    
    img.onload = () => {
      setCurrentSrc(src)
      setLoading(false)
      setError(false)
    }
    
    img.onerror = () => {
      setLoading(false)
      setError(true)
    }
    
    img.src = src
    
    return () => {
      img.onload = null
      img.onerror = null
    }
  }, [src])

  return { src: currentSrc, loading, error }
}

/**
 * Hook for intersection observer
 */
export function useIntersectionObserver(
  options: IntersectionObserverInit = {}
): [React.RefCallback<Element>, boolean] {
  const [isIntersecting, setIsIntersecting] = useState(false)
  const [element, setElement] = useState<Element | null>(null)

  const ref = useCallback((node: Element | null) => {
    setElement(node)
  }, [])

  useEffect(() => {
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting)
      },
      {
        rootMargin: '50px',
        threshold: 0.1,
        ...options,
      }
    )

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [element, options])

  return [ref, isIntersecting]
}

/**
 * Progressive loading strategies
 */
export const LoadingStrategy = {
  /**
   * Load content immediately
   */
  immediate: () => true,

  /**
   * Load content when it becomes visible
   */
  onVisible: (element: Element) => {
    return new Promise<void>((resolve) => {
      globalLazyLoader.observe(element, resolve)
    })
  },

  /**
   * Load content after a delay
   */
  delayed: (delay: number) => {
    return new Promise<void>((resolve) => {
      setTimeout(resolve, delay)
    })
  },

  /**
   * Load content when the page is idle
   */
  onIdle: () => {
    return new Promise<void>((resolve) => {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => resolve())
      } else {
        setTimeout(resolve, 100)
      }
    })
  },

  /**
   * Load content based on connection speed
   */
  adaptive: () => {
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      const connection = (navigator as any).connection
      if (connection) {
        // Load immediately on fast connections
        if (connection.effectiveType === '4g') {
          return Promise.resolve()
        }
        // Delay on slower connections
        return new Promise<void>((resolve) => {
          setTimeout(resolve, 500)
        })
      }
    }
    return Promise.resolve()
  },
}

/**
 * Resource preloader for critical assets
 */
export class ResourcePreloader {
  private preloadedResources = new Set<string>()

  preloadImage(src: string, priority: 'high' | 'low' = 'low'): Promise<void> {
    if (this.preloadedResources.has(src)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'image'
      link.href = src
      
      if (priority === 'high') {
        link.setAttribute('fetchpriority', 'high')
      }

      link.onload = () => {
        this.preloadedResources.add(src)
        resolve()
      }
      
      link.onerror = reject
      
      document.head.appendChild(link)
    })
  }

  preloadScript(src: string): Promise<void> {
    if (this.preloadedResources.has(src)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'script'
      link.href = src

      link.onload = () => {
        this.preloadedResources.add(src)
        resolve()
      }
      
      link.onerror = reject
      
      document.head.appendChild(link)
    })
  }

  preloadFont(href: string, type: string = 'font/woff2'): Promise<void> {
    if (this.preloadedResources.has(href)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'font'
      link.type = type
      link.href = href
      link.crossOrigin = 'anonymous'

      link.onload = () => {
        this.preloadedResources.add(href)
        resolve()
      }
      
      link.onerror = reject
      
      document.head.appendChild(link)
    })
  }
}

export const resourcePreloader = new ResourcePreloader()

/**
 * Performance monitoring utilities
 */
export class PerformanceMonitor {
  private metrics = new Map<string, number>()

  startTiming(name: string) {
    this.metrics.set(`${name}_start`, performance.now())
  }

  endTiming(name: string): number {
    const startTime = this.metrics.get(`${name}_start`)
    if (!startTime) return 0

    const duration = performance.now() - startTime
    this.metrics.set(name, duration)
    return duration
  }

  getTiming(name: string): number {
    return this.metrics.get(name) || 0
  }

  getAllTimings(): Record<string, number> {
    const timings: Record<string, number> = {}
    this.metrics.forEach((value, key) => {
      if (!key.endsWith('_start')) {
        timings[key] = value
      }
    })
    return timings
  }

  measureLCP(): Promise<number> {
    return new Promise((resolve) => {
      if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const lastEntry = entries[entries.length - 1]
          resolve(lastEntry.startTime)
          observer.disconnect()
        })
        
        observer.observe({ entryTypes: ['largest-contentful-paint'] })
        
        // Fallback timeout
        setTimeout(() => {
          observer.disconnect()
          resolve(0)
        }, 10000)
      } else {
        resolve(0)
      }
    })
  }

  measureFID(): Promise<number> {
    return new Promise((resolve) => {
      if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const firstEntry = entries[0]
          resolve(firstEntry.processingStart - firstEntry.startTime)
          observer.disconnect()
        })
        
        observer.observe({ entryTypes: ['first-input'] })
        
        // Fallback timeout
        setTimeout(() => {
          observer.disconnect()
          resolve(0)
        }, 10000)
      } else {
        resolve(0)
      }
    })
  }

  measureCLS(): Promise<number> {
    return new Promise((resolve) => {
      if ('PerformanceObserver' in window) {
        let clsValue = 0
        
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value
            }
          }
        })
        
        observer.observe({ entryTypes: ['layout-shift'] })
        
        // Measure for 5 seconds
        setTimeout(() => {
          observer.disconnect()
          resolve(clsValue)
        }, 5000)
      } else {
        resolve(0)
      }
    })
  }
}

export const performanceMonitor = new PerformanceMonitor()

/**
 * Bundle splitting utilities
 */
export const dynamicImport = {
  /**
   * Dynamically import a component with loading state
   */
  component: <T extends React.ComponentType<any>>(
    importFn: () => Promise<{ default: T }>,
    fallback?: React.ComponentType
  ) => {
    return React.lazy(async () => {
      try {
        const module = await importFn()
        return { default: module.default }
      } catch (error) {
        console.error('Dynamic import failed:', error)
        if (fallback) {
          return { default: fallback }
        }
        throw error
      }
    })
  },

  /**
   * Preload a dynamic import
   */
  preload: (importFn: () => Promise<any>) => {
    // Start loading but don't wait for it
    importFn().catch(console.error)
  },
}

// React import for lazy loading
import React from 'react'