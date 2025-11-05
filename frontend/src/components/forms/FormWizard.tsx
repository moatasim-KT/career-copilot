/**
 * Multi-Step Form Wizard Component
 * A reusable component for creating multi-step forms with progress tracking
 */

'use client';

import React, { useState, createContext, useContext, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ============================================================================
// Types
// ============================================================================

export interface WizardStep {
    id: string;
    title: string;
    description?: string;
    optional?: boolean;
    validate?: (data: any) => Promise<boolean> | boolean;
}

interface WizardContextValue {
    currentStep: number;
    totalSteps: number;
    isFirstStep: boolean;
    isLastStep: boolean;
    canGoNext: boolean;
    canGoPrevious: boolean;
    formData: Record<string, any>;
    steps: WizardStep[];
    goToStep: (step: number) => void;
    nextStep: () => Promise<void>;
    previousStep: () => void;
    updateFormData: (data: Record<string, any>) => void;
    isStepValid: (stepIndex: number) => boolean;
    isLoading: boolean;
}

// ============================================================================
// Context
// ============================================================================

const WizardContext = createContext<WizardContextValue | null>(null);

export function useWizard() {
    const context = useContext(WizardContext);
    if (!context) {
        throw new Error('useWizard must be used within a FormWizard');
    }
    return context;
}

// ============================================================================
// Wizard Provider
// ============================================================================

interface FormWizardProps {
    children: ReactNode;
    steps: WizardStep[];
    initialData?: Record<string, any>;
    onComplete: (data: Record<string, any>) => void | Promise<void>;
    onStepChange?: (step: number) => void;
    className?: string;
}

export function FormWizard({
    children,
    steps,
    initialData = {},
    onComplete,
    onStepChange,
    className = '',
}: FormWizardProps) {
    const [currentStep, setCurrentStep] = useState(0);
    const [formData, setFormData] = useState(initialData);
    const [visitedSteps, setVisitedSteps] = useState<Set<number>>(new Set([0]));
    const [isLoading, setIsLoading] = useState(false);

    const totalSteps = steps.length;
    const isFirstStep = currentStep === 0;
    const isLastStep = currentStep === totalSteps - 1;

    const updateFormData = (data: Record<string, any>) => {
        setFormData(prev => ({ ...prev, ...data }));
    };

    const isStepValid = (stepIndex: number): boolean => {
        const step = steps[stepIndex];
        if (!step || step.optional) return true;

        // You can implement custom validation logic here
        // For now, just check if the step has been visited
        return visitedSteps.has(stepIndex);
    };

    const goToStep = (step: number) => {
        if (step >= 0 && step < totalSteps) {
            setCurrentStep(step);
            setVisitedSteps(prev => new Set(prev).add(step));
            onStepChange?.(step);
        }
    };

    const nextStep = async () => {
        const step = steps[currentStep];

        // Validate current step
        if (step.validate) {
            setIsLoading(true);
            try {
                const isValid = await step.validate(formData);
                if (!isValid) {
                    setIsLoading(false);
                    return;
                }
            } catch (error) {
                console.error('Step validation error:', error);
                setIsLoading(false);
                return;
            }
            setIsLoading(false);
        }

        if (isLastStep) {
            // Complete the wizard
            setIsLoading(true);
            try {
                await onComplete(formData);
            } catch (error) {
                console.error('Form completion error:', error);
            } finally {
                setIsLoading(false);
            }
        } else {
            goToStep(currentStep + 1);
        }
    };

    const previousStep = () => {
        if (!isFirstStep) {
            goToStep(currentStep - 1);
        }
    };

    const canGoNext = !isLoading && (steps[currentStep]?.optional || isStepValid(currentStep));
    const canGoPrevious = !isLoading && !isFirstStep;

    const value: WizardContextValue = {
        currentStep,
        totalSteps,
        isFirstStep,
        isLastStep,
        canGoNext,
        canGoPrevious,
        formData,
        steps,
        goToStep,
        nextStep,
        previousStep,
        updateFormData,
        isStepValid,
        isLoading,
    };

    return (
        <WizardContext.Provider value={value}>
            <div className={`form-wizard ${className}`}>
                {children}
            </div>
        </WizardContext.Provider>
    );
}

// ============================================================================
// Wizard Components
// ============================================================================

/**
 * Progress indicator showing current step
 */
export function WizardProgress({ className = '' }: { className?: string }) {
    const { currentStep, totalSteps, steps, goToStep, isStepValid } = useWizard();

    return (
        <div className={`wizard-progress ${className}`}>
            <div className="flex items-center justify-between">
                {steps.map((step, index) => {
                    const isActive = index === currentStep;
                    const isCompleted = index < currentStep;
                    const isValid = isStepValid(index);
                    const canClick = isCompleted || isValid;

                    return (
                        <React.Fragment key={step.id}>
                            <div className="flex flex-col items-center flex-1">
                                <button
                                    onClick={() => canClick && goToStep(index)}
                                    disabled={!canClick}
                                    className={`
                    flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all
                    ${isActive ? 'border-blue-600 bg-blue-600 text-white' : ''}
                    ${isCompleted ? 'border-green-600 bg-green-600 text-white' : ''}
                    ${!isActive && !isCompleted ? 'border-gray-300 bg-white text-gray-500' : ''}
                    ${canClick ? 'cursor-pointer hover:scale-105' : 'cursor-not-allowed opacity-50'}
                  `}
                                >
                                    {isCompleted ? (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : (
                                        <span className="text-sm font-medium">{index + 1}</span>
                                    )}
                                </button>
                                <div className="mt-2 text-xs font-medium text-center">
                                    <div className={isActive ? 'text-blue-600' : 'text-gray-600'}>
                                        {step.title}
                                    </div>
                                    {step.optional && (
                                        <div className="text-gray-400 text-xs">(Optional)</div>
                                    )}
                                </div>
                            </div>

                            {index < steps.length - 1 && (
                                <div className="flex-1 h-0.5 mx-4 bg-gray-300 relative top-[-20px]">
                                    <div
                                        className={`h-full transition-all duration-300 ${index < currentStep ? 'bg-green-600' : 'bg-gray-300'
                                            }`}
                                    />
                                </div>
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
        </div>
    );
}

/**
 * Container for wizard step content
 */
interface WizardStepsProps {
    children: ReactNode;
    className?: string;
}

export function WizardSteps({ children, className = '' }: WizardStepsProps) {
    const { currentStep } = useWizard();
    const childrenArray = React.Children.toArray(children);

    return (
        <div className={`wizard-steps ${className}`}>
            <AnimatePresence mode="wait">
                <motion.div
                    key={currentStep}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                >
                    {childrenArray[currentStep]}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}

/**
 * Individual wizard step
 */
interface WizardStepProps {
    children: ReactNode;
    className?: string;
}

export function WizardStep({ children, className = '' }: WizardStepProps) {
    return <div className={`wizard-step ${className}`}>{children}</div>;
}

/**
 * Navigation buttons for wizard
 */
export function WizardNavigation({ className = '' }: { className?: string }) {
    const {
        isFirstStep,
        isLastStep,
        canGoNext,
        canGoPrevious,
        nextStep,
        previousStep,
        isLoading,
    } = useWizard();

    return (
        <div className={`wizard-navigation flex justify-between ${className}`}>
            <button
                onClick={previousStep}
                disabled={!canGoPrevious}
                className={`
          px-6 py-2 rounded-lg font-medium transition-all
          ${canGoPrevious
                        ? 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }
        `}
            >
                Previous
            </button>

            <button
                onClick={nextStep}
                disabled={!canGoNext}
                className={`
          px-6 py-2 rounded-lg font-medium transition-all
          ${canGoNext
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }
          ${isLoading ? 'opacity-50 cursor-wait' : ''}
        `}
            >
                {isLoading ? (
                    <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Processing...
                    </span>
                ) : isLastStep ? (
                    'Complete'
                ) : (
                    'Next'
                )}
            </button>
        </div>
    );
}
