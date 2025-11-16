/**
 * Service Worker Registration
 * 
 * Enterprise-grade service worker setup for Progressive Web App (PWA) capabilities
 * Provides offline support, caching strategies, and background sync
 * 
 * @module lib/serviceWorker
 */

/**
 * Service Worker Configuration
 */
export const SW_CONFIG = {
    /** Cache name for static assets */
    CACHE_NAME: 'career-copilot-v1',
    /** Cache name for API responses */
    API_CACHE_NAME: 'career-copilot-api-v1',
    /** Cache name for images */
    IMAGE_CACHE_NAME: 'career-copilot-images-v1',
    /** URLs to precache on service worker installation */
    PRECACHE_URLS: [
        '/',
        '/dashboard',
        '/jobs',
        '/applications',
        '/offline',
    ],
    /** Max age for cached API responses (in seconds) */
    API_CACHE_MAX_AGE: 5 * 60, // 5 minutes
    /** Max number of cached images */
    MAX_CACHED_IMAGES: 50,
} as const;

/**
 * Register the service worker
 * 
 * Only registers in production and when service workers are supported
 * 
 * @returns Promise<ServiceWorkerRegistration | undefined>
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | undefined> {
    // Only register in production
    if (process.env.NODE_ENV !== 'production') {
        logger.info('[SW] Service worker not registered in development');
        return undefined;
    }

    // Check if service workers are supported
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
        logger.warn('[SW] Service workers are not supported');
        return undefined;
    }

    try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/',
        });

        logger.info('[SW] Service worker registered successfully:', registration.scope);

        // Check for updates periodically
        setInterval(() => {
            registration.update();
        }, 60 * 60 * 1000); // Check every hour

        // Handle service worker updates
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;

            if (newWorker) {
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // New service worker available, notify user
                        notifyUserOfUpdate();
                    }
                });
            }
        });

        return registration;
    } catch (error) {
        logger.error('[SW] Service worker registration failed:', error);
        return undefined;
    }
}

/**
 * Unregister the service worker
 * 
 * Useful for development or troubleshooting
 */
export async function unregisterServiceWorker(): Promise<boolean> {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
        return false;
    }

    try {
        const registration = await navigator.serviceWorker.ready;
        const unregistered = await registration.unregister();

        if (unregistered) {
            logger.info('[SW] Service worker unregistered successfully');
        }

        return unregistered;
    } catch (error) {
        logger.error('[SW] Service worker unregistration failed:', error);
        return false;
    }
}

/**
 * Notify user of available update
 * 
 * Shows a toast/notification when a new version is available
 */
function notifyUserOfUpdate() {
    // Check if we have a toast notification system available
    if (typeof window !== 'undefined') {
        // Create a custom event for the app to listen to
        const event = new CustomEvent('swUpdate', {
            detail: {
                message: 'A new version is available. Reload to update.',
                action: () => {
                    window.location.reload();
                },
            },
        });

        window.dispatchEvent(event);
    }
}

/**
 * Check if app is running in standalone mode (installed PWA)
 */
export function isStandalone(): boolean {
    if (typeof window === 'undefined') return false;

    return (
        window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as any).standalone === true ||
        document.referrer.includes('android-app://')
    );
}

/**
 * Check if service worker is supported
 */
export function isServiceWorkerSupported(): boolean {
    return typeof window !== 'undefined' && 'serviceWorker' in navigator;
}

/**
 * Check if the app is online
 */
export function useOnlineStatus() {
    const [isOnline, setIsOnline] = React.useState(
        typeof window !== 'undefined' && typeof navigator !== 'undefined' ? navigator.onLine : true,
    );

    React.useEffect(() => {
        if (typeof window === 'undefined') return;

        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    return isOnline;
}

// Note: This file should be imported in the app's root layout or _app file
// Example usage:
// useEffect(() => {
//   registerServiceWorker();
// }, []);

import React from 'react';

import { logger } from '@/lib/logger';
