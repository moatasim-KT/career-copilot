import React, { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { Button } from './ui/Button'
import { Card, CardContent } from './ui/Card'
import { Progress } from './ui/Progress'
import { useAccessibility } from '@/contexts/AccessibilityContext'
import { cn } from '@/utils/helpers'

interface TutorialStep {
  id: string
  title: string
  description: string
  target_element?: string
  position: 'top' | 'bottom' | 'left' | 'right' | 'center'
  content: string
  action_required: boolean
  action_text?: string
}

interface Tutorial {
  id: string
  title: string
  description: string
  category: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  estimated_time: number
  prerequisites: string[]
  steps: TutorialStep[]
  is_required: boolean
}

interface TutorialOverlayProps {
  tutorial: Tutorial
  isOpen: boolean
  onClose: () => void
  onComplete: (tutorialId: string) => void
  onStepComplete?: (stepId: string) => void
}

export function TutorialOverlay({
  tutorial,
  isOpen,
  onClose,
  onComplete,
  onStepComplete
}: TutorialOverlayProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null)
  const [overlayPosition, setOverlayPosition] = useState({ top: 0, left: 0 })
  const { announceToScreenReader } = useAccessibility()
  const overlayRef = useRef<HTMLDivElement>(null)

  const currentStep = tutorial.steps[currentStepIndex]
  const isLastStep = currentStepIndex === tutorial.steps.length - 1
  const progress = ((currentStepIndex + 1) / tutorial.steps.length) * 100

  useEffect(() => {
    if (isOpen && currentStep) {
      announceToScreenReader(`Tutorial step ${currentStepIndex + 1} of ${tutorial.steps.length}: ${currentStep.title}`)
      
      // Find target element if specified
      if (currentStep.target_element) {
        const element = document.querySelector(currentStep.target_element) as HTMLElement
        if (element) {
          setTargetElement(element)
          calculatePosition(element, currentStep.position)
          
          // Scroll element into view
          element.scrollIntoView({ behavior: 'smooth', block: 'center' })
          
          // Highlight the target element
          element.classList.add('tutorial-highlight')
        }
      } else {
        setTargetElement(null)
        // Center the overlay
        setOverlayPosition({
          top: window.innerHeight / 2 - 200,
          left: window.innerWidth / 2 - 200
        })
      }
    }

    return () => {
      // Remove highlight from all elements
      document.querySelectorAll('.tutorial-highlight').forEach(el => {
        el.classList.remove('tutorial-highlight')
      })
    }
  }, [isOpen, currentStepIndex, currentStep, announceToScreenReader])

  const calculatePosition = (element: HTMLElement, position: string) => {
    const rect = element.getBoundingClientRect()
    const overlayWidth = 400
    const overlayHeight = 300
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
      case 'center':
      default:
        top = window.innerHeight / 2 - overlayHeight / 2
        left = window.innerWidth / 2 - overlayWidth / 2
        break
    }

    // Ensure overlay stays within viewport
    top = Math.max(20, Math.min(top, window.innerHeight - overlayHeight - 20))
    left = Math.max(20, Math.min(left, window.innerWidth - overlayWidth - 20))

    setOverlayPosition({ top, left })
  }

  const handleNext = () => {
    if (onStepComplete) {
      onStepComplete(currentStep.id)
    }

    if (isLastStep) {
      onComplete(tutorial.id)
      onClose()
    } else {
      setCurrentStepIndex(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1)
    }
  }

  const handleSkip = () => {
    onClose()
  }

  if (!isOpen) return null

  const overlayContent = (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-40" />
      
      {/* Tutorial overlay */}
      <div
        ref={overlayRef}
        className="fixed z-50 w-96 max-w-sm"
        style={{
          top: overlayPosition.top,
          left: overlayPosition.left
        }}
      >
        <Card className="shadow-2xl border-2 border-blue-500">
          <CardContent className="p-0">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {tutorial.category} • {tutorial.difficulty}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="p-1"
                  aria-label="Close tutorial"
                >
                  <XMarkIcon className="h-4 w-4" />
                </Button>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                {currentStep.title}
              </h3>
              
              <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                <span>Step {currentStepIndex + 1} of {tutorial.steps.length}</span>
                <span>{tutorial.estimated_time} min</span>
              </div>
              
              <Progress value={progress} className="mt-2" />
            </div>

            {/* Content */}
            <div className="p-4">
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                {currentStep.content}
              </p>
              
              {currentStep.action_required && currentStep.action_text && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse" />
                    <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                      Action Required: {currentStep.action_text}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center justify-between">
                <div className="flex space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handlePrevious}
                    disabled={currentStepIndex === 0}
                    className="flex items-center"
                  >
                    <ChevronLeftIcon className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleSkip}
                    className="text-gray-600 dark:text-gray-400"
                  >
                    Skip Tutorial
                  </Button>
                </div>
                
                <Button
                  onClick={handleNext}
                  size="sm"
                  className="flex items-center"
                >
                  {isLastStep ? 'Complete' : 'Next'}
                  {!isLastStep && <ChevronRightIcon className="h-4 w-4 ml-1" />}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pointer/Arrow */}
      {targetElement && currentStep.position !== 'center' && (
        <div
          className={cn(
            "fixed z-50 w-0 h-0",
            {
              'border-l-8 border-r-8 border-b-8 border-l-transparent border-r-transparent border-b-white dark:border-b-gray-800':
                currentStep.position === 'top',
              'border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-white dark:border-t-gray-800':
                currentStep.position === 'bottom',
              'border-t-8 border-b-8 border-r-8 border-t-transparent border-b-transparent border-r-white dark:border-r-gray-800':
                currentStep.position === 'left',
              'border-t-8 border-b-8 border-l-8 border-t-transparent border-b-transparent border-l-white dark:border-l-gray-800':
                currentStep.position === 'right'
            }
          )}
          style={{
            top: currentStep.position === 'top' ? overlayPosition.top + 300 :
                 currentStep.position === 'bottom' ? overlayPosition.top - 8 :
                 overlayPosition.top + 150,
            left: currentStep.position === 'left' ? overlayPosition.left + 400 :
                  currentStep.position === 'right' ? overlayPosition.left - 8 :
                  overlayPosition.left + 200
          }}
        />
      )}
    </>
  )

  return createPortal(overlayContent, document.body)
}

// Tutorial highlight styles (add to global CSS)
export const tutorialStyles = `
.tutorial-highlight {
  position: relative;
  z-index: 30;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5), 0 0 0 8px rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  transition: all 0.3s ease-in-out;
}

.tutorial-highlight::before {
  content: '';
  position: absolute;
  inset: -4px;
  border: 2px solid #3b82f6;
  border-radius: 8px;
  animation: tutorial-pulse 2s infinite;
}

@keyframes tutorial-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.02);
  }
}
`