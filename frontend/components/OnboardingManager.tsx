import React, { useState, useEffect, useCallback } from 'react'
import { TutorialOverlay } from './TutorialOverlay'
import { FeatureHighlight } from './FeatureHighlight'
import { FeedbackModal } from './FeedbackModal'
import { HelpCenter } from './HelpCenter'
import { Button } from './ui/Button'
import { 
  QuestionMarkCircleIcon, 
  ChatBubbleLeftRightIcon,
  AcademicCapIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { apiClient } from '@/utils/api'
import { cn } from '@/utils/helpers'

interface Tutorial {
  id: string
  title: string
  description: string
  category: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  estimated_time: number
  prerequisites: string[]
  steps: Array<{
    id: string
    title: string
    description: string
    target_element?: string
    position: 'top' | 'bottom' | 'left' | 'right' | 'center'
    content: string
    action_required: boolean
    action_text?: string
  }>
  is_required: boolean
}

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

interface OnboardingProgress {
  id: number
  user_id: number
  steps_completed: string[]
  current_step?: string
  tutorials_completed: string[]
  features_discovered: string[]
  help_topics_viewed: string[]
  show_tooltips: boolean
  show_feature_highlights: boolean
  onboarding_completed: boolean
  created_at: string
  updated_at: string
  completed_at?: string
}

interface OnboardingManagerProps {
  userId?: number
  autoStart?: boolean
  showHelpButton?: boolean
  showFeedbackButton?: boolean
}

export function OnboardingManager({
  userId,
  autoStart = true,
  showHelpButton = true,
  showFeedbackButton = true
}: OnboardingManagerProps) {
  // State management
  const [progress, setProgress] = useState<OnboardingProgress | null>(null)
  const [tutorials, setTutorials] = useState<Tutorial[]>([])
  const [featureHighlights, setFeatureHighlights] = useState<FeatureHighlight[]>([])
  
  // UI state
  const [currentTutorial, setCurrentTutorial] = useState<Tutorial | null>(null)
  const [currentHighlight, setCurrentHighlight] = useState<FeatureHighlight | null>(null)
  const [showHelpCenter, setShowHelpCenter] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [showFloatingButtons, setShowFloatingButtons] = useState(true)
  
  // Loading states
  const [loading, setLoading] = useState(false)
  const [initialized, setInitialized] = useState(false)

  // Initialize onboarding system
  useEffect(() => {
    if (userId && !initialized) {
      initializeOnboarding()
    }
  }, [userId, initialized])

  // Auto-start onboarding for new users
  useEffect(() => {
    if (autoStart && progress && !progress.onboarding_completed && tutorials.length > 0) {
      const requiredTutorials = tutorials.filter(t => t.is_required)
      const incompleteTutorials = requiredTutorials.filter(t => 
        !progress.tutorials_completed.includes(t.id)
      )
      
      if (incompleteTutorials.length > 0) {
        setCurrentTutorial(incompleteTutorials[0])
      }
    }
  }, [autoStart, progress, tutorials])

  // Show feature highlights
  useEffect(() => {
    if (progress?.show_feature_highlights && featureHighlights.length > 0) {
      const availableHighlights = featureHighlights.filter(h => 
        !progress.features_discovered.includes(h.id)
      )
      
      if (availableHighlights.length > 0) {
        // Show highest priority highlight
        const nextHighlight = availableHighlights.sort((a, b) => a.priority - b.priority)[0]
        
        // Check conditions if any
        if (nextHighlight.conditions) {
          const conditionsMet = checkHighlightConditions(nextHighlight.conditions)
          if (conditionsMet) {
            setCurrentHighlight(nextHighlight)
          }
        } else {
          setCurrentHighlight(nextHighlight)
        }
      }
    }
  }, [progress, featureHighlights])

  const initializeOnboarding = async () => {
    setLoading(true)
    try {
      const [progressResponse, tutorialsResponse, highlightsResponse] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/onboarding/progress`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/tutorials`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/feature-highlights`)
      ])
      
      const progressData = await progressResponse.json()
      const tutorialsData = await tutorialsResponse.json()
      const highlightsData = await highlightsResponse.json()
      
      setProgress(progressData)
      setTutorials(tutorialsData)
      setFeatureHighlights(highlightsData)
      setInitialized(true)
    } catch (error) {
      console.error('Failed to initialize onboarding:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkHighlightConditions = (conditions: Record<string, any>): boolean => {
    // Implement condition checking logic
    // For now, return true - in a real app, you'd check against user data
    return true
  }

  const handleTutorialComplete = async (tutorialId: string) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/onboarding/tutorial/${tutorialId}/complete`, {
        method: 'POST'
      })
      
      // Update local state
      setProgress(prev => prev ? {
        ...prev,
        tutorials_completed: [...prev.tutorials_completed, tutorialId]
      } : null)
      
      setCurrentTutorial(null)
      
      // Check if all required tutorials are complete
      const requiredTutorials = tutorials.filter(t => t.is_required)
      const completedRequired = requiredTutorials.filter(t => 
        progress?.tutorials_completed.includes(t.id) || t.id === tutorialId
      )
      
      if (completedRequired.length === requiredTutorials.length) {
        // Mark onboarding as complete
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/onboarding/progress`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            onboarding_completed: true
          })
        })
        
        setProgress(prev => prev ? {
          ...prev,
          onboarding_completed: true,
          completed_at: new Date().toISOString()
        } : null)
      }
    } catch (error) {
      console.error('Failed to complete tutorial:', error)
    }
  }

  const handleStepComplete = async (stepId: string) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/onboarding/step/${stepId}/complete`, {
        method: 'POST'
      })
      
      setProgress(prev => prev ? {
        ...prev,
        steps_completed: [...prev.steps_completed, stepId]
      } : null)
    } catch (error) {
      console.error('Failed to complete step:', error)
    }
  }

  const handleFeatureDiscover = async (featureId: string) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/onboarding/feature/${featureId}/discover`, {
        method: 'POST'
      })
      
      setProgress(prev => prev ? {
        ...prev,
        features_discovered: [...prev.features_discovered, featureId]
      } : null)
      
      setCurrentHighlight(null)
    } catch (error) {
      console.error('Failed to discover feature:', error)
    }
  }

  const handleFeatureDismiss = (featureId: string) => {
    setCurrentHighlight(null)
    // Optionally mark as discovered to prevent showing again
    handleFeatureDiscover(featureId)
  }

  const handleFeedbackSubmit = async (feedbackData: any) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackData)
      })
      // Show success message or toast
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      throw error
    }
  }

  const startTutorial = (tutorialId: string) => {
    const tutorial = tutorials.find(t => t.id === tutorialId)
    if (tutorial) {
      setCurrentTutorial(tutorial)
    }
  }

  const toggleTooltips = async () => {
    const newValue = !progress?.show_tooltips
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/onboarding/progress`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          show_tooltips: newValue
        })
      })
      
      setProgress(prev => prev ? {
        ...prev,
        show_tooltips: newValue
      } : null)
    } catch (error) {
      console.error('Failed to toggle tooltips:', error)
    }
  }

  const toggleFeatureHighlights = async () => {
    const newValue = !progress?.show_feature_highlights
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/onboarding/progress`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          show_feature_highlights: newValue
        })
      })
      
      setProgress(prev => prev ? {
        ...prev,
        show_feature_highlights: newValue
      } : null)
    } catch (error) {
      console.error('Failed to toggle feature highlights:', error)
    }
  }

  if (!userId || loading) {
    return null
  }

  return (
    <>
      {/* Tutorial Overlay */}
      {currentTutorial && (
        <TutorialOverlay
          tutorial={currentTutorial}
          isOpen={!!currentTutorial}
          onClose={() => setCurrentTutorial(null)}
          onComplete={handleTutorialComplete}
          onStepComplete={handleStepComplete}
        />
      )}

      {/* Feature Highlights */}
      {currentHighlight && (
        <FeatureHighlight
          highlight={currentHighlight}
          isVisible={!!currentHighlight}
          onDismiss={handleFeatureDismiss}
          onDiscover={handleFeatureDiscover}
        />
      )}

      {/* Help Center Modal */}
      <HelpCenter
        isOpen={showHelpCenter}
        onClose={() => setShowHelpCenter(false)}
      />

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmit={handleFeedbackSubmit}
      />

      {/* Floating Help Buttons */}
      {showFloatingButtons && (showHelpButton || showFeedbackButton) && (
        <div className="fixed bottom-4 right-4 z-30 flex flex-col space-y-2">
          {/* Collapse/Expand Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFloatingButtons(false)}
            className="self-end p-2 bg-white dark:bg-gray-800 shadow-lg rounded-full"
            aria-label="Hide help buttons"
          >
            <XMarkIcon className="h-4 w-4" />
          </Button>

          {/* Tutorial Menu */}
          {tutorials.length > 0 && (
            <div className="relative group">
              <Button
                variant="primary"
                size="sm"
                className="p-3 rounded-full shadow-lg"
                aria-label="Tutorials"
              >
                <AcademicCapIcon className="h-5 w-5" />
              </Button>
              
              <div className="absolute bottom-full right-0 mb-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                <div className="p-3">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Available Tutorials
                  </h4>
                  <div className="space-y-1">
                    {tutorials.map((tutorial) => (
                      <button
                        key={tutorial.id}
                        onClick={() => startTutorial(tutorial.id)}
                        className={cn(
                          "w-full text-left p-2 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-700",
                          progress?.tutorials_completed.includes(tutorial.id) 
                            ? "text-green-600 dark:text-green-400" 
                            : "text-gray-700 dark:text-gray-300"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span>{tutorial.title}</span>
                          {progress?.tutorials_completed.includes(tutorial.id) && (
                            <span className="text-xs">✓</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {tutorial.estimated_time} min • {tutorial.difficulty}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Help Button */}
          {showHelpButton && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowHelpCenter(true)}
              className="p-3 rounded-full shadow-lg"
              aria-label="Help Center"
            >
              <QuestionMarkCircleIcon className="h-5 w-5" />
            </Button>
          )}

          {/* Feedback Button */}
          {showFeedbackButton && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFeedbackModal(true)}
              className="p-3 rounded-full shadow-lg bg-white dark:bg-gray-800"
              aria-label="Send Feedback"
            >
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
            </Button>
          )}
        </div>
      )}

      {/* Collapsed Help Button */}
      {!showFloatingButtons && (
        <Button
          variant="primary"
          size="sm"
          onClick={() => setShowFloatingButtons(true)}
          className="fixed bottom-4 right-4 z-30 p-3 rounded-full shadow-lg"
          aria-label="Show help buttons"
        >
          <QuestionMarkCircleIcon className="h-5 w-5" />
        </Button>
      )}

      {/* Onboarding Progress Indicator (for new users) */}
      {progress && !progress.onboarding_completed && (
        <div className="fixed top-4 right-4 z-20 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              Getting Started
            </span>
          </div>
          <div className="mt-2">
            <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-1">
              <div 
                className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                style={{ 
                  width: `${(progress.tutorials_completed.length / tutorials.filter(t => t.is_required).length) * 100}%` 
                }}
              />
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {progress.tutorials_completed.length} of {tutorials.filter(t => t.is_required).length} tutorials complete
            </p>
          </div>
        </div>
      )}
    </>
  )
}