/**
 * PreferencesStep Component
 * 
 * Fourth step of onboarding wizard - job preferences and search criteria.
 * 
 * Features:
 * - Preferred job titles (multi-select)
 * - Preferred locations (city, state, or remote)
 * - Salary expectations (range slider)
 * - Work arrangement: Remote, Hybrid, On-site
 * - Company size preference (optional)
 * - Industry preference (optional)
 * 
 * @module components/onboarding/steps/PreferencesStep
 */

'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Briefcase,
  MapPin,
  DollarSign,
  Home,
  Building2,
  TrendingUp,
  Check,
} from 'lucide-react';

import Input2 from '@/components/ui/Input2';
import MultiSelect2 from '@/components/ui/MultiSelect2';
import Select2 from '@/components/ui/Select2';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations';
import { cn } from '@/lib/utils';
import type { StepProps } from '../OnboardingWizard';

/**
 * Job title options
 */
const jobTitleOptions = [
  { value: 'frontend-developer', label: 'Frontend Developer' },
  { value: 'backend-developer', label: 'Backend Developer' },
  { value: 'full-stack-developer', label: 'Full-Stack Developer' },
  { value: 'mobile-developer', label: 'Mobile Developer' },
  { value: 'devops-engineer', label: 'DevOps Engineer' },
  { value: 'data-scientist', label: 'Data Scientist' },
  { value: 'data-engineer', label: 'Data Engineer' },
  { value: 'ml-engineer', label: 'Machine Learning Engineer' },
  { value: 'product-manager', label: 'Product Manager' },
  { value: 'ui-ux-designer', label: 'UI/UX Designer' },
  { value: 'qa-engineer', label: 'QA Engineer' },
  { value: 'security-engineer', label: 'Security Engineer' },
];

/**
 * Work arrangement options
 */
const workArrangementOptions = [
  {
    value: 'remote',
    label: 'Remote',
    description: 'Work from anywhere',
    icon: <Home className="h-5 w-5" />,
  },
  {
    value: 'hybrid',
    label: 'Hybrid',
    description: 'Mix of remote and office',
    icon: <Building2 className="h-5 w-5" />,
  },
  {
    value: 'on-site',
    label: 'On-site',
    description: 'Work from office',
    icon: <Building2 className="h-5 w-5" />,
  },
];

/**
 * Company size options
 */
const companySizeOptions = [
  { value: '1-10', label: '1-10 employees (Startup)' },
  { value: '11-50', label: '11-50 employees (Small)' },
  { value: '51-200', label: '51-200 employees (Medium)' },
  { value: '201-500', label: '201-500 employees (Large)' },
  { value: '501-1000', label: '501-1000 employees (Enterprise)' },
  { value: '1000+', label: '1000+ employees (Corporation)' },
];

/**
 * Industry options
 */
const industryOptions = [
  { value: 'fintech', label: 'Fintech' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'saas', label: 'SaaS' },
  { value: 'gaming', label: 'Gaming' },
  { value: 'edtech', label: 'EdTech' },
  { value: 'ai-ml', label: 'AI/ML' },
  { value: 'cybersecurity', label: 'Cybersecurity' },
  { value: 'blockchain', label: 'Blockchain' },
  { value: 'iot', label: 'IoT' },
];

/**
 * PreferencesStep Component
 */
const PreferencesStep: React.FC<StepProps> = ({ data, onChange }) => {
  const [preferences, setPreferences] = useState({
    preferredJobTitles: data.preferredJobTitles || [],
    preferredLocations: data.preferredLocations || '',
    salaryMin: data.salaryMin || 50000,
    salaryMax: data.salaryMax || 150000,
    workArrangement: data.workArrangement || [],
    companySize: data.companySize || '',
    industry: data.industry || [],
  });

  // Auto-save on change
  useEffect(() => {
    onChange(preferences);
  }, [preferences, onChange]);

  /**
   * Update preference
   */
  const updatePreference = (key: string, value: any) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
  };

  /**
   * Toggle work arrangement
   */
  const toggleWorkArrangement = (value: string) => {
    const current = preferences.workArrangement;
    const updated = current.includes(value)
      ? current.filter((v: string) => v !== value)
      : [...current, value];
    updatePreference('workArrangement', updated);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
          <Briefcase className="h-8 w-8 text-primary-600 dark:text-primary-400" />
        </div>
        <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          What's your ideal job?
        </h3>
        <p className="text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
          Tell us about your preferences so we can find the perfect opportunities for you.
        </p>
      </motion.div>

      {/* Form fields */}
      <motion.div variants={staggerItem} className="space-y-6">
        {/* Preferred job titles */}
        <div>
          <MultiSelect2
            label="Preferred Job Titles"
            options={jobTitleOptions}
            value={preferences.preferredJobTitles}
            onChange={(value) => updatePreference('preferredJobTitles', value)}
            placeholder="Select job titles you're interested in"
            prefixIcon={<Briefcase className="h-4 w-4" />}
            helperText="Select at least one job title"
          />
        </div>

        {/* Preferred locations */}
        <div>
          <Input2
            label="Preferred Locations"
            placeholder="e.g., Berlin, Munich, Remote"
            value={preferences.preferredLocations}
            onChange={(e) => updatePreference('preferredLocations', e.target.value)}
            prefixIcon={<MapPin className="h-4 w-4" />}
            helperText="Enter cities, countries, or 'Remote'"
          />
        </div>

        {/* Salary expectations */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
            Salary Expectations (Annual)
          </label>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Input2
                  type="number"
                  placeholder="Min"
                  value={preferences.salaryMin}
                  onChange={(e) => updatePreference('salaryMin', parseInt(e.target.value) || 0)}
                  prefixIcon={<DollarSign className="h-4 w-4" />}
                />
              </div>
              <span className="text-neutral-500 dark:text-neutral-400">to</span>
              <div className="flex-1">
                <Input2
                  type="number"
                  placeholder="Max"
                  value={preferences.salaryMax}
                  onChange={(e) => updatePreference('salaryMax', parseInt(e.target.value) || 0)}
                  prefixIcon={<DollarSign className="h-4 w-4" />}
                />
              </div>
            </div>

            {/* Salary range display */}
            <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-lg">
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Expected salary range:
              </p>
              <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mt-1">
                €{preferences.salaryMin.toLocaleString()} - €
                {preferences.salaryMax.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Work arrangement */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
            Work Arrangement
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {workArrangementOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => toggleWorkArrangement(option.value)}
                className={cn(
                  'p-4 rounded-lg border-2 transition-all text-left',
                  preferences.workArrangement.includes(option.value)
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                    : 'border-neutral-200 dark:border-neutral-700 hover:border-primary-300 dark:hover:border-primary-700'
                )}
              >
                <div className="flex items-start justify-between mb-2">
                  <div
                    className={cn(
                      'p-2 rounded-lg',
                      preferences.workArrangement.includes(option.value)
                        ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-600 dark:text-primary-400'
                        : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'
                    )}
                  >
                    {option.icon}
                  </div>
                  {preferences.workArrangement.includes(option.value) && (
                    <Check className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  )}
                </div>
                <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                  {option.label}
                </h4>
                <p className="text-xs text-neutral-600 dark:text-neutral-400">
                  {option.description}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Company size (optional) */}
        <div>
          <Select2
            label="Company Size (Optional)"
            options={companySizeOptions}
            value={preferences.companySize}
            onChange={(e) => updatePreference('companySize', e.target.value)}
            placeholder="Select company size preference"
            prefixIcon={<Building2 className="h-4 w-4" />}
          />
        </div>

        {/* Industry (optional) */}
        <div>
          <MultiSelect2
            label="Industry (Optional)"
            options={industryOptions}
            value={preferences.industry}
            onChange={(value) => updatePreference('industry', value)}
            placeholder="Select industries you're interested in"
            prefixIcon={<TrendingUp className="h-4 w-4" />}
          />
        </div>
      </motion.div>

      {/* Summary */}
      {preferences.preferredJobTitles.length > 0 && (
        <motion.div
          variants={staggerItem}
          className="p-6 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 rounded-xl border border-primary-200 dark:border-primary-800"
        >
          <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-3">
            Your Job Search Summary
          </h4>
          <div className="space-y-2 text-sm text-neutral-700 dark:text-neutral-300">
            <p>
              Looking for <strong>{preferences.preferredJobTitles.length}</strong> job
              title(s)
            </p>
            {preferences.preferredLocations && (
              <p>
                in <strong>{preferences.preferredLocations}</strong>
              </p>
            )}
            <p>
              with salary range{' '}
              <strong>
                €{preferences.salaryMin.toLocaleString()} - €
                {preferences.salaryMax.toLocaleString()}
              </strong>
            </p>
            {preferences.workArrangement.length > 0 && (
              <p>
                preferring <strong>{preferences.workArrangement.join(', ')}</strong> work
              </p>
            )}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default PreferencesStep;
