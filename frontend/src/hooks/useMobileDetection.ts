/**
 * Mobile Detection Hook
 * 
 * Enterprise-grade mobile device detection and viewport management
 * Handles responsive breakpoints, touch detection, and device capabilities
 * 
 * @module hooks/useMobileDetection
 */

'use client';

import { useState, useEffect } from 'react';

export interface DeviceInfo {
    /** Whether the device is mobile (width < 768px) */
    isMobile: boolean;
    /** Whether the device is tablet (width >= 768px and < 1024px) */
    isTablet: boolean;
    /** Whether the device is desktop (width >= 1024px) */
    isDesktop: boolean;
    /** Whether the device supports touch */
    isTouch: boolean;
    /** Current viewport width */
    width: number;
    /** Current viewport height */
    height: number;
    /** Device pixel ratio for high-DPI screens */
    pixelRatio: number;
    /** Whether device is in portrait orientation */
    isPortrait: boolean;
    /** Whether device is in landscape orientation */
    isLandscape: boolean;
    /** Detected device type */
    deviceType: 'mobile' | 'tablet' | 'desktop';
}

/**
 * Breakpoint constants following Material Design guidelines
 */
export const BREAKPOINTS = {
    mobile: 768,
    tablet: 1024,
    desktop: 1280,
    wide: 1920,
} as const;

/**
 * Detects if the device supports touch
 */
const hasTouch = (): boolean => {
    if (typeof window === 'undefined') return false;

    return (
        'ontouchstart' in window ||
        navigator.maxTouchPoints > 0 ||
        (window.matchMedia && window.matchMedia('(pointer: coarse)').matches)
    );
};

/**
 * Mobile Detection Hook
 * 
 * @returns {DeviceInfo} Device information and capabilities
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isMobile, isTouch, deviceType } = useMobileDetection();
 * 
 *   return (
 *     <div className={isMobile ? 'mobile-layout' : 'desktop-layout'}>
 *       {isTouch ? <TouchInterface /> : <MouseInterface />}
 *     </div>
 *   );
 * }
 * ```
 */
export function useMobileDetection(): DeviceInfo {
    const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>(() => {
        // Server-side rendering defaults
        if (typeof window === 'undefined') {
            return {
                isMobile: false,
                isTablet: false,
                isDesktop: true,
                isTouch: false,
                width: 1024,
                height: 768,
                pixelRatio: 1,
                isPortrait: false,
                isLandscape: true,
                deviceType: 'desktop',
            };
        }

        const width = window.innerWidth;
        const height = window.innerHeight;
        const isPortrait = height > width;

        return {
            isMobile: width < BREAKPOINTS.mobile,
            isTablet: width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet,
            isDesktop: width >= BREAKPOINTS.tablet,
            isTouch: hasTouch(),
            width,
            height,
            pixelRatio: window.devicePixelRatio || 1,
            isPortrait,
            isLandscape: !isPortrait,
            deviceType: width < BREAKPOINTS.mobile ? 'mobile' : width < BREAKPOINTS.tablet ? 'tablet' : 'desktop',
        };
    });

    useEffect(() => {
        const updateDeviceInfo = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const isPortrait = height > width;

            setDeviceInfo({
                isMobile: width < BREAKPOINTS.mobile,
                isTablet: width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet,
                isDesktop: width >= BREAKPOINTS.tablet,
                isTouch: hasTouch(),
                width,
                height,
                pixelRatio: window.devicePixelRatio || 1,
                isPortrait,
                isLandscape: !isPortrait,
                deviceType: width < BREAKPOINTS.mobile ? 'mobile' : width < BREAKPOINTS.tablet ? 'tablet' : 'desktop',
            });
        };

        // Debounce resize events for performance
        let timeoutId: NodeJS.Timeout;
        const debouncedUpdate = () => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(updateDeviceInfo, 150);
        };

        window.addEventListener('resize', debouncedUpdate);
        window.addEventListener('orientationchange', updateDeviceInfo);

        return () => {
            clearTimeout(timeoutId);
            window.removeEventListener('resize', debouncedUpdate);
            window.removeEventListener('orientationchange', updateDeviceInfo);
        };
    }, []);

    return deviceInfo;
}

/**
 * Hook to match specific media queries
 * 
 * @param query - CSS media query string
 * @returns boolean indicating if the query matches
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
 *   const isLandscape = useMediaQuery('(orientation: landscape)');
 *   
 *   return <div className={prefersDark ? 'dark' : 'light'}>...</div>;
 * }
 * ```
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(() => {
        if (typeof window === 'undefined') return false;
        return window.matchMedia(query).matches;
    });

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const mediaQuery = window.matchMedia(query);
        const handler = (event: MediaQueryListEvent) => setMatches(event.matches);

        // Modern browsers
        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', handler);
            return () => mediaQuery.removeEventListener('change', handler);
        }
        // Legacy browsers
        else {
            mediaQuery.addListener(handler);
            return () => mediaQuery.removeListener(handler);
        }
    }, [query]);

    return matches;
}
