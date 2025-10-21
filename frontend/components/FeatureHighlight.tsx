import React, { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { XMarkIcon, LightBulbIcon } from '@heroicons/react/24/outline'
import { Button } from './ui/Button'
import { Card, CardContent } from './ui/Card'
import { useAccessibility } from '@/contexts/AccessibilityContext'
import { cn } from '@/utils/helpers'

interface FeatureHighlight {
  id: string
  title: string
  description: string
  target_element: string
  position: 'top' | 'bottom' | 'left' | 'right'
  priority: number
  show_once: boolean
  conditions?: Record<string, any>
}

interface FeatureHighlightProps {
  highlight: FeatureHighlight
  isVisible: boolean
  onDismiss: (featureId: string) => void
  onDiscover: (featureId: string) => void
}

export function FeatureHighlight({
  highlight,
  isVisible,
  onDismiss,
  onDiscover
}: FeatureHighlightProps) {
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null)
  const [overlayPosition, setOverlayPosition] = useState({ top: 0, left: 0 })
  const [isAnimating, setIsAnimating] = useState(false)
  const { announceToScreenReader } = useAccessibility()
  const overlayRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    if (isVisible) {
      // Find target element
      const element = document.querySelector(highlight.target_element) as HTMLElement
      if (element) {
        setTargetElement(element)
        calculatePosition(element, highlight.position)
        
        // Add highlight class
        element.classList.add('feature-highlight')
        
        // Announce to screen reader
        announceToScreenReader(`New feature available: ${highlight.title}`)
        
        // Start animation
        setIsAnimating(true)
        
        // Auto-dismiss after 10 seconds if show_once is true
        if (highlight.show_once) {
          timeoutRef.current = setTimeout(() => {
            handleDismiss()
          }, 10000)
        }
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      // Remove highlight from all elements
      document.querySelectorAll('.feature-highlight').forEach(el => {
        el.classList.remove('feature-highlight')
      })
    }
  }, [isVisible, highlight, announceToScreenReader])

  const calculatePosition = (element: HTMLElement, position: string) => {
    const rect = element.getBoundingClientRect()
    const overlayWidth = 320
    const overlayHeight = 200
    let top = 0
    let left = 0

    switch (position) {
      case 'top':
        top = rect.top - overlayHeight - 20
        left = rect.left + (rect.width / 2) - (overlayWidth / 2)
        break
      case 'bottom':
        top = rect.bottom + 20
        left = rect.left + (rect.width / 2) - (overlayWidth / 2)
        break
      case 'left':
        top = rect.top + (rect.height / 2) - (overlayHeight / 2)
        left = rect.left - overlayWidth - 20
        break
      case 'right':
        top = rect.top + (rect.height / 2) - (overlayHeight / 2)
        left = rect.right + 20
        break
    }

    // Ensure overlay stays within viewport
    top = Math.max(20, Math.min(top, window.innerHeight - overlayHeight - 20))
    left = Math.max(20, Math.min(left, window.innerWidth - overlayWidth - 20))

    setOverlayPosition({ top, left })
  }

  const handleDismiss = () => {
    setIsAnimating(false)
    setTimeout(() => {
      onDismiss(highlight.id)
    }, 300)
  }

  const handleDiscover = () => {
    onDiscover(highlight.id)
    handleDismiss()
  }

  if (!isVisible || !targetElement) return null

  const overlayContent = (
    <div
      ref={overlayRef}
      className={cn(
        "fixed z-40 w-80 transition-all duration-300 ease-out",
        isAnimating ? "opacity-100 scale-100" : "opacity-0 scale-95"
      )}
      style={{
        top: overlayPosition.top,
        left: overlayPosition.left
      }}
    >
      <Card className="shadow-xl border-2 border-yellow-400 bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20">
        <CardContent className="p-0">
          {/* Header */}
          <div className="p-4 border-b border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-1 bg-yellow-400 rounded-full">
                  <LightBulbIcon className="h-4 w-4 text-yellow-900" />
                </div>
                <span className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  New Feature
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDismiss}
                className="p-1 text-yellow-600 hover:text-yellow-800 dark:text-yellow-400 dark:hover:text-yellow-200"
                aria-label="Dismiss feature highlight"
              >
                <XMarkIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {highlight.title}
            </h3>
            <p className="text-gray-700 dark:text-gray-300 text-sm mb-4">
              {highlight.description}
            </p>
            
            <div className="flex space-x-2">
              <Button
                onClick={handleDiscover}
                size="sm"
                className="bg-yellow-500 hover:bg-yellow-600 text-yellow-900"
              >
                Try it now
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDismiss}
                className="text-gray-600 dark:text-gray-400"
              >
                Maybe later
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pointer/Arrow */}
      <div
        className={cn(
          "absolute w-0 h-0",
          {
            'border-l-8 border-r-8 border-b-8 border-l-transparent border-r-transparent border-b-yellow-400 -bottom-2 left-1/2 transform -translate-x-1/2':
              highlight.position === 'top',
            'border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-yellow-400 -top-2 left-1/2 transform -translate-x-1/2':
              highlight.position === 'bottom',
            'border-t-8 border-b-8 border-r-8 border-t-transparent border-b-transparent border-r-yellow-400 -right-2 top-1/2 transform -translate-y-1/2':
              highlight.position === 'left',
            'border-t-8 border-b-8 border-l-8 border-t-transparent border-b-transparent border-l-yellow-400 -left-2 top-1/2 transform -translate-y-1/2':
              highlight.position === 'right'
          }
        )}
      />
    </div>
  )

  return createPortal(overlayContent, document.body)
}

// Feature highlight styles (add to global CSS)
export const featureHighlightStyles = `
.feature-highlight {
  position: relative;
  z-index: 20;
  animation: feature-glow 3s ease-in-out infinite;
}

.feature-highlight::before {
  content: '';
  position: absolute;
  inset: -2px;
  border: 2px solid #fbbf24;
  border-radius: 6px;
  animation: feature-pulse 2s ease-in-out infinite;
}

@keyframes feature-glow {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.3);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.5), 0 0 20px rgba(251, 191, 36, 0.2);
  }
}

@keyframes feature-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.01);
  }
}
`