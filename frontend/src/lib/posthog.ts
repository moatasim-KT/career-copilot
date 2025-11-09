/**
 * PostHog Analytics Integration
 * 
 * Enterprise-grade product analytics with PostHog for user behavior tracking,
 * feature flags, session recordings, and experimentation.
 * 
 * @module lib/posthog
 */

'use client';

// Dynamic import to handle optional dependency
let posthog: any = null;

// Try to import posthog if available
if (typeof window !== 'undefined') {
    try {
        posthog = require('posthog-js');
    } catch {
        console.warn('PostHog is not installed. Analytics features will be disabled.');
    }
}

export interface PostHogConfig {
    apiKey: string;
    apiHost?: string;
    enabled?: boolean;
    capturePageviews?: boolean;
    capturePageleave?: boolean;
    autocapture?: boolean;
}

let isInitialized = false;

/**
 * Initialize PostHog
 * 
 * @example
 * ```tsx
 * initPostHog({
 *   apiKey: process.env.NEXT_PUBLIC_POSTHOG_KEY!,
 *   apiHost: process.env.NEXT_PUBLIC_POSTHOG_HOST,
 * });
 * ```
 */
export function initPostHog(config: PostHogConfig): void {
    if (!posthog) {
        console.warn('PostHog not available. Analytics disabled.');
        return;
    }

    if (isInitialized) {
        console.warn('PostHog already initialized');
        return;
    }

    if (!config.enabled && process.env.NODE_ENV !== 'production') {
        console.log('PostHog disabled in development');
        return;
    }

    if (!config.apiKey) {
        console.error('PostHog API key is required');
        return;
    }

    posthog.init(config.apiKey, {
        api_host: config.apiHost || 'https://app.posthog.com',

        // Capture settings
        capture_pageview: config.capturePageviews ?? true,
        capture_pageleave: config.capturePageleave ?? true,
        autocapture: config.autocapture ?? true,

        // Session recording
        session_recording: {
            maskAllInputs: true,
            maskTextSelector: '[data-private]',
        },

        // Privacy
        respect_dnt: true,

        // Performance
        loaded: (ph: any) => {
            if (process.env.NODE_ENV === 'development') {
                ph.debug();
            }
        },
    });

    isInitialized = true;
}

/**
 * Identify user
 * 
 * @example
 * ```tsx
 * identifyUser('user-123', {
 *   email: 'user@example.com',
 *   name: 'John Doe',
 *   plan: 'premium',
 * });
 * ```
 */
export function identifyUser(
    userId: string,
    properties?: Record<string, any>,
): void {
    if (!isInitialized) return;
    posthog.identify(userId, properties);
}

/**
 * Reset user (on logout)
 */
export function resetUser(): void {
    if (!isInitialized) return;
    posthog.reset();
}

/**
 * Track custom event
 * 
 * @example
 * ```tsx
 * trackEvent('job_application_submitted', {
 *   jobId: '123',
 *   company: 'Acme Corp',
 *   position: 'Software Engineer',
 * });
 * ```
 */
export function trackEvent(
    eventName: string,
    properties?: Record<string, any>,
): void {
    if (!isInitialized) return;
    posthog.capture(eventName, properties);
}

/**
 * Set user properties
 * 
 * @example
 * ```tsx
 * setUserProperties({
 *   totalApplications: 50,
 *   totalInterviews: 10,
 *   plan: 'premium',
 * });
 * ```
 */
export function setUserProperties(properties: Record<string, any>): void {
    if (!isInitialized) return;
    posthog.people.set(properties);
}

/**
 * Increment user property
 * 
 * @example
 * ```tsx
 * incrementProperty('applications_count', 1);
 * ```
 */
export function incrementProperty(property: string, value: number = 1): void {
    if (!isInitialized) return;
    posthog.people.increment(property, value);
}

/**
 * Check feature flag
 * 
 * @example
 * ```tsx
 * const showNewFeature = checkFeatureFlag('new-dashboard');
 * if (showNewFeature) {
 *   // Show new feature
 * }
 * ```
 */
export function checkFeatureFlag(flagKey: string): boolean {
    if (!isInitialized) return false;
    return posthog.isFeatureEnabled(flagKey) ?? false;
}

/**
 * Get feature flag payload
 * 
 * @example
 * ```tsx
 * const config = getFeatureFlagPayload('dashboard-config');
 * ```
 */
export function getFeatureFlagPayload(flagKey: string): any {
    if (!isInitialized) return null;
    return posthog.getFeatureFlagPayload(flagKey);
}

/**
 * Track page view manually
 * 
 * @example
 * ```tsx
 * trackPageView('/jobs/search', {
 *   query: 'software engineer',
 *   location: 'remote',
 * });
 * ```
 */
export function trackPageView(
    path?: string,
    properties?: Record<string, any>,
): void {
    if (!isInitialized) return;
    posthog.capture('$pageview', {
        $current_url: path || window.location.href,
        ...properties,
    });
}

/**
 * Start session recording
 */
export function startSessionRecording(): void {
    if (!isInitialized) return;
    posthog.startSessionRecording();
}

/**
 * Stop session recording
 */
export function stopSessionRecording(): void {
    if (!isInitialized) return;
    posthog.stopSessionRecording();
}

/**
 * Common event tracking helpers
 */
export const analytics = {
    // Job application events
    jobApplication: {
        viewed: (jobId: string, company: string, position: string) => {
            trackEvent('job_viewed', { jobId, company, position });
        },
        applied: (jobId: string, company: string, position: string) => {
            trackEvent('job_application_submitted', { jobId, company, position });
            incrementProperty('total_applications');
        },
        updated: (applicationId: string, status: string) => {
            trackEvent('application_updated', { applicationId, status });
        },
        deleted: (applicationId: string) => {
            trackEvent('application_deleted', { applicationId });
        },
    },

    // Interview events
    interview: {
        scheduled: (applicationId: string, date: string, type: string) => {
            trackEvent('interview_scheduled', { applicationId, date, type });
            incrementProperty('total_interviews');
        },
        completed: (applicationId: string, rating?: number) => {
            trackEvent('interview_completed', { applicationId, rating });
        },
        cancelled: (applicationId: string, reason?: string) => {
            trackEvent('interview_cancelled', { applicationId, reason });
        },
    },

    // Offer events
    offer: {
        received: (applicationId: string, salary?: number) => {
            trackEvent('offer_received', { applicationId, salary });
            incrementProperty('total_offers');
        },
        accepted: (applicationId: string) => {
            trackEvent('offer_accepted', { applicationId });
        },
        rejected: (applicationId: string, reason?: string) => {
            trackEvent('offer_rejected', { applicationId, reason });
        },
    },

    // Feature usage
    feature: {
        used: (featureName: string, details?: Record<string, any>) => {
            trackEvent('feature_used', { feature: featureName, ...details });
        },
        error: (featureName: string, error: string) => {
            trackEvent('feature_error', { feature: featureName, error });
        },
    },

    // Search events
    search: {
        performed: (query: string, filters?: Record<string, any>) => {
            trackEvent('search_performed', { query, ...filters });
        },
        resultClicked: (query: string, resultId: string, position: number) => {
            trackEvent('search_result_clicked', { query, resultId, position });
        },
    },

    // User engagement
    engagement: {
        sessionStart: () => {
            trackEvent('session_started');
        },
        sessionEnd: (duration: number) => {
            trackEvent('session_ended', { duration });
        },
        helpViewed: (topic: string) => {
            trackEvent('help_viewed', { topic });
        },
    },
};

/**
 * React hook for PostHog analytics
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const analytics = usePostHog();
 *   
 *   const handleClick = () => {
 *     analytics.trackEvent('button_clicked', { button: 'submit' });
 *   };
 * }
 * ```
 */
export function usePostHog() {
    return {
        trackEvent,
        identifyUser,
        resetUser,
        setUserProperties,
        incrementProperty,
        checkFeatureFlag,
        getFeatureFlagPayload,
        trackPageView,
        analytics,
    };
}

export { posthog };
