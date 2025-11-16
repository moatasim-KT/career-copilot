/**
 * Performance Monitoring and Core Web Vitals
 * 
 * Enterprise-grade performance monitoring with Core Web Vitals tracking,
 * real user monitoring (RUM), and performance budgets.
 * 
 * @module lib/performance
 */

'use client';

import { useEffect } from 'react';

import { logger } from '@/lib/logger';

export interface PerformanceMetric {
    name: string;
    value: number;
    rating: 'good' | 'needs-improvement' | 'poor';
    timestamp: number;
}

export interface CoreWebVitals {
    LCP?: PerformanceMetric; // Largest Contentful Paint
    FID?: PerformanceMetric; // First Input Delay
    CLS?: PerformanceMetric; // Cumulative Layout Shift
    FCP?: PerformanceMetric; // First Contentful Paint
    TTFB?: PerformanceMetric; // Time to First Byte
    INP?: PerformanceMetric; // Interaction to Next Paint
}

/**
 * Performance thresholds (in milliseconds or score)
 */
const THRESHOLDS = {
    LCP: { good: 2500, poor: 4000 },
    FID: { good: 100, poor: 300 },
    CLS: { good: 0.1, poor: 0.25 },
    FCP: { good: 1800, poor: 3000 },
    TTFB: { good: 800, poor: 1800 },
    INP: { good: 200, poor: 500 },
};

/**
 * Get metric rating based on value
 */
function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
    const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS];
    if (!threshold) return 'good';

    if (value <= threshold.good) return 'good';
    if (value <= threshold.poor) return 'needs-improvement';
    return 'poor';
}

/**
 * Report metric to analytics
 */
function reportMetric(metric: PerformanceMetric): void {
    // Send to your analytics service
    if (typeof window !== 'undefined') {
        // Google Analytics 4
        if (window.gtag) {
            window.gtag('event', metric.name, {
                value: Math.round(metric.value),
                metric_rating: metric.rating,
                metric_value: metric.value,
            });
        }

        // PostHog
        if (window.posthog) {
            window.posthog.capture('performance_metric', {
                metric_name: metric.name,
                metric_value: metric.value,
                metric_rating: metric.rating,
            });
        }

        // Sentry
        if (window.Sentry) {
            window.Sentry.captureMessage(`Performance: ${metric.name}`, {
                level: metric.rating === 'poor' ? 'warning' : 'info',
                tags: {
                    metric_name: metric.name,
                    metric_rating: metric.rating,
                },
                extra: {
                    metric_value: metric.value,
                },
            });
        }

        // Custom endpoint
        if (process.env.NEXT_PUBLIC_PERFORMANCE_ENDPOINT) {
            fetch(process.env.NEXT_PUBLIC_PERFORMANCE_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(metric),
            }).catch(console.error);
        }

        logger.info(`[Performance] ${metric.name}:`, {
            value: metric.value,
            rating: metric.rating,
        });
    }
}

/**
 * Measure Largest Contentful Paint (LCP)
 */
function measureLCP(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    try {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1] as any;

            if (lastEntry) {
                const value = lastEntry.renderTime || lastEntry.loadTime;
                reportMetric({
                    name: 'LCP',
                    value,
                    rating: getRating('LCP', value),
                    timestamp: Date.now(),
                });
            }
        });

        observer.observe({ type: 'largest-contentful-paint', buffered: true });
    } catch (error) {
        logger.error('Error measuring LCP:', error);
    }
}

/**
 * Measure First Input Delay (FID)
 */
function measureFID(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    try {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach((entry: any) => {
                const value = entry.processingStart - entry.startTime;
                reportMetric({
                    name: 'FID',
                    value,
                    rating: getRating('FID', value),
                    timestamp: Date.now(),
                });
            });
        });

        observer.observe({ type: 'first-input', buffered: true });
    } catch (error) {
        logger.error('Error measuring FID:', error);
    }
}

/**
 * Measure Cumulative Layout Shift (CLS)
 */
function measureCLS(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    try {
        let clsValue = 0;
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach((entry: any) => {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            });
        });

        observer.observe({ type: 'layout-shift', buffered: true });

        // Report CLS on page unload
        window.addEventListener('beforeunload', () => {
            reportMetric({
                name: 'CLS',
                value: clsValue,
                rating: getRating('CLS', clsValue),
                timestamp: Date.now(),
            });
        });
    } catch (error) {
        logger.error('Error measuring CLS:', error);
    }
}

/**
 * Measure First Contentful Paint (FCP)
 */
function measureFCP(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    try {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach((entry) => {
                if (entry.name === 'first-contentful-paint') {
                    reportMetric({
                        name: 'FCP',
                        value: entry.startTime,
                        rating: getRating('FCP', entry.startTime),
                        timestamp: Date.now(),
                    });
                }
            });
        });

        observer.observe({ type: 'paint', buffered: true });
    } catch (error) {
        logger.error('Error measuring FCP:', error);
    }
}

/**
 * Measure Time to First Byte (TTFB)
 */
function measureTTFB(): void {
    if (typeof window === 'undefined') return;

    try {
        const navigationTiming = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

        if (navigationTiming) {
            const value = navigationTiming.responseStart - navigationTiming.requestStart;
            reportMetric({
                name: 'TTFB',
                value,
                rating: getRating('TTFB', value),
                timestamp: Date.now(),
            });
        }
    } catch (error) {
        logger.error('Error measuring TTFB:', error);
    }
}

/**
 * Measure Interaction to Next Paint (INP)
 */
function measureINP(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    try {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            let maxDuration = 0;

            entries.forEach((entry: any) => {
                if (entry.duration > maxDuration) {
                    maxDuration = entry.duration;
                }
            });

            if (maxDuration > 0) {
                reportMetric({
                    name: 'INP',
                    value: maxDuration,
                    rating: getRating('INP', maxDuration),
                    timestamp: Date.now(),
                });
            }
        });

        observer.observe({ type: 'event', buffered: true });
    } catch (error) {
        logger.error('Error measuring INP:', error);
    }
}

/**
 * Initialize performance monitoring
 */
export function initPerformanceMonitoring(): void {
    if (typeof window === 'undefined') return;

    measureLCP();
    measureFID();
    measureCLS();
    measureFCP();
    measureTTFB();
    measureINP();
}

/**
 * usePerformanceMonitoring Hook
 * 
 * Initialize performance monitoring on component mount
 * 
 * @example
 * ```tsx
 * function App() {
 *   usePerformanceMonitoring();
 *   return <YourApp />;
 * }
 * ```
 */
export function usePerformanceMonitoring(): void {
    useEffect(() => {
        initPerformanceMonitoring();
    }, []);
}

/**
 * Get current performance metrics
 */
export function getPerformanceMetrics(): CoreWebVitals {
    const metrics: CoreWebVitals = {};

    if (typeof window === 'undefined') return metrics;

    try {
        // Get LCP
        const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
        if (lcpEntries.length > 0) {
            const lastEntry = lcpEntries[lcpEntries.length - 1] as any;
            const value = lastEntry.renderTime || lastEntry.loadTime;
            metrics.LCP = {
                name: 'LCP',
                value,
                rating: getRating('LCP', value),
                timestamp: Date.now(),
            };
        }

        // Get FCP
        const paintEntries = performance.getEntriesByType('paint');
        const fcpEntry = paintEntries.find((entry) => entry.name === 'first-contentful-paint');
        if (fcpEntry) {
            metrics.FCP = {
                name: 'FCP',
                value: fcpEntry.startTime,
                rating: getRating('FCP', fcpEntry.startTime),
                timestamp: Date.now(),
            };
        }

        // Get TTFB
        const navigationTiming = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigationTiming) {
            const value = navigationTiming.responseStart - navigationTiming.requestStart;
            metrics.TTFB = {
                name: 'TTFB',
                value,
                rating: getRating('TTFB', value),
                timestamp: Date.now(),
            };
        }
    } catch (error) {
        logger.error('Error getting performance metrics:', error);
    }

    return metrics;
}

/**
 * Performance budget checker
 */
export function checkPerformanceBudget(): {
    passed: boolean;
    failures: string[];
} {
    const metrics = getPerformanceMetrics();
    const failures: string[] = [];

    if (metrics.LCP && metrics.LCP.rating === 'poor') {
        failures.push(`LCP: ${metrics.LCP.value.toFixed(0)}ms (budget: ${THRESHOLDS.LCP.poor}ms)`);
    }

    if (metrics.FCP && metrics.FCP.rating === 'poor') {
        failures.push(`FCP: ${metrics.FCP.value.toFixed(0)}ms (budget: ${THRESHOLDS.FCP.poor}ms)`);
    }

    if (metrics.TTFB && metrics.TTFB.rating === 'poor') {
        failures.push(`TTFB: ${metrics.TTFB.value.toFixed(0)}ms (budget: ${THRESHOLDS.TTFB.poor}ms)`);
    }

    return {
        passed: failures.length === 0,
        failures,
    };
}

// Type declarations for global analytics
declare global {
    interface Window {
        gtag?: (...args: any[]) => void;
        posthog?: {
            capture: (event: string, properties?: any) => void;
        };
        Sentry?: {
            captureMessage: (message: string, options?: any) => void;
        };
    }
}
