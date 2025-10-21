import { useState, useEffect } from 'react'

// Breakpoint definitions matching Tailwind CSS
const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const

type Breakpoint = keyof typeof breakpoints

interface ResponsiveState {
  width: number
  height: number
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  isLargeDesktop: boolean
  breakpoint: Breakpoint | 'xs'
  orientation: 'portrait' | 'landscape'
  isTouch: boolean
  pixelRatio: number
}

/**
 * Hook for responsive design utilities
 * Provides current screen size, breakpoint, and device information
 */
export function useResponsive(): ResponsiveState {
  const [state, setState] = useState<ResponsiveState>(() => {
    // Default state for SSR
    return {
      width: 1024,
      height: 768,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      isLargeDesktop: false,
      breakpoint: 'lg' as const,
      orientation: 'landscape',
      isTouch: false,
      pixelRatio: 1,
    }
  })

  useEffect(() => {
    if (typeof window === 'undefined') return

    const updateState = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      const pixelRatio = window.devicePixelRatio || 1
      
      // Determine breakpoint
      let breakpoint: Breakpoint | 'xs' = 'xs'
      if (width >= breakpoints['2xl']) breakpoint = '2xl'
      else if (width >= breakpoints.xl) breakpoint = 'xl'
      else if (width >= breakpoints.lg) breakpoint = 'lg'
      else if (width >= breakpoints.md) breakpoint = 'md'
      else if (width >= breakpoints.sm) breakpoint = 'sm'

      // Device type detection
      const isMobile = width < breakpoints.md
      const isTablet = width >= breakpoints.md && width < breakpoints.lg
      const isDesktop = width >= breakpoints.lg && width < breakpoints.xl
      const isLargeDesktop = width >= breakpoints.xl

      // Orientation
      const orientation = width > height ? 'landscape' : 'portrait'

      // Touch detection
      const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0

      setState({
        width,
        height,
        isMobile,
        isTablet,
        isDesktop,
        isLargeDesktop,
        breakpoint,
        orientation,
        isTouch,
        pixelRatio,
      })
    }

    // Initial update
    updateState()

    // Listen for resize events
    const handleResize = () => {
      // Debounce resize events
      clearTimeout(window.resizeTimeout)
      window.resizeTimeout = setTimeout(updateState, 100)
    }

    window.addEventListener('resize', handleResize)
    window.addEventListener('orientationchange', updateState)

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('orientationchange', updateState)
      clearTimeout(window.resizeTimeout)
    }
  }, [])

  return state
}

/**
 * Hook for media query matching
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return

    const mediaQuery = window.matchMedia(query)
    setMatches(mediaQuery.matches)

    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [query])

  return matches
}

/**
 * Hook for breakpoint-specific values
 */
export function useBreakpointValue<T>(values: Partial<Record<Breakpoint | 'xs', T>>): T | undefined {
  const { breakpoint } = useResponsive()
  
  // Return value for current breakpoint or fallback to smaller breakpoints
  const breakpointOrder: (Breakpoint | 'xs')[] = ['xs', 'sm', 'md', 'lg', 'xl', '2xl']
  const currentIndex = breakpointOrder.indexOf(breakpoint)
  
  for (let i = currentIndex; i >= 0; i--) {
    const bp = breakpointOrder[i]
    if (values[bp] !== undefined) {
      return values[bp]
    }
  }
  
  return undefined
}

/**
 * Hook for responsive grid columns
 */
export function useResponsiveColumns(
  mobile: number = 1,
  tablet: number = 2,
  desktop: number = 3,
  largeDesktop: number = 4
): number {
  const { isMobile, isTablet, isDesktop, isLargeDesktop } = useResponsive()
  
  if (isLargeDesktop) return largeDesktop
  if (isDesktop) return desktop
  if (isTablet) return tablet
  return mobile
}

/**
 * Hook for responsive spacing
 */
export function useResponsiveSpacing(): {
  containerPadding: string
  sectionSpacing: string
  cardPadding: string
  buttonSize: 'sm' | 'md' | 'lg'
} {
  const { isMobile, isTablet } = useResponsive()
  
  return {
    containerPadding: isMobile ? 'px-4' : isTablet ? 'px-6' : 'px-8',
    sectionSpacing: isMobile ? 'space-y-4' : isTablet ? 'space-y-6' : 'space-y-8',
    cardPadding: isMobile ? 'p-4' : isTablet ? 'p-6' : 'p-8',
    buttonSize: isMobile ? 'sm' : isTablet ? 'md' : 'lg',
  }
}

/**
 * Hook for responsive font sizes
 */
export function useResponsiveFontSize(): {
  heading1: string
  heading2: string
  heading3: string
  body: string
  caption: string
} {
  const { isMobile, isTablet } = useResponsive()
  
  if (isMobile) {
    return {
      heading1: 'text-2xl',
      heading2: 'text-xl',
      heading3: 'text-lg',
      body: 'text-sm',
      caption: 'text-xs',
    }
  }
  
  if (isTablet) {
    return {
      heading1: 'text-3xl',
      heading2: 'text-2xl',
      heading3: 'text-xl',
      body: 'text-base',
      caption: 'text-sm',
    }
  }
  
  return {
    heading1: 'text-4xl',
    heading2: 'text-3xl',
    heading3: 'text-2xl',
    body: 'text-lg',
    caption: 'text-base',
  }
}

/**
 * Hook for detecting device capabilities
 */
export function useDeviceCapabilities(): {
  supportsHover: boolean
  supportsTouch: boolean
  prefersReducedMotion: boolean
  prefersHighContrast: boolean
  supportsFocus: boolean
} {
  const [capabilities, setCapabilities] = useState({
    supportsHover: true,
    supportsTouch: false,
    prefersReducedMotion: false,
    prefersHighContrast: false,
    supportsFocus: true,
  })

  useEffect(() => {
    if (typeof window === 'undefined') return

    const supportsHover = window.matchMedia('(hover: hover)').matches
    const supportsTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches
    const supportsFocus = window.matchMedia('(focus: focus)').matches

    setCapabilities({
      supportsHover,
      supportsTouch,
      prefersReducedMotion,
      prefersHighContrast,
      supportsFocus,
    })
  }, [])

  return capabilities
}

// Extend Window interface for TypeScript
declare global {
  interface Window {
    resizeTimeout: NodeJS.Timeout
  }
}