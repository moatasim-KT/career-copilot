/**
 * FeatureTourStep Component
 * 
 * Fifth step of onboarding wizard - interactive feature tour.
 * 
 * Features:
 * - Interactive tour of key features
 * - Highlight dashboard, jobs, applications
 * - Show command palette (⌘K)
 * - Show notification center
 * - Animated pointers and tooltips
 * - Navigation between tour steps
 * 
 * @module components/onboarding/steps/FeatureTourStep
 */

'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Bell,
  Command,
  Search,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

import Button2 from '@/components/ui/Button2';
import { fadeInUp, slideVariants } from '@/lib/animations';
import { cn } from '@/lib/utils';
import type { StepProps } from '../OnboardingWizard';

/**
 * Tour step interface
 */
interface TourStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  features: string[];
  image?: string;
  gradient: string;
}

/**
 * Tour steps
 */
const tourSteps: TourStep[] = [
  {
    id: 'dashboard',
    title: 'Your Personal Dashboard',
    description:
      'Get a bird\'s-eye view of your job search progress with real-time analytics and insights.',
    icon: <LayoutDashboard className="h-8 w-8" />,
    features: [
      'Track application status at a glance',
      'View upcoming interviews and deadlines',
      'Monitor your job search metrics',
      'Get personalized recommendations',
    ],
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'jobs',
    title: 'AI-Powered Job Matching',
    description:
      'Discover opportunities tailored to your skills and preferences with our intelligent matching algorithm.',
    icon: <Briefcase className="h-8 w-8" />,
    features: [
      'Smart job recommendations based on your profile',
      'Advanced search and filtering options',
      'Save jobs to review later',
      'Get notified about new matches',
    ],
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    id: 'applications',
    title: 'Application Tracking',
    description:
      'Manage all your job applications in one place with our comprehensive tracking system.',
    icon: <FileText className="h-8 w-8" />,
    features: [
      'Track application status and progress',
      'Set reminders for follow-ups',
      'Store notes and interview feedback',
      'Visualize your application pipeline',
    ],
    gradient: 'from-green-500 to-emerald-500',
  },
  {
    id: 'command-palette',
    title: 'Command Palette (⌘K)',
    description:
      'Navigate faster with keyboard shortcuts. Press ⌘K (or Ctrl+K) to access any feature instantly.',
    icon: <Command className="h-8 w-8" />,
    features: [
      'Quick navigation to any page',
      'Search jobs and applications',
      'Execute actions with keyboard',
      'Access recent items',
    ],
    gradient: 'from-orange-500 to-red-500',
  },
  {
    id: 'analytics',
    title: 'Career Insights',
    description:
      'Gain valuable insights into your job search with detailed analytics and visualizations.',
    icon: <BarChart3 className="h-8 w-8" />,
    features: [
      'Track application success rates',
      'Analyze response times',
      'Identify trending skills',
      'Compare salary ranges',
    ],
    gradient: 'from-indigo-500 to-purple-500',
  },
  {
    id: 'notifications',
    title: 'Stay Updated',
    description:
      'Never miss an opportunity with real-time notifications and alerts.',
    icon: <Bell className="h-8 w-8" />,
    features: [
      'Get notified about new job matches',
      'Receive application status updates',
      'Set custom notification preferences',
      'Enable browser push notifications',
    ],
    gradient: 'from-pink-500 to-rose-500',
  },
];

/**
 * FeatureTourStep Component
 */
const FeatureTourStep: React.FC<StepProps> = ({ data, onChange }) => {
  const [currentTourStep, setCurrentTourStep] = useState(0);

  const currentStep = tourSteps[currentTourStep];
  const isFirstStep = currentTourStep === 0;
  const isLastStep = currentTourStep === tourSteps.length - 1;

  /**
   * Navigate to next tour step
   */
  const handleNext = () => {
    if (!isLastStep) {
      setCurrentTourStep(currentTourStep + 1);
    }
  };

  /**
   * Navigate to previous tour step
   */
  const handlePrevious = () => {
    if (!isFirstStep) {
      setCurrentTourStep(currentTourStep - 1);
    }
  };

  /**
   * Jump to specific step
   */
  const handleJumpTo = (index: number) => {
    setCurrentTourStep(index);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-purple-500 mb-4">
          <Sparkles className="h-8 w-8 text-white" />
        </div>
        <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          Discover Career Copilot
        </h3>
        <p className="text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
          Let's take a quick tour of the key features that will help you land your dream job.
        </p>
      </div>

      {/* Progress indicators */}
      <div className="flex items-center justify-center gap-2">
        {tourSteps.map((step, index) => (
          <button
            key={step.id}
            onClick={() => handleJumpTo(index)}
            className={cn(
              'h-2 rounded-full transition-all',
              index === currentTourStep
                ? 'w-8 bg-primary-600'
                : index < currentTourStep
                ? 'w-2 bg-success-500'
                : 'w-2 bg-neutral-300 dark:bg-neutral-700'
            )}
            aria-label={`Go to ${step.title}`}
          />
        ))}
      </div>

      {/* Tour content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentTourStep}
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={slideVariants.right}
          className="space-y-6"
        >
          {/* Feature card */}
          <div
            className={cn(
              'relative overflow-hidden rounded-2xl p-8 text-white',
              'bg-gradient-to-br',
              currentStep.gradient
            )}
          >
            {/* Background pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute inset-0" style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
              }} />
            </div>

            {/* Content */}
            <div className="relative">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm mb-4">
                {currentStep.icon}
              </div>

              <h4 className="text-2xl font-bold mb-3">{currentStep.title}</h4>
              <p className="text-white/90 text-lg mb-6">{currentStep.description}</p>

              {/* Features list */}
              <div className="space-y-3">
                {currentStep.features.map((feature, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center mt-0.5">
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </div>
                    <span className="text-white/90">{feature}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          {/* Keyboard shortcut hint */}
          {currentStep.id === 'command-palette' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="p-6 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl border border-neutral-200 dark:border-neutral-700"
            >
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-neutral-900 dark:bg-neutral-700 flex items-center justify-center">
                  <Command className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1">
                  <h5 className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                    Try it now!
                  </h5>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    Press{' '}
                    <kbd className="px-2 py-1 bg-neutral-200 dark:bg-neutral-700 rounded text-xs font-mono">
                      ⌘K
                    </kbd>{' '}
                    or{' '}
                    <kbd className="px-2 py-1 bg-neutral-200 dark:bg-neutral-700 rounded text-xs font-mono">
                      Ctrl+K
                    </kbd>{' '}
                    to open the command palette
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4">
        <Button2
          variant="ghost"
          onClick={handlePrevious}
          disabled={isFirstStep}
          icon={<ChevronLeft className="h-4 w-4" />}
          iconPosition="left"
        >
          Previous
        </Button2>

        <div className="text-sm text-neutral-600 dark:text-neutral-400">
          {currentTourStep + 1} of {tourSteps.length}
        </div>

        <Button2
          variant="primary"
          onClick={handleNext}
          disabled={isLastStep}
          icon={<ChevronRight className="h-4 w-4" />}
          iconPosition="right"
        >
          {isLastStep ? 'Finish Tour' : 'Next'}
        </Button2>
      </div>
    </div>
  );
};

export default FeatureTourStep;
