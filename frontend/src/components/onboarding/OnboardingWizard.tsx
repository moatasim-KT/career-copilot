/**
 * OnboardingWizard Component
 * 
 * Multi-step wizard for user onboarding with progress tracking,
 * backend persistence, and resume functionality.
 * 
 * Features:
 * - Multi-step wizard with smooth transitions
 * - Progress indicator
 * - Save progress to backend after each step
 * - Resume from last incomplete step
 * - Skip individual steps or entire onboarding
 * - Keyboard navigation support
 * 
 * @module components/onboarding/OnboardingWizard
 */

'use client';

import { ChevronLeft, ChevronRight, X, Check } from 'lucide-react';
import React, { useState, useReducer, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

import Button2 from '@/components/ui/Button2';
import Modal2 from '@/components/ui/Modal2';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { slideVariants } from '@/lib/animations';
import apiClient from '@/lib/api/client';
import { logger } from '@/lib/logger';
import { AnimatePresence, m } from '@/lib/motion';

import CompletionStep from './steps/CompletionStep';
import FeatureTourStep from './steps/FeatureTourStep';
import PreferencesStep from './steps/PreferencesStep';
import ResumeStep from './steps/ResumeStep';
import SkillsStep from './steps/SkillsStep';
import WelcomeStep from './steps/WelcomeStep';


/**
 * Step configuration
 */
interface StepConfig {
  id: string;
  title: string;
  description: string;
  component: React.ComponentType<StepProps>;
  optional: boolean;
  skippable: boolean;
}

/**
 * Step component props
 */
export interface StepProps {
  data: any;
  onChange: (data: any) => void;
  onNext?: () => void;
  onBack?: () => void;
  onSkip?: () => void;
}

/**
 * Onboarding state
 */
type OnboardingState = {
  [key: string]: any;
};

/**
 * State actions
 */
type StateAction =
  | { type: 'UPDATE_STEP'; payload: { step: string; data: any } }
  | { type: 'SET_STATE'; payload: OnboardingState }
  | { type: 'MARK_COMPLETE'; payload: string }
  | { type: 'RESET' };

/**
 * Onboarding wizard props
 */
export interface OnboardingWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
  startStep?: number;
}

/**
 * Step definitions
 */
const steps: StepConfig[] = [
  {
    id: 'welcome',
    title: 'Welcome',
    description: 'Let\'s get started with your profile',
    component: WelcomeStep,
    optional: false,
    skippable: false,
  },
  {
    id: 'skills',
    title: 'Skills',
    description: 'Tell us about your expertise',
    component: SkillsStep,
    optional: false,
    skippable: true,
  },
  {
    id: 'resume',
    title: 'Resume',
    description: 'Upload your resume (optional)',
    component: ResumeStep,
    optional: true,
    skippable: true,
  },
  {
    id: 'preferences',
    title: 'Preferences',
    description: 'Set your job preferences',
    component: PreferencesStep,
    optional: false,
    skippable: true,
  },
  {
    id: 'tour',
    title: 'Feature Tour',
    description: 'Discover key features',
    component: FeatureTourStep,
    optional: true,
    skippable: true,
  },
  {
    id: 'completion',
    title: 'Complete',
    description: 'You\'re all set!',
    component: CompletionStep,
    optional: false,
    skippable: false,
  },
];

/**
 * Initial state
 */
const initialState: OnboardingState = {};

/**
 * State reducer
 */
function onboardingReducer(state: OnboardingState, action: StateAction): OnboardingState {
  switch (action.type) {
    case 'UPDATE_STEP':
      return {
        ...state,
        [action.payload.step]: {
          ...state[action.payload.step],
          ...action.payload.data,
        },
      };
    case 'SET_STATE':
      return action.payload;
    case 'MARK_COMPLETE':
      return {
        ...state,
        [action.payload]: {
          ...state[action.payload],
          completed: true,
          completedAt: new Date().toISOString(),
        },
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

/**
 * OnboardingWizard Component
 */
const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  isOpen,
  onClose,
  onComplete,
  startStep = 0,
}) => {
  const [currentStep, setCurrentStep] = useState(startStep);
  const [state, dispatch] = useReducer(onboardingReducer, initialState);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  /**
   * Load onboarding progress from backend
   */
  useEffect(() => {
    if (!isOpen) return;

    const fetchProgress = async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.user.getProfile();
        if (response.data?.onboarding) {
          dispatch({ type: 'SET_STATE', payload: response.data.onboarding });

          // Find first incomplete step
          const lastCompletedIndex = steps.findIndex(
            (step) => !response.data.onboarding?.[step.id]?.completed,
          );

          if (lastCompletedIndex !== -1 && lastCompletedIndex > startStep) {
            setCurrentStep(lastCompletedIndex);
          }
        }
      } catch (error) {
        logger.error('Failed to load onboarding progress:', error);
        toast.error('Failed to load your progress');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProgress();
  }, [isOpen, startStep]);

  /**
   * Save progress to backend
   */
  const saveProgress = useCallback(async (stepId: string, stepData: any) => {
    setIsSaving(true);
    try {
      const updatedState = {
        ...state,
        [stepId]: {
          ...state[stepId],
          ...stepData,
          completed: true,
          completedAt: new Date().toISOString(),
        },
      };

      const response = await apiClient.user.updateProfile({
        onboarding: updatedState,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      dispatch({ type: 'MARK_COMPLETE', payload: stepId });
      setHasUnsavedChanges(false);
      return true;
    } catch (error) {
      logger.error('Failed to save progress:', error);
      toast.error('Failed to save your progress');
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [state]);

  /**
   * Handle step data change
   */
  const handleStepChange = useCallback((data: any) => {
    dispatch({
      type: 'UPDATE_STEP',
      payload: { step: steps[currentStep].id, data },
    });
    setHasUnsavedChanges(true);
  }, [currentStep]);

  /**
   * Complete onboarding
   */
  const handleComplete = useCallback(async () => {
    try {
      await apiClient.user.updateProfile({
        onboardingCompleted: true,
        onboardingCompletedAt: new Date().toISOString(),
      });

      toast.success('Welcome to Career Copilot! 🎉');

      if (onComplete) {
        onComplete();
      }

      onClose();
    } catch (error) {
      logger.error('Failed to complete onboarding:', error);
      toast.error('Failed to complete onboarding');
    }
  }, [onComplete, onClose]);

  /**
   * Navigate to next step
   */
  const handleNext = useCallback(async () => {
    const currentStepConfig = steps[currentStep];
    const stepData = state[currentStepConfig.id] || {};

    // Save progress before moving to next step
    const saved = await saveProgress(currentStepConfig.id, stepData);
    if (!saved) return;

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Completed all steps
      handleComplete();
    }
  }, [currentStep, state, saveProgress, handleComplete]);

  /**
   * Navigate to previous step
   */
  const handleBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  }, [currentStep]);

  /**
   * Skip current step
   */
  const handleSkip = useCallback(async () => {
    const currentStepConfig = steps[currentStep];

    if (!currentStepConfig.skippable) {
      toast.error('This step cannot be skipped');
      return;
    }

    // Mark as skipped
    const stepData = {
      ...state[currentStepConfig.id],
      skipped: true,
      skippedAt: new Date().toISOString(),
    };

    await saveProgress(currentStepConfig.id, stepData);

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  }, [currentStep, state, saveProgress, handleComplete]);

  /**
   * Skip entire onboarding
   */
  const handleSkipAll = useCallback(async () => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to skip onboarding?',
      );
      if (!confirmed) return;
    }

    try {
      // Mark all steps as skipped
      const skippedState: OnboardingState = {};
      steps.forEach((step) => {
        skippedState[step.id] = {
          skipped: true,
          skippedAt: new Date().toISOString(),
        };
      });

      await apiClient.user.updateProfile({
        onboarding: skippedState,
        onboardingCompleted: true,
        onboardingCompletedAt: new Date().toISOString(),
      });

      toast.success('You can complete onboarding later from settings');
      onClose();
    } catch (error) {
      logger.error('Failed to skip onboarding:', error);
      toast.error('Failed to skip onboarding');
    }
  }, [hasUnsavedChanges, onClose]);

  /**
   * Handle close with unsaved changes warning
   */
  const handleClose = useCallback(() => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to close?',
      );
      if (!confirmed) return;
    }
    onClose();
  }, [hasUnsavedChanges, onClose]);

  /**
   * Keyboard navigation
   */
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't interfere with form inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      switch (e.key) {
        case 'ArrowRight':
          if (currentStep < steps.length - 1) {
            e.preventDefault();
            handleNext();
          }
          break;
        case 'ArrowLeft':
          if (currentStep > 0) {
            e.preventDefault();
            handleBack();
          }
          break;
        case 'Escape':
          e.preventDefault();
          handleClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStep, handleNext, handleBack, handleClose]);

  // Current step configuration
  const currentStepConfig = steps[currentStep];
  const CurrentStepComponent = currentStepConfig.component;
  const progress = ((currentStep + 1) / steps.length) * 100;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  return (
    <Modal2
      open={isOpen}
      onClose={handleClose}
      size="xl"
      showClose={false}
      className="max-h-[90vh] overflow-hidden"
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {currentStepConfig.title}
              </h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                {currentStepConfig.description}
              </p>
            </div>
            <button
              onClick={handleClose}
              className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
              aria-label="Close onboarding"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Progress bar */}
          <div className="space-y-2">
            <ProgressBar value={progress} className="h-2" />
            <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400">
              <span>
                Step {currentStep + 1} of {steps.length}
              </span>
              <span>{Math.round(progress)}% complete</span>
            </div>
          </div>

          {/* Step indicators */}
          <div className="flex items-center gap-2 mt-4">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`flex-1 h-1 rounded-full transition-all duration-300 ${index < currentStep
                  ? 'bg-success-500'
                  : index === currentStep
                    ? 'bg-primary-500'
                    : 'bg-neutral-200 dark:bg-neutral-700'
                  }`}
                title={step.title}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
                <p className="text-neutral-600 dark:text-neutral-400">Loading your progress...</p>
              </div>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              <m.div
                key={currentStep}
                initial="hidden"
                animate="visible"
                exit="exit"
                variants={slideVariants.right}
                className="min-h-[400px]"
              >
                <CurrentStepComponent
                  data={state[currentStepConfig.id] || {}}
                  onChange={handleStepChange}
                  onNext={handleNext}
                  onBack={handleBack}
                  onSkip={handleSkip}
                />
              </m.div>
            </AnimatePresence>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {!isFirstStep && (
                <Button2
                  variant="ghost"
                  onClick={handleBack}
                  disabled={isSaving}
                  icon={<ChevronLeft className="h-4 w-4" />}
                  iconPosition="left"
                >
                  Back
                </Button2>
              )}
              {currentStepConfig.skippable && !isLastStep && (
                <Button2
                  variant="ghost"
                  onClick={handleSkip}
                  disabled={isSaving}
                  className="text-neutral-600 dark:text-neutral-400"
                >
                  Skip this step
                </Button2>
              )}
            </div>

            <div className="flex items-center gap-2">
              {!isLastStep && (
                <Button2
                  variant="outline"
                  onClick={handleSkipAll}
                  disabled={isSaving}
                >
                  Skip onboarding
                </Button2>
              )}
              <Button2
                variant="primary"
                onClick={isLastStep ? handleComplete : handleNext}
                loading={isSaving}
                loadingText="Saving..."
                icon={
                  isLastStep ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )
                }
                iconPosition="right"
                glow
              >
                {isLastStep ? 'Complete' : 'Next'}
              </Button2>
            </div>
          </div>

          {/* Keyboard hints */}
          <div className="mt-3 text-xs text-neutral-500 dark:text-neutral-400 text-center">
            Use arrow keys to navigate • Press Esc to close
          </div>
        </div>
      </div>
    </Modal2>
  );
};

export default OnboardingWizard;
