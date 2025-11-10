/**
 * Tests for useRoutePrefetch hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';

import { useRoutePrefetch, usePrefetchRoutes } from '../useRoutePrefetch';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

describe('useRoutePrefetch', () => {
  let mockRouter: { prefetch: jest.Mock };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    mockRouter = {
      prefetch: jest.fn(),
    };
    
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('useRoutePrefetch', () => {
    it('should prefetch route on mouse enter after delay', async () => {
      const { result } = renderHook(() => useRoutePrefetch('/dashboard'));

      act(() => {
        result.current.onMouseEnter();
      });

      // Should not prefetch immediately
      expect(mockRouter.prefetch).not.toHaveBeenCalled();

      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(50);
      });

      // Should prefetch after delay
      expect(mockRouter.prefetch).toHaveBeenCalledWith('/dashboard');
      expect(mockRouter.prefetch).toHaveBeenCalledTimes(1);
    });

    it('should cancel prefetch if mouse leaves before delay', () => {
      const { result } = renderHook(() => useRoutePrefetch('/dashboard'));

      act(() => {
        result.current.onMouseEnter();
      });

      // Leave before delay completes
      act(() => {
        jest.advanceTimersByTime(25);
        result.current.onMouseLeave();
        jest.advanceTimersByTime(50);
      });

      // Should not prefetch
      expect(mockRouter.prefetch).not.toHaveBeenCalled();
    });

    it('should prefetch immediately on touch start', () => {
      const { result } = renderHook(() => useRoutePrefetch('/dashboard'));

      act(() => {
        result.current.onTouchStart();
      });

      // Should prefetch immediately without delay
      expect(mockRouter.prefetch).toHaveBeenCalledWith('/dashboard');
    });

    it('should only prefetch once', () => {
      const { result } = renderHook(() => useRoutePrefetch('/dashboard'));

      // Trigger multiple times
      act(() => {
        result.current.onMouseEnter();
        jest.advanceTimersByTime(50);
      });

      act(() => {
        result.current.onMouseEnter();
        jest.advanceTimersByTime(50);
      });

      // Should only prefetch once
      expect(mockRouter.prefetch).toHaveBeenCalledTimes(1);
    });

    it('should respect custom delay', () => {
      const { result } = renderHook(() => 
        useRoutePrefetch('/dashboard', { delay: 100 })
      );

      act(() => {
        result.current.onMouseEnter();
      });

      // Should not prefetch after default delay
      act(() => {
        jest.advanceTimersByTime(50);
      });
      expect(mockRouter.prefetch).not.toHaveBeenCalled();

      // Should prefetch after custom delay
      act(() => {
        jest.advanceTimersByTime(50);
      });
      expect(mockRouter.prefetch).toHaveBeenCalledWith('/dashboard');
    });

    it('should not prefetch when disabled', () => {
      const { result } = renderHook(() => 
        useRoutePrefetch('/dashboard', { enabled: false })
      );

      act(() => {
        result.current.onMouseEnter();
        jest.advanceTimersByTime(50);
      });

      expect(mockRouter.prefetch).not.toHaveBeenCalled();
    });

    it('should handle prefetch errors gracefully', () => {
      const consoleDebugSpy = jest.spyOn(console, 'debug').mockImplementation();
      mockRouter.prefetch.mockImplementation(() => {
        throw new Error('Prefetch failed');
      });

      const { result } = renderHook(() => useRoutePrefetch('/dashboard'));

      act(() => {
        result.current.onMouseEnter();
        jest.advanceTimersByTime(50);
      });

      // Should log error but not throw
      expect(consoleDebugSpy).toHaveBeenCalledWith(
        'Route prefetch failed:',
        '/dashboard',
        expect.any(Error)
      );

      consoleDebugSpy.mockRestore();
    });
  });

  describe('usePrefetchRoutes', () => {
    it('should prefetch multiple routes', () => {
      const routes = ['/dashboard', '/jobs', '/applications'];
      const { result } = renderHook(() => usePrefetchRoutes(routes));

      act(() => {
        result.current.prefetchAll();
      });

      expect(mockRouter.prefetch).toHaveBeenCalledTimes(3);
      expect(mockRouter.prefetch).toHaveBeenCalledWith('/dashboard');
      expect(mockRouter.prefetch).toHaveBeenCalledWith('/jobs');
      expect(mockRouter.prefetch).toHaveBeenCalledWith('/applications');
    });

    it('should not prefetch when disabled', () => {
      const routes = ['/dashboard', '/jobs'];
      const { result } = renderHook(() => usePrefetchRoutes(routes, false));

      act(() => {
        result.current.prefetchAll();
      });

      expect(mockRouter.prefetch).not.toHaveBeenCalled();
    });

    it('should handle errors for individual routes', () => {
      const consoleDebugSpy = jest.spyOn(console, 'debug').mockImplementation();
      mockRouter.prefetch.mockImplementation((route: string) => {
        if (route === '/jobs') {
          throw new Error('Prefetch failed');
        }
      });

      const routes = ['/dashboard', '/jobs', '/applications'];
      const { result } = renderHook(() => usePrefetchRoutes(routes));

      act(() => {
        result.current.prefetchAll();
      });

      // Should still prefetch other routes
      expect(mockRouter.prefetch).toHaveBeenCalledTimes(3);
      expect(consoleDebugSpy).toHaveBeenCalledWith(
        'Route prefetch failed:',
        '/jobs',
        expect.any(Error)
      );

      consoleDebugSpy.mockRestore();
    });
  });
});
