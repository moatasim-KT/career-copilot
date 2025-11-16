/**
 * FeatureTour Component
 * 
 * A multi-step modal that guides users through key features of the application.
 * Can be triggered from the Help menu or shown to new users.
 * 
 * Features:
 * - Multi-step walkthrough with navigation
 * - Screenshots or GIFs for visual guidance
 * - Progress indicator
 * - Skip functionality
 * - Keyboard navigation
 * - Accessible
 * 
 * Usage:
 * ```tsx
 * <FeatureTour
 *   isOpen={showTour}
 *   onClose={() => setShowTour(false)}
 *   onComplete={() => handleTourComplete()}
 * />
 * ```
 */

'use client';

import {
  X,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Briefcase,
  FileText,
  Sparkles,
  BarChart3,
  Command,
  Bell,
  Search,
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

import { Modal2 } from '@/components/ui/Modal2';
import { logger } from '@/lib/logger';
import { m, AnimatePresence } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface TourStep {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  image?: string; // URL to screenshot or GIF
  tips?: string[]; // Additional tips or shortcuts
}

const defaultSteps: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to Career Copilot',
    description:
      'Your AI-powered job search assistant. Let\'s take a quick tour of the key features to help you get started.',
    icon: Sparkles,
    tips: [
      'Track all your job applications in one place',
      'Get AI-powered job recommendations',
      'Analyze your job search progress',
    ],
  },
  {
    id: 'dashboard',
    title: 'Dashboard Overview',
    description:
      'Your central hub for tracking job search progress. View key metrics, recent activity, and quick actions all in one place.',
    icon: LayoutDashboard,
    tips: [
      'Customize widget layout by dragging',
      'View application status at a glance',
      'Access quick actions for common tasks',
    ],
  },
  {
    id: 'jobs',
    title: 'Browse & Save Jobs',
    description:
      'Discover job opportunities tailored to your profile. Save interesting positions and track your applications.',
    icon: Briefcase,
    tips: [
      'Use filters to narrow down results',
      'Save jobs to review later',
      'Get AI-powered match scores',
    ],
  },
  {
    id: 'applications',
    title: 'Track Applications',
    description:
      'Manage all your job applications in one place. Update statuses, add notes, and never miss a follow-up.',
    icon: FileText,
    tips: [
      'Drag cards between status columns',
      'Set reminders for follow-ups',
      'Export your application history',
    ],
  },
  {
    id: 'command-palette',
    title: 'Command Palette',
    description:
      'Access any feature instantly with the command palette. Press ⌘K (Mac) or Ctrl+K (Windows) to open.',
    icon: Command,
    tips: [
      'Search for jobs and applications',
      'Navigate to any page quickly',
      'Execute actions without clicking',
    ],
  },
  {
    id: 'advanced-search',
    title: 'Advanced Search',
    description:
      'Build complex queries with AND/OR logic to find exactly what you\'re looking for.',
    icon: Search,
    tips: [
      'Combine multiple filters',
      'Save searches for later',
      'Export search results',
    ],
  },
  {
    id: 'analytics',
    title: 'Analytics & Insights',
    description:
      'Visualize your job search progress with interactive charts and gain insights into your application success rate.',
    icon: BarChart3,
    tips: [
      'Track application trends over time',
      'Identify top skills in demand',
      'Compare your success rate',
    ],
  },
  {
    id: 'notifications',
    title: 'Stay Updated',
    description:
      'Get real-time notifications for new job matches, application updates, and important reminders.',
    icon: Bell,
    tips: [
      'Customize notification preferences',
      'Enable browser push notifications',
      'Never miss an important update',
    ],
  },
];

export interface FeatureTourProps {
  /**
   * Whether the tour is open
   */
  isOpen: boolean;

  /**
   * Callback when tour is closed
   */
  onClose: () => void;

  /**
   * Callback when tour is completed
   */
  onComplete?: () => void;

  /**
   * Custom steps (optional, uses default steps if not provided)
   */
  steps?: TourStep[];

  /**
   * Initial step index
   */
  initialStep?: number;

  /**
   * Whether to show progress indicator
   */
  showProgress?: boolean;

  /**
   * Whether to allow skipping
   */
  allowSkip?: boolean;
}

export function FeatureTour({
  isOpen,
  onClose,
  onComplete,
  steps = defaultSteps,
  initialStep = 0,
  showProgress = true,
  allowSkip = true,
}: FeatureTourProps) {
  const [currentStep, setCurrentStep] = useState(initialStep);
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward');

  const step = steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;
  const progress = ((currentStep + 1) / steps.length) * 100;

  // Reset to initial step when opened
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(initialStep);
    }
  }, [isOpen, initialStep]);

  const handleComplete = useCallback(() => {
    onComplete?.();
    onClose();
  }, [onComplete, onClose]);

  const handleNext = useCallback(() => {
    if (isLastStep) {
      handleComplete();
    } else {
      setDirection('forward');
      setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1));
    }
  }, [handleComplete, isLastStep, steps.length]);

  const handlePrevious = useCallback(() => {
    setDirection('backward');
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  }, []);

  const handleSkip = useCallback(() => {
    onClose();
  }, [onClose]);

  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  const handleStepClick = useCallback((index: number) => {
    setDirection(index > currentStep ? 'forward' : 'backward');
    setCurrentStep(index);
  }, [currentStep]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' && !isLastStep) {
        handleNext();
      } else if (e.key === 'ArrowLeft' && !isFirstStep) {
        handlePrevious();
      } else if (e.key === 'Escape') {
        handleClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleClose, handleNext, handlePrevious, isFirstStep, isLastStep, isOpen]);

  const slideVariants = {
    enter: (direction: 'forward' | 'backward') => ({
      x: direction === 'forward' ? 300 : -300,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: 'forward' | 'backward') => ({
      x: direction === 'forward' ? -300 : 300,
      opacity: 0,
    }),
  };

  return (
    <Modal2
      open={isOpen}
      onClose={handleClose}
      size="lg"
      showClose={false}
      className="overflow-hidden"
    >
      <div className="relative">
        {/* Close Button */}
        <button
          onClick={handleClose}
          className={cn(
            'absolute top-4 right-4 z-10',
            'p-2 rounded-lg',
            'text-neutral-500 hover:text-neutral-700',
            'dark:text-neutral-400 dark:hover:text-neutral-200',
            'hover:bg-neutral-100 dark:hover:bg-neutral-800',
            'transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-primary-500',
          )}
          aria-label="Close tour"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Progress Bar */}
        {showProgress && (
          <div className="absolute top-0 left-0 right-0 h-1 bg-neutral-200 dark:bg-neutral-700">
            <m.div
              className="h-full bg-primary-500"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        )}

        {/* Content */}
        <div className="pt-8 pb-6 px-6">
          <AnimatePresence mode="wait" custom={direction}>
            <m.div
              key={currentStep}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{
                x: { type: 'spring', stiffness: 300, damping: 30 },
                opacity: { duration: 0.2 },
              }}
              className="space-y-6"
            >
              {/* Icon */}
              <div className="flex justify-center">
                <div
                  className={cn(
                    'p-4 rounded-2xl',
                    'bg-primary-100 dark:bg-primary-900/30',
                  )}
                >
                  <step.icon className="h-12 w-12 text-primary-600 dark:text-primary-400" />
                </div>
              </div>

              {/* Title */}
              <div className="text-center">
                <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                  {step.title}
                </h2>
              </div>

              {/* Description */}
              <p className="text-center text-neutral-600 dark:text-neutral-400 text-lg">
                {step.description}
              </p>

              {/* Image/Screenshot */}
              {step.image && (
                <div className="rounded-lg overflow-hidden border border-neutral-200 dark:border-neutral-700">
                  <img
                    src={step.image}
                    alt={step.title}
                    className="w-full h-auto"
                  />
                </div>
              )}

              {/* Tips */}
              {step.tips && step.tips.length > 0 && (
                <div className="bg-neutral-50 dark:bg-neutral-800/50 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                    💡 Quick Tips
                  </h3>
                  <ul className="space-y-1.5">
                    {step.tips.map((tip, index) => (
                      <li
                        key={index}
                        className="text-sm text-neutral-600 dark:text-neutral-400 flex items-start gap-2"
                      >
                        <span className="text-primary-500 mt-0.5">•</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </m.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-200 dark:border-neutral-700 px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Step Indicators */}
            <div className="flex items-center gap-2">
              {steps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => handleStepClick(index)}
                  className={cn(
                    'h-2 rounded-full transition-all',
                    index === currentStep
                      ? 'w-8 bg-primary-500'
                      : 'w-2 bg-neutral-300 dark:bg-neutral-600 hover:bg-neutral-400 dark:hover:bg-neutral-500',
                  )}
                  aria-label={`Go to step ${index + 1}`}
                  aria-current={index === currentStep ? 'step' : undefined}
                />
              ))}
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center gap-3">
              {/* Skip Button */}
              {allowSkip && !isLastStep && (
                <button
                  onClick={handleSkip}
                  className={cn(
                    'px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'text-neutral-600 dark:text-neutral-400',
                    'hover:text-neutral-900 dark:hover:text-neutral-100',
                    'hover:bg-neutral-100 dark:hover:bg-neutral-800',
                    'transition-colors',
                  )}
                >
                  Skip Tour
                </button>
              )}

              {/* Previous Button */}
              {!isFirstStep && (
                <button
                  onClick={handlePrevious}
                  className={cn(
                    'px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'text-neutral-700 dark:text-neutral-300',
                    'bg-neutral-100 dark:bg-neutral-800',
                    'hover:bg-neutral-200 dark:hover:bg-neutral-700',
                    'transition-colors',
                    'flex items-center gap-2',
                  )}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </button>
              )}

              {/* Next/Finish Button */}
              <button
                onClick={handleNext}
                className={cn(
                  'px-6 py-2 rounded-lg',
                  'text-sm font-medium',
                  'text-white',
                  'bg-primary-600 hover:bg-primary-700',
                  'dark:bg-primary-500 dark:hover:bg-primary-600',
                  'transition-colors',
                  'flex items-center gap-2',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                  'dark:focus:ring-offset-neutral-900',
                )}
              >
                {isLastStep ? (
                  'Get Started'
                ) : (
                  <>
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Step Counter */}
          <div className="mt-3 text-center">
            <span className="text-xs text-neutral-500 dark:text-neutral-400">
              Step {currentStep + 1} of {steps.length}
            </span>
          </div>
        </div>
      </div>
    </Modal2>
  );
}

/**
 * Hook to manage feature tour state
 */
export function useFeatureTour() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasCompletedTour, setHasCompletedTour] = useState(false);

  useEffect(() => {
    // Check if user has completed tour
    if (typeof window !== 'undefined') {
      try {
        const completed = localStorage.getItem('feature-tour-completed');
        setHasCompletedTour(completed === 'true');
      } catch (error) {
        logger.error('Failed to check tour completion:', error);
      }
    }
  }, []);

  const openTour = useCallback(() => {
    setIsOpen(true);
  }, []);

  const closeTour = useCallback(() => {
    setIsOpen(false);
  }, []);

  const completeTour = useCallback(() => {
    setHasCompletedTour(true);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('feature-tour-completed', 'true');
      } catch (error) {
        logger.error('Failed to save tour completion:', error);
      }
    }
  }, []);

  const resetTour = useCallback(() => {
    setHasCompletedTour(false);
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('feature-tour-completed');
      } catch (error) {
        logger.error('Failed to reset tour:', error);
      }
    }
  }, []);

  return {
    isOpen,
    hasCompletedTour,
    openTour,
    closeTour,
    completeTour,
    resetTour,
  };
}
