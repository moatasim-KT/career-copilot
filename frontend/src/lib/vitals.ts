/**
 * Web Vitals Reporting
 * 
 * This module provides utilities for tracking and reporting Core Web Vitals metrics.
 * Core Web Vitals are a set of metrics that measure real-world user experience:
 * 
 * - FCP (First Contentful Paint): Time until first content is rendered
 * - LCP (Largest Contentful Paint): Time until largest content element is rendered
 * - INP (Interaction to Next Paint): Responsiveness - time from interaction to next paint
 * - CLS (Cumulative Layout Shift): Visual stability - measures unexpected layout shifts
 * - TTFB (Time to First Byte): Time from navigation to first byte received
 * 
 * Note: FID (First Input Delay) has been deprecated and replaced by INP.
 * 
 * @see https://web.dev/vitals/
 */

import { onCLS, onFCP, onINP, onLCP, onTTFB } from 'web-vitals';
import type { Metric } from 'web-vitals';

import { logger } from '@/lib/logger';

/**
 * Web Vitals metric thresholds
 * Based on Google's recommendations for good user experience
 */
export const VITALS_THRESHOLDS = {
  FCP: {
    good: 1800, // 1.8s
    needsImprovement: 3000, // 3s
  },
  LCP: {
    good: 2500, // 2.5s
    needsImprovement: 4000, // 4s
  },
  INP: {
    good: 200, // 200ms
    needsImprovement: 500, // 500ms
  },
  CLS: {
    good: 0.1,
    needsImprovement: 0.25,
  },
  TTFB: {
    good: 800, // 800ms
    needsImprovement: 1800, // 1.8s
  },
} as const;

/**
 * Rating for a metric based on thresholds
 */
export type MetricRating = 'good' | 'needs-improvement' | 'poor';

/**
 * Get the rating for a metric value
 */
export function getMetricRating(
  name: Metric['name'],
  value: number,
): MetricRating {
  const thresholds = VITALS_THRESHOLDS[name as keyof typeof VITALS_THRESHOLDS];
  
  if (!thresholds) {
    return 'good';
  }
  
  if (value <= thresholds.good) {
    return 'good';
  }
  
  if (value <= thresholds.needsImprovement) {
    return 'needs-improvement';
  }
  
  return 'poor';
}

/**
 * Format metric value for display
 */
export function formatMetricValue(name: Metric['name'], value: number): string {
  // CLS is unitless
  if (name === 'CLS') {
    return value.toFixed(3);
  }
  
  // All other metrics are in milliseconds
  if (value < 1000) {
    return `${Math.round(value)}ms`;
  }
  
  return `${(value / 1000).toFixed(2)}s`;
}

/**
 * Enhanced metric with additional context
 */
export interface EnhancedMetric extends Metric {
  rating: MetricRating;
  formattedValue: string;
  url: string;
  timestamp: number;
}

/**
 * Enhance a metric with additional context
 */
function enhanceMetric(metric: Metric): EnhancedMetric {
  return {
    ...metric,
    rating: getMetricRating(metric.name, metric.value),
    formattedValue: formatMetricValue(metric.name, metric.value),
    url: window.location.href,
    timestamp: Date.now(),
  };
}

/**
 * Analytics provider interface
 * Implement this interface to send metrics to your analytics service
 */
export interface AnalyticsProvider {
  trackMetric: (metric: EnhancedMetric) => void;
}

/**
 * Console analytics provider (default)
 * Logs metrics to the console for development
 */
export class ConsoleAnalyticsProvider implements AnalyticsProvider {
  trackMetric(metric: EnhancedMetric): void {
    const emoji = {
      good: '✅',
      'needs-improvement': '⚠️',
      poor: '❌',
    }[metric.rating];
    
    logger.info(
      `${emoji} Web Vitals: ${metric.name}`,
      {
        value: metric.formattedValue,
        rating: metric.rating,
        id: metric.id,
        navigationType: metric.navigationType,
        url: metric.url,
      },
    );
  }
}

/**
 * Google Analytics provider
 * Sends metrics to Google Analytics 4
 */
export class GoogleAnalyticsProvider implements AnalyticsProvider {
  trackMetric(metric: EnhancedMetric): void {
    // Check if gtag is available
    if (typeof window !== 'undefined' && 'gtag' in window) {
      const gtag = (window as any).gtag;
      
      gtag('event', metric.name, {
        event_category: 'Web Vitals',
        event_label: metric.id,
        value: Math.round(metric.value),
        metric_rating: metric.rating,
        metric_delta: Math.round(metric.delta),
        metric_navigation_type: metric.navigationType,
        non_interaction: true,
      });
    }
  }
}

/**
 * Custom API provider
 * Sends metrics to a custom analytics endpoint
 */
export class CustomAPIProvider implements AnalyticsProvider {
  constructor(private endpoint: string) {}
  
  trackMetric(metric: EnhancedMetric): void {
    // Send to custom endpoint
    // Using sendBeacon for reliability (works even if page is unloading)
    if (typeof navigator !== 'undefined' && 'sendBeacon' in navigator) {
      const data = JSON.stringify({
        metric: metric.name,
        value: metric.value,
        rating: metric.rating,
        id: metric.id,
        navigationType: metric.navigationType,
        url: metric.url,
        timestamp: metric.timestamp,
        userAgent: navigator.userAgent,
      });
      
      navigator.sendBeacon(this.endpoint, data);
    } else {
      // Fallback to fetch
      fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(metric),
        keepalive: true,
      }).catch((error) => {
        logger.error('Failed to send Web Vitals metric:', error);
      });
    }
  }
}

/**
 * Composite provider
 * Sends metrics to multiple providers
 */
export class CompositeAnalyticsProvider implements AnalyticsProvider {
  constructor(private providers: AnalyticsProvider[]) {}
  
  trackMetric(metric: EnhancedMetric): void {
    this.providers.forEach((provider) => {
      try {
        provider.trackMetric(metric);
      } catch (error) {
        logger.error('Error tracking metric with provider:', error);
      }
    });
  }
}

/**
 * Global analytics provider instance
 */
let analyticsProvider: AnalyticsProvider = new ConsoleAnalyticsProvider();

/**
 * Set the analytics provider
 * Call this early in your application to configure where metrics are sent
 * 
 * @example
 * ```ts
 * // Use Google Analytics
 * setAnalyticsProvider(new GoogleAnalyticsProvider());
 * 
 * // Use custom API
 * setAnalyticsProvider(new CustomAPIProvider('/api/analytics/vitals'));
 * 
 * // Use multiple providers
 * setAnalyticsProvider(new CompositeAnalyticsProvider([
 *   new ConsoleAnalyticsProvider(),
 *   new GoogleAnalyticsProvider(),
 *   new CustomAPIProvider('/api/analytics/vitals'),
 * ]));
 * ```
 */
export function setAnalyticsProvider(provider: AnalyticsProvider): void {
  analyticsProvider = provider;
}

/**
 * Report a Web Vitals metric
 * This is the main function called by the web-vitals library
 */
function reportMetric(metric: Metric): void {
  const enhanced = enhanceMetric(metric);
  analyticsProvider.trackMetric(enhanced);
}

/**
 * Initialize Web Vitals tracking
 * Call this once in your application to start tracking all Core Web Vitals
 * 
 * @example
 * ```ts
 * // In your app layout or entry point
 * import { initWebVitals } from '@/lib/vitals';
 * 
 * initWebVitals();
 * ```
 */
export function initWebVitals(): void {
  // Only run in browser
  if (typeof window === 'undefined') {
    return;
  }
  
  // Track all Core Web Vitals
  onCLS(reportMetric);
  onFCP(reportMetric);
  onINP(reportMetric);
  onLCP(reportMetric);
  onTTFB(reportMetric);
}

/**
 * Report Web Vitals for Next.js
 * Use this in your _app.tsx or app/layout.tsx
 * 
 * @example
 * ```tsx
 * // In app/layout.tsx
 * export function reportWebVitals(metric: NextWebVitalsMetric) {
 *   reportNextWebVitals(metric);
 * }
 * ```
 */
export function reportWebVitals(metric: Metric): void {
  reportMetric(metric);
}

/**
 * Get current Web Vitals snapshot
 * Useful for debugging or displaying metrics in the UI
 */
export async function getWebVitalsSnapshot(): Promise<Record<string, EnhancedMetric | null>> {
  return new Promise((resolve) => {
    const metrics: Record<string, EnhancedMetric | null> = {
      CLS: null,
      FCP: null,
      INP: null,
      LCP: null,
      TTFB: null,
    };
    
    let collected = 0;
    const total = 5;
    
    const checkComplete = () => {
      collected++;
      if (collected === total) {
        resolve(metrics);
      }
    };
    
    onCLS((metric) => {
      metrics.CLS = enhanceMetric(metric);
      checkComplete();
    });
    
    onFCP((metric) => {
      metrics.FCP = enhanceMetric(metric);
      checkComplete();
    });
    
    onINP((metric) => {
      metrics.INP = enhanceMetric(metric);
      checkComplete();
    });
    
    onLCP((metric) => {
      metrics.LCP = enhanceMetric(metric);
      checkComplete();
    });
    
    onTTFB((metric) => {
      metrics.TTFB = enhanceMetric(metric);
      checkComplete();
    });
    
    // Timeout after 5 seconds
    setTimeout(() => {
      resolve(metrics);
    }, 5000);
  });
}

/**
 * Export types for external use
 */
export type { Metric } from 'web-vitals';
