/**
 * CompletionStep Component
 * 
 * Final step of onboarding wizard - completion screen with recommendations.
 * 
 * Features:
 * - Success animation
 * - Display first recommended jobs
 * - CTA buttons: "View Dashboard", "Browse Jobs"
 * - Option to retake onboarding in settings
 * - Celebration confetti effect
 * 
 * @module components/onboarding/steps/CompletionStep
 */

'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import {
  CheckCircle2,
  Sparkles,
  TrendingUp,
  MapPin,
  DollarSign,
  ArrowRight,
  Settings,
} from 'lucide-react';

import Button2 from '@/components/ui/Button2';
import { fadeInUp, staggerContainer, staggerItem, checkmarkVariants } from '@/lib/animations';
import apiClient from '@/lib/api/client';

import type { StepProps } from '../OnboardingWizard';

/**
 * Job interface (simplified)
 */
interface Job {
  id: number;
  title: string;
  company: {
    name: string;
    logo?: string;
  };
  location: string;
  salary?: {
    min: number;
    max: number;
    currency: string;
  };
  type: string;
  postedAt: string;
}

/**
 * CompletionStep Component
 */
const CompletionStep: React.FC<StepProps> = ({ data }) => {
  const router = useRouter();
  const [recommendedJobs, setRecommendedJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showConfetti, setShowConfetti] = useState(false);

  /**
   * Fetch recommended jobs
   */
  useEffect(() => {
    const fetchRecommendedJobs = async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.jobs.available({ limit: 3 });
        if (response.data) {
          setRecommendedJobs(response.data);
        }
      } catch (error) {
        console.error('Failed to fetch recommended jobs:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecommendedJobs();

    // Show confetti animation
    setShowConfetti(true);
    const timer = setTimeout(() => setShowConfetti(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  /**
   * Navigate to dashboard
   */
  const handleViewDashboard = () => {
    router.push('/dashboard');
  };

  /**
   * Navigate to jobs page
   */
  const handleBrowseJobs = () => {
    router.push('/jobs');
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Confetti effect */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {[...Array(50)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: '-10%',
                backgroundColor: [
                  '#3B82F6',
                  '#8B5CF6',
                  '#EC4899',
                  '#10B981',
                  '#F59E0B',
                ][Math.floor(Math.random() * 5)],
              }}
              initial={{ y: 0, opacity: 1, rotate: 0 }}
              animate={{
                y: window.innerHeight + 100,
                opacity: 0,
                rotate: Math.random() * 360,
              }}
              transition={{
                duration: 2 + Math.random() * 2,
                delay: Math.random() * 0.5,
                ease: 'easeIn',
              }}
            />
          ))}
        </div>
      )}

      {/* Success animation */}
      <motion.div variants={staggerItem} className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            type: 'spring',
            stiffness: 260,
            damping: 20,
            delay: 0.2,
          }}
          className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-success-500 to-emerald-500 mb-6 relative"
        >
          <motion.svg
            className="w-12 h-12 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <motion.path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
              variants={checkmarkVariants}
              initial="hidden"
              animate="visible"
            />
          </motion.svg>

          {/* Glow effect */}
          <div className="absolute inset-0 rounded-full bg-success-500 opacity-20 blur-xl animate-pulse" />
        </motion.div>

        <motion.h3
          variants={fadeInUp}
          className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mb-3"
        >
          You&apos;re all set! 🎉
        </motion.h3>
        <motion.p
          variants={fadeInUp}
          className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto"
        >
          Welcome to Career Copilot! Your profile is complete and we&apos;re ready to help you
          find your dream job.
        </motion.p>
      </motion.div>

      {/* Stats summary */}
      <motion.div
        variants={staggerItem}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        {[
          {
            icon: <CheckCircle2 className="h-5 w-5" />,
            label: 'Profile Complete',
            value: '100%',
            color: 'text-success-600 dark:text-success-400',
            bg: 'bg-success-100 dark:bg-success-900/30',
          },
          {
            icon: <Sparkles className="h-5 w-5" />,
            label: 'Skills Added',
            value: data.skills?.length || 0,
            color: 'text-purple-600 dark:text-purple-400',
            bg: 'bg-purple-100 dark:bg-purple-900/30',
          },
          {
            icon: <TrendingUp className="h-5 w-5" />,
            label: 'Job Matches',
            value: recommendedJobs.length,
            color: 'text-primary-600 dark:text-primary-400',
            bg: 'bg-primary-100 dark:bg-primary-900/30',
          },
        ].map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className="p-6 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700"
          >
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${stat.bg} ${stat.color}`}>
                {stat.icon}
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                  {stat.value}
                </p>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  {stat.label}
                </p>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Recommended jobs */}
      <motion.div variants={staggerItem} className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            Jobs we think you&apos;ll love
          </h4>
          {recommendedJobs.length > 0 && (
            <button
              onClick={handleBrowseJobs}
              className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium flex items-center gap-1"
            >
              View all
              <ArrowRight className="h-4 w-4" />
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="h-32 bg-neutral-100 dark:bg-neutral-800 rounded-xl animate-pulse"
              />
            ))}
          </div>
        ) : recommendedJobs.length > 0 ? (
          <div className="space-y-4">
            {recommendedJobs.map((job, index) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="p-6 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors cursor-pointer"
                onClick={() => router.push(`/jobs/${job.id}`)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h5 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                      {job.title}
                    </h5>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-3">
                      {job.company.name}
                    </p>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400">
                      <div className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        <span>{job.location}</span>
                      </div>
                      {job.salary && (
                        <div className="flex items-center gap-1">
                          <DollarSign className="h-4 w-4" />
                          <span>
                            {job.salary.currency}
                            {job.salary.min.toLocaleString()} -{' '}
                            {job.salary.max.toLocaleString()}
                          </span>
                        </div>
                      )}
                      <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded text-xs font-medium">
                        {job.type}
                      </span>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-neutral-400 flex-shrink-0" />
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
            <Sparkles className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400">
              We&apos;re finding the perfect jobs for you. Check back soon!
            </p>
          </div>
        )}
      </motion.div>

      {/* Action buttons */}
      <motion.div
        variants={staggerItem}
        className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6"
      >
        <Button2
          variant="primary"
          size="lg"
          onClick={handleViewDashboard}
          icon={<TrendingUp className="h-5 w-5" />}
          iconPosition="left"
          glow
          className="w-full sm:w-auto"
        >
          View Dashboard
        </Button2>
        <Button2
          variant="outline"
          size="lg"
          onClick={handleBrowseJobs}
          icon={<ArrowRight className="h-5 w-5" />}
          iconPosition="right"
          className="w-full sm:w-auto"
        >
          Browse Jobs
        </Button2>
      </motion.div>

      {/* Footer note */}
      <motion.div
        variants={staggerItem}
        className="text-center pt-6 border-t border-neutral-200 dark:border-neutral-700"
      >
        <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
          You can update your preferences anytime from settings
        </p>
        <button
          onClick={() => router.push('/settings/profile')}
          className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium inline-flex items-center gap-1"
        >
          <Settings className="h-4 w-4" />
          Go to Settings
        </button>
      </motion.div>
    </motion.div>
  );
};

export default CompletionStep;
