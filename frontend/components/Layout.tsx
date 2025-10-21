import { ReactNode, useEffect, useState } from 'react'
import Head from 'next/head'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'
import { OfflineStatus } from './OfflineStatus'
import { SkipLinks } from './SkipLinks'
import { ResponsiveContainer } from './ResponsiveContainer'
import { OnboardingManager } from './OnboardingManager'
import { useTheme } from '@/hooks/useTheme'
import { useResponsive, useResponsiveSpacing } from '@/hooks/useResponsive'
import { serviceWorkerManager } from '@/utils/service-worker'
import { performanceMonitor } from '@/utils/progressive-loading'

interface LayoutProps {
  children: ReactNode
  title?: string
  description?: string
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'responsive'
  showSidebar?: boolean
  userId?: number
  enableOnboarding?: boolean
}

export function Layout({ 
  children, 
  title = 'Career Co-Pilot', 
  description = 'Intelligent career management system',
  maxWidth = 'xl',
  padding = 'responsive',
  showSidebar = true,
  userId,
  enableOnboarding = true
}: LayoutProps) {
  const { theme } = useTheme()
  const { isMobile, isTablet } = useResponsive()
  const { containerPadding, sectionSpacing } = useResponsiveSpacing()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    // Start performance monitoring
    performanceMonitor.startTiming('layout_render')
    
    // Register service worker on mount
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      serviceWorkerManager.register().catch(console.error);
    }

    // End performance monitoring
    performanceMonitor.endTiming('layout_render')
  }, []);

  // Close sidebar on mobile when clicking outside
  useEffect(() => {
    if (sidebarOpen && isMobile) {
      const handleClickOutside = () => setSidebarOpen(false)
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [sidebarOpen, isMobile])

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'dark' : ''}`}>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Career Co-Pilot" />
        
        {/* Responsive meta tags */}
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />
        
        {/* Preload critical resources */}
        <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        
        {/* DNS prefetch for external resources */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
      </Head>
      
      {/* Skip Links for keyboard navigation */}
      <SkipLinks />
      
      <div className="bg-white dark:bg-gray-900 transition-colors duration-200">
        <Navbar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        
        <div className="flex relative">
          {/* Sidebar */}
          {showSidebar && (
            <>
              {/* Mobile sidebar overlay */}
              {isMobile && sidebarOpen && (
                <div 
                  className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
                  onClick={() => setSidebarOpen(false)}
                  aria-hidden="true"
                />
              )}
              
              {/* Sidebar component */}
              <div className={`
                ${isMobile ? 'fixed' : 'relative'} 
                ${isMobile && !sidebarOpen ? '-translate-x-full' : 'translate-x-0'}
                ${isMobile ? 'z-50' : 'z-auto'}
                transition-transform duration-300 ease-in-out
                ${isMobile ? 'top-16 left-0 h-[calc(100vh-4rem)]' : ''}
              `}>
                <Sidebar 
                  isOpen={sidebarOpen} 
                  onClose={() => setSidebarOpen(false)}
                  isMobile={isMobile}
                />
              </div>
            </>
          )}
          
          {/* Main content */}
          <main 
            id="main-content"
            className={`
              flex-1 min-h-screen bg-gray-50 dark:bg-gray-800 transition-colors duration-200
              ${isMobile ? 'w-full' : ''}
              ${showSidebar && !isMobile ? 'ml-0' : ''}
            `}
            role="main"
            aria-label="Main content"
          >
            <ResponsiveContainer 
              maxWidth={maxWidth}
              padding={padding}
              className={`py-4 sm:py-6 lg:py-8 ${sectionSpacing}`}
            >
              {children}
            </ResponsiveContainer>
          </main>
        </div>
        
        {/* Offline Status - Responsive positioning */}
        <div className={`
          fixed z-40 transition-all duration-300
          ${isMobile ? 'bottom-4 left-4 right-4' : 'bottom-4 right-4'}
        `}>
          <OfflineStatus />
        </div>
        
        {/* Mobile navigation indicator */}
        {isMobile && showSidebar && (
          <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 z-30">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
              aria-label={sidebarOpen ? 'Close navigation' : 'Open navigation'}
            >
              <svg 
                className={`w-6 h-6 transition-transform ${sidebarOpen ? 'rotate-180' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        )}
        
        {/* Onboarding Manager */}
        {enableOnboarding && userId && (
          <OnboardingManager
            userId={userId}
            autoStart={true}
            showHelpButton={true}
            showFeedbackButton={true}
          />
        )}
      </div>
    </div>
  )
}