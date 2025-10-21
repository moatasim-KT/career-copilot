import React, { useState } from 'react'
import { ResponsiveModal } from './ResponsiveModal'
import { Button } from './ui/Button'
import { Card, CardContent } from './ui/Card'
import { 
  BugAntIcon, 
  LightBulbIcon, 
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  BoltIcon
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/helpers'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (feedback: FeedbackData) => Promise<void>
  initialType?: FeedbackType
  initialContext?: {
    pageUrl?: string
    userAgent?: string
    screenResolution?: string
  }
}

type FeedbackType = 'BUG_REPORT' | 'FEATURE_REQUEST' | 'GENERAL_FEEDBACK' | 'USABILITY_ISSUE' | 'PERFORMANCE_ISSUE'
type FeedbackPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

interface FeedbackData {
  type: FeedbackType
  title: string
  description: string
  priority: FeedbackPriority
  pageUrl?: string
  userAgent?: string
  screenResolution?: string
  browserInfo?: Record<string, any>
}

const feedbackTypes = [
  {
    id: 'BUG_REPORT' as FeedbackType,
    title: 'Bug Report',
    description: 'Report a problem or error',
    icon: BugAntIcon,
    color: 'red'
  },
  {
    id: 'FEATURE_REQUEST' as FeedbackType,
    title: 'Feature Request',
    description: 'Suggest a new feature or improvement',
    icon: LightBulbIcon,
    color: 'yellow'
  },
  {
    id: 'GENERAL_FEEDBACK' as FeedbackType,
    title: 'General Feedback',
    description: 'Share your thoughts or suggestions',
    icon: ChatBubbleLeftRightIcon,
    color: 'blue'
  },
  {
    id: 'USABILITY_ISSUE' as FeedbackType,
    title: 'Usability Issue',
    description: 'Report something that\'s hard to use',
    icon: ExclamationTriangleIcon,
    color: 'orange'
  },
  {
    id: 'PERFORMANCE_ISSUE' as FeedbackType,
    title: 'Performance Issue',
    description: 'Report slow loading or performance problems',
    icon: BoltIcon,
    color: 'purple'
  }
]

const priorityLevels = [
  { id: 'LOW' as FeedbackPriority, title: 'Low', description: 'Minor issue or suggestion' },
  { id: 'MEDIUM' as FeedbackPriority, title: 'Medium', description: 'Moderate impact on usage' },
  { id: 'HIGH' as FeedbackPriority, title: 'High', description: 'Significant impact on usage' },
  { id: 'CRITICAL' as FeedbackPriority, title: 'Critical', description: 'Blocks core functionality' }
]

export function FeedbackModal({
  isOpen,
  onClose,
  onSubmit,
  initialType,
  initialContext
}: FeedbackModalProps) {
  const [step, setStep] = useState<'type' | 'details'>('type')
  const [selectedType, setSelectedType] = useState<FeedbackType | null>(initialType || null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<FeedbackPriority>('MEDIUM')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleTypeSelect = (type: FeedbackType) => {
    setSelectedType(type)
    setStep('details')
  }

  const handleBack = () => {
    setStep('type')
    setErrors({})
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!title.trim()) {
      newErrors.title = 'Title is required'
    } else if (title.trim().length < 5) {
      newErrors.title = 'Title must be at least 5 characters'
    }

    if (!description.trim()) {
      newErrors.description = 'Description is required'
    } else if (description.trim().length < 10) {
      newErrors.description = 'Description must be at least 10 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!selectedType || !validateForm()) return

    setIsSubmitting(true)
    try {
      const feedbackData: FeedbackData = {
        type: selectedType,
        title: title.trim(),
        description: description.trim(),
        priority,
        pageUrl: initialContext?.pageUrl || window.location.href,
        userAgent: initialContext?.userAgent || navigator.userAgent,
        screenResolution: initialContext?.screenResolution || `${screen.width}x${screen.height}`,
        browserInfo: {
          language: navigator.language,
          platform: navigator.platform,
          cookieEnabled: navigator.cookieEnabled,
          onLine: navigator.onLine
        }
      }

      await onSubmit(feedbackData)
      
      // Reset form
      setStep('type')
      setSelectedType(null)
      setTitle('')
      setDescription('')
      setPriority('MEDIUM')
      setErrors({})
      
      onClose()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      setErrors({ submit: 'Failed to submit feedback. Please try again.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setStep('type')
    setSelectedType(null)
    setTitle('')
    setDescription('')
    setPriority('MEDIUM')
    setErrors({})
    onClose()
  }

  const selectedTypeInfo = feedbackTypes.find(t => t.id === selectedType)

  return (
    <ResponsiveModal
      isOpen={isOpen}
      onClose={handleClose}
      title={step === 'type' ? 'Send Feedback' : `${selectedTypeInfo?.title} Details`}
      size="md"
      footer={
        step === 'details' ? (
          <div className="flex justify-between">
            <Button variant="ghost" onClick={handleBack}>
              Back
            </Button>
            <div className="flex space-x-2">
              <Button variant="ghost" onClick={handleClose}>
                Cancel
              </Button>
              <Button 
                onClick={handleSubmit} 
                loading={isSubmitting}
                disabled={!title.trim() || !description.trim()}
              >
                Submit Feedback
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex justify-end">
            <Button variant="ghost" onClick={handleClose}>
              Cancel
            </Button>
          </div>
        )
      }
    >
      {step === 'type' ? (
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Help us improve Career Co-Pilot by sharing your feedback. What would you like to tell us about?
          </p>
          
          <div className="grid gap-3">
            {feedbackTypes.map((type) => {
              const Icon = type.icon
              return (
                <Card
                  key={type.id}
                  className={cn(
                    "cursor-pointer transition-all duration-200 hover:shadow-md border-2",
                    "hover:border-blue-300 dark:hover:border-blue-600"
                  )}
                  onClick={() => handleTypeSelect(type.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <div className={cn(
                        "p-2 rounded-lg",
                        {
                          'bg-red-100 dark:bg-red-900/20': type.color === 'red',
                          'bg-yellow-100 dark:bg-yellow-900/20': type.color === 'yellow',
                          'bg-blue-100 dark:bg-blue-900/20': type.color === 'blue',
                          'bg-orange-100 dark:bg-orange-900/20': type.color === 'orange',
                          'bg-purple-100 dark:bg-purple-900/20': type.color === 'purple'
                        }
                      )}>
                        <Icon className={cn(
                          "h-5 w-5",
                          {
                            'text-red-600 dark:text-red-400': type.color === 'red',
                            'text-yellow-600 dark:text-yellow-400': type.color === 'yellow',
                            'text-blue-600 dark:text-blue-400': type.color === 'blue',
                            'text-orange-600 dark:text-orange-400': type.color === 'orange',
                            'text-purple-600 dark:text-purple-400': type.color === 'purple'
                          }
                        )} />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {type.title}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {type.description}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {selectedTypeInfo && (
            <div className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className={cn(
                "p-2 rounded-lg",
                {
                  'bg-red-100 dark:bg-red-900/20': selectedTypeInfo.color === 'red',
                  'bg-yellow-100 dark:bg-yellow-900/20': selectedTypeInfo.color === 'yellow',
                  'bg-blue-100 dark:bg-blue-900/20': selectedTypeInfo.color === 'blue',
                  'bg-orange-100 dark:bg-orange-900/20': selectedTypeInfo.color === 'orange',
                  'bg-purple-100 dark:bg-purple-900/20': selectedTypeInfo.color === 'purple'
                }
              )}>
                <selectedTypeInfo.icon className={cn(
                  "h-5 w-5",
                  {
                    'text-red-600 dark:text-red-400': selectedTypeInfo.color === 'red',
                    'text-yellow-600 dark:text-yellow-400': selectedTypeInfo.color === 'yellow',
                    'text-blue-600 dark:text-blue-400': selectedTypeInfo.color === 'blue',
                    'text-orange-600 dark:text-orange-400': selectedTypeInfo.color === 'orange',
                    'text-purple-600 dark:text-purple-400': selectedTypeInfo.color === 'purple'
                  }
                )} />
              </div>
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">
                  {selectedTypeInfo.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedTypeInfo.description}
                </p>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="feedback-title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Title *
            </label>
            <input
              id="feedback-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Brief summary of your feedback"
              className={cn(
                "w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white",
                errors.title && "border-red-500 focus:ring-red-500 focus:border-red-500"
              )}
            />
            {errors.title && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.title}</p>
            )}
          </div>

          <div>
            <label htmlFor="feedback-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description *
            </label>
            <textarea
              id="feedback-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Please provide detailed information about your feedback..."
              rows={4}
              className={cn(
                "w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white resize-vertical",
                errors.description && "border-red-500 focus:ring-red-500 focus:border-red-500"
              )}
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.description}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Priority
            </label>
            <div className="grid grid-cols-2 gap-2">
              {priorityLevels.map((level) => (
                <button
                  key={level.id}
                  type="button"
                  onClick={() => setPriority(level.id)}
                  className={cn(
                    "p-3 text-left border rounded-lg transition-colors",
                    priority === level.id
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300"
                      : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                  )}
                >
                  <div className="font-medium text-sm">{level.title}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {level.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {errors.submit && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{errors.submit}</p>
            </div>
          )}
        </div>
      )}
    </ResponsiveModal>
  )
}