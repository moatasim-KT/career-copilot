import type { AppProps } from 'next/app'
import { useEffect } from 'react'
import { ThemeProvider } from '@/components/ThemeProvider'
import { AccessibilityProvider } from '@/contexts/AccessibilityContext'
import { PerformanceMonitor } from '@/components/PerformanceMonitor'
import { useDeviceCapabilities } from '@/hooks/useResponsive'
import { resourcePreloader } from '@/utils/progressive-loading'
import '@/styles/globals.css'
import '@/styles/accessibility.css'

function AppContent({ Component, pageProps }: AppProps) {
  const { supportsTouch, prefersReducedMotion } = useDeviceCapabilities()

  useEffect(() => {
    // Preload critical resources
    if (typeof window !== 'undefined') {
      // Preload fonts
      resourcePreloader.preloadFont('/fonts/inter-var.woff2', 'font/woff2').catch(() => {
        // Fallback to system fonts if preload fails
      })
      
      // Add device capability classes to body for CSS targeting
      if (supportsTouch) {
        document.body.classList.add('touch-device')
      }
      
      // Add motion preference class
      if (prefersReducedMotion) {
        document.body.classList.add('reduce-motion')
      }
      
      // Viewport height fix for mobile browsers
      const setVH = () => {
        const vh = window.innerHeight * 0.01
        document.documentElement.style.setProperty('--vh', `${vh}px`)
      }
      
      setVH()
      window.addEventListener('resize', setVH)
      window.addEventListener('orientationchange', setVH)
      
      return () => {
        window.removeEventListener('resize', setVH)
        window.removeEventListener('orientationchange', setVH)
      }
    }
  }, [supportsTouch, prefersReducedMotion])

  return (
    <>
      <Component {...pageProps} />
      <PerformanceMonitor />
    </>
  )
}

export default function App(props: AppProps) {
  return (
    <AccessibilityProvider>
      <ThemeProvider>
        <AppContent {...props} />
      </ThemeProvider>
    </AccessibilityProvider>
  )
}