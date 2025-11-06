/**
 * Tests for Mobile Detection Hook
 * 
 * @module hooks/__tests__/useMobileDetection.test.ts
 */

import { renderHook, act } from '@testing-library/react';

import { useMobileDetection, useMediaQuery, BREAKPOINTS } from '../useMobileDetection';

// Mock window.matchMedia
const createMatchMedia = (matches: boolean) => {
    return (query: string) => ({
        matches,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    });
};

describe('useMobileDetection', () => {
    beforeEach(() => {
        // Reset window size
        Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: 1024,
        });
        Object.defineProperty(window, 'innerHeight', {
            writable: true,
            configurable: true,
            value: 768,
        });
        Object.defineProperty(window, 'devicePixelRatio', {
            writable: true,
            configurable: true,
            value: 1,
        });
    });

    describe('Device Type Detection', () => {
        it('should detect mobile devices correctly', () => {
            window.innerWidth = 375;
            window.innerHeight = 812;

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isMobile).toBe(true);
            expect(result.current.isTablet).toBe(false);
            expect(result.current.isDesktop).toBe(false);
            expect(result.current.deviceType).toBe('mobile');
        });

        it('should detect tablet devices correctly', () => {
            window.innerWidth = 768;
            window.innerHeight = 1024;

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isMobile).toBe(false);
            expect(result.current.isTablet).toBe(true);
            expect(result.current.isDesktop).toBe(false);
            expect(result.current.deviceType).toBe('tablet');
        });

        it('should detect desktop devices correctly', () => {
            window.innerWidth = 1920;
            window.innerHeight = 1080;

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isMobile).toBe(false);
            expect(result.current.isTablet).toBe(false);
            expect(result.current.isDesktop).toBe(true);
            expect(result.current.deviceType).toBe('desktop');
        });
    });

    describe('Touch Detection', () => {
        it('should detect touch support when ontouchstart exists', () => {
            // Mock touch support
            Object.defineProperty(window, 'ontouchstart', {
                writable: true,
                configurable: true,
                value: () => { },
            });

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isTouch).toBe(true);
        });

        it('should detect touch support when maxTouchPoints > 0', () => {
            Object.defineProperty(navigator, 'maxTouchPoints', {
                writable: true,
                configurable: true,
                value: 5,
            });

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isTouch).toBe(true);
        });
    });

    describe('Orientation Detection', () => {
        it('should detect portrait orientation', () => {
            window.innerWidth = 375;
            window.innerHeight = 812;

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isPortrait).toBe(true);
            expect(result.current.isLandscape).toBe(false);
        });

        it('should detect landscape orientation', () => {
            window.innerWidth = 812;
            window.innerHeight = 375;

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isPortrait).toBe(false);
            expect(result.current.isLandscape).toBe(true);
        });
    });

    describe('Responsive Updates', () => {
        it('should update on window resize', async () => {
            window.innerWidth = 1920;
            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.isDesktop).toBe(true);

            // Simulate resize
            act(() => {
                window.innerWidth = 375;
                window.dispatchEvent(new Event('resize'));
            });

            // Wait for debounce
            await new Promise((resolve) => setTimeout(resolve, 200));

            expect(result.current.isMobile).toBe(true);
        });

        it('should update on orientation change', () => {
            const { result } = renderHook(() => useMobileDetection());
            const initialOrientation = result.current.isPortrait;

            act(() => {
                const temp = window.innerWidth;
                window.innerWidth = window.innerHeight;
                window.innerHeight = temp;
                window.dispatchEvent(new Event('orientationchange'));
            });

            expect(result.current.isPortrait).toBe(!initialOrientation);
        });
    });

    describe('Pixel Ratio', () => {
        it('should return correct pixel ratio', () => {
            window.devicePixelRatio = 2;

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.pixelRatio).toBe(2);
        });

        it('should default to 1 if pixel ratio not available', () => {
            delete (window as any).devicePixelRatio;

            const { result } = renderHook(() => useMobileDetection());

            expect(result.current.pixelRatio).toBe(1);
        });
    });

    describe('Breakpoints', () => {
        it('should have correct breakpoint values', () => {
            expect(BREAKPOINTS.mobile).toBe(768);
            expect(BREAKPOINTS.tablet).toBe(1024);
            expect(BREAKPOINTS.desktop).toBe(1280);
            expect(BREAKPOINTS.wide).toBe(1920);
        });
    });
});

describe('useMediaQuery', () => {
    beforeEach(() => {
        window.matchMedia = createMatchMedia(false);
    });

    it('should return true when media query matches', () => {
        window.matchMedia = createMatchMedia(true);

        const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'));

        expect(result.current).toBe(true);
    });

    it('should return false when media query does not match', () => {
        window.matchMedia = createMatchMedia(false);

        const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'));

        expect(result.current).toBe(false);
    });

    it('should update when media query changes', () => {
        let matches = false;
        const listeners: ((e: MediaQueryListEvent) => void)[] = [];

        window.matchMedia = (query: string) => ({
            matches,
            media: query,
            onchange: null,
            addListener: jest.fn(),
            removeListener: jest.fn(),
            addEventListener: jest.fn((event, handler) => {
                if (event === 'change') listeners.push(handler);
            }),
            removeEventListener: jest.fn(),
            dispatchEvent: jest.fn(),
        });

        const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'));

        expect(result.current).toBe(false);

        // Simulate media query change
        act(() => {
            matches = true;
            listeners.forEach((listener) =>
                listener({ matches: true, media: '(min-width: 768px)' } as MediaQueryListEvent),
            );
        });

        expect(result.current).toBe(true);
    });

    it('should handle dark mode preference', () => {
        window.matchMedia = createMatchMedia(true);

        const { result } = renderHook(() => useMediaQuery('(prefers-color-scheme: dark)'));

        expect(result.current).toBe(true);
    });
});
