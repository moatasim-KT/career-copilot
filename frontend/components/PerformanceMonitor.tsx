import { useEffect, useState } from 'react'
import { performanceMonitor } from '@/utils/progressive-loading'
import { useResponsive } from '@/hooks/useResponsive'

interface PerformanceMetrics {
  lcp: number
  fid: number
  cls: number
  loadTime: number
  renderTime: number
}

/**
 * Performance monitoring component for development
 */
export function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
  const [showMetrics, setShowMetrics] = useState(false)
  const { isMobile } = useResponsive()

  useEffect(() => {
    // Only show in development
    if (process.env.NODE_ENV !== 'development') return

    const measurePerformance = async () => {
      performanceMonitor.startTiming('page_load')
      
      // Wait for page to be fully loaded
      if (document.readyState === 'complete') {
        const lcp = await performanceMonitor.measureLCP()
        const fid = await performanceMonitor.measureFID()
        const cls = await performanceMonitor.measureCLS()
        
        performanceMonitor.endTiming('page_load')
        
        const loadTime = performanceMonitor.getTiming('page_load')
        const renderTime = performanceMonitor.getTiming('layout_render') || 0

        setMetrics({
          lcp,
          fid,
          cls,
          loadTime,
          renderTime,
        })
      } else {
        window.addEventListener('load', measurePerformance)
      }
    }

    measurePerformance()

    return () => {
      window.removeEventListener('load', measurePerformance)
    }
  }, [])

  if (process.env.NODE_ENV !== 'development' || !metrics) {
    return null
  }

  const getScoreColor = (value: number, thresholds: [number, number]) => {
    if (value <= thresholds[0]) return 'text-green-600'
    if (value <= thresholds[1]) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <button
        onClick={() => setShowMetrics(!showMetrics)}
        className="bg-gray-800 text-white p-2 rounded-full shadow-lg hover:bg-gray-700 transition-colors"
        title="Performance Metrics"
      >
        📊
      </button>

      {showMetrics && (
        <div className={`
          absolute bottom-12 left-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-4 min-w-64
          ${isMobile ? 'text-sm' : 'text-base'}
        `}>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
            Performance Metrics
          </h3>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">LCP:</span>
              <span className={getScoreColor(metrics.lcp, [2500, 4000])}>
                {metrics.lcp.toFixed(0)}ms
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">FID:</span>
              <span className={getScoreColor(metrics.fid, [100, 300])}>
                {metrics.fid.toFixed(0)}ms
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">CLS:</span>
              <span className={getScoreColor(metrics.cls * 1000, [100, 250])}>
                {metrics.cls.toFixed(3)}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Load:</span>
              <span className={getScoreColor(metrics.loadTime, [1000, 3000])}>
                {metrics.loadTime.toFixed(0)}ms
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Render:</span>
              <span className={getScoreColor(metrics.renderTime, [16, 50])}>
                {metrics.renderTime.toFixed(0)}ms
              </span>
            </div>
          </div>
          
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              <div>Device: {isMobile ? 'Mobile' : 'Desktop'}</div>
              <div>Connection: {(navigator as any).connection?.effectiveType || 'Unknown'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Progressive loading indicator component
 */
export function ProgressiveLoadingIndicator({ 
  loading, 
  progress = 0,
  message = 'Loading...' 
}: {
  loading: boolean
  progress?: number
  message?: string
}) {
  const { isMobile } = useResponsive()

  if (!loading) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`
        bg-white dark:bg-gray-800 rounded-lg p-6 shadow-xl max-w-sm mx-4
        ${isMobile ? 'w-full' : 'w-auto'}
      `}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          
          <p className="text-gray-900 dark:text-white font-medium mb-2">
            {message}
          </p>
          
          {progress > 0 && (
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(progress, 100)}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Lazy loading skeleton component
 */
export function LazyLoadingSkeleton({ 
  className = '',
  lines = 3,
  showAvatar = false 
}: {
  className?: string
  lines?: number
  showAvatar?: boolean
}) {
  return (
    <div className={`animate-pulse ${className}`}>
      <div className="flex items-start space-x-4">
        {showAvatar && (
          <div className="rounded-full bg-gray-300 dark:bg-gray-600 h-12 w-12 flex-shrink-0" />
        )}
        
        <div className="flex-1 space-y-2">
          {Array.from({ length: lines }).map((_, i) => (
            <div 
              key={i}
              className={`h-4 bg-gray-300 dark:bg-gray-600 rounded ${
                i === lines - 1 ? 'w-3/4' : 'w-full'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Image loading skeleton
 */
export function ImageSkeleton({ 
  width = '100%', 
  height = '200px',
  className = '' 
}: {
  width?: string | number
  height?: string | number
  className?: string
}) {
  return (
    <div 
      className={`bg-gray-300 dark:bg-gray-600 animate-pulse rounded ${className}`}
      style={{ width, height }}
    >
      <div className="flex items-center justify-center h-full">
        <svg 
          className="w-8 h-8 text-gray-400 dark:text-gray-500" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
          />
        </svg>
      </div>
    </div>
  )
}