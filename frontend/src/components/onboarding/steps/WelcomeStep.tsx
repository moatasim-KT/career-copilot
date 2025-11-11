/**
 * WelcomeStep Component
 * 
 * First step of onboarding wizard - collects basic profile information.
 * 
 * Features:
 * - Profile photo upload (optional)
 * - Name and email (pre-filled if signed in)
 * - Job title/role
 * - Years of experience
 * - Form validation with Zod
 * - Auto-save on change
 * 
 * @module components/onboarding/steps/WelcomeStep
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion } from 'framer-motion';
import { User, Mail, Briefcase, Calendar, Upload, X, Check } from 'lucide-react';
import { toast } from 'react-hot-toast';

import Input2 from '@/components/ui/Input2';
import Select2 from '@/components/ui/Select2';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations';
import { cn } from '@/lib/utils';
import type { StepProps } from '../OnboardingWizard';

/**
 * Form validation schema
 */
const welcomeSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(100, 'Name is too long'),
  email: z.string().email('Please enter a valid email address'),
  jobTitle: z.string().min(2, 'Job title is required').max(100, 'Job title is too long'),
  yearsOfExperience: z.string().min(1, 'Please select your experience level'),
  profilePhoto: z.string().optional(),
});

type WelcomeFormData = z.infer<typeof welcomeSchema>;

/**
 * Experience level options
 */
const experienceOptions = [
  { value: '0-1', label: '0-1 years (Entry Level)' },
  { value: '1-3', label: '1-3 years (Junior)' },
  { value: '3-5', label: '3-5 years (Mid-Level)' },
  { value: '5-10', label: '5-10 years (Senior)' },
  { value: '10+', label: '10+ years (Expert/Lead)' },
];

/**
 * WelcomeStep Component
 */
const WelcomeStep: React.FC<StepProps> = ({ data, onChange }) => {
  const [profilePhoto, setProfilePhoto] = useState<string | null>(data.profilePhoto || null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const {
    register,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<WelcomeFormData>({
    resolver: zodResolver(welcomeSchema),
    mode: 'onChange',
    defaultValues: {
      name: data.name || '',
      email: data.email || '',
      jobTitle: data.jobTitle || '',
      yearsOfExperience: data.yearsOfExperience || '',
      profilePhoto: data.profilePhoto || '',
    },
  });

  // Watch form changes and auto-save
  const formValues = watch();

  useEffect(() => {
    if (isValid) {
      onChange(formValues);
    }
  }, [formValues, isValid, onChange]);

  /**
   * Handle profile photo upload
   */
  const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image size must be less than 5MB');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 100);

      // Convert to base64 for preview (in production, upload to server)
      const reader = new FileReader();
      reader.onloadend = () => {
        clearInterval(progressInterval);
        setUploadProgress(100);
        const base64 = reader.result as string;
        setProfilePhoto(base64);
        setValue('profilePhoto', base64);
        setIsUploading(false);
        toast.success('Photo uploaded successfully');
      };
      reader.onerror = () => {
        clearInterval(progressInterval);
        setIsUploading(false);
        toast.error('Failed to upload photo');
      };
      reader.readAsDataURL(file);
    } catch (error) {
      setIsUploading(false);
      console.error('Photo upload error:', error);
      toast.error('Failed to upload photo');
    }
  };

  /**
   * Remove profile photo
   */
  const handlePhotoRemove = () => {
    setProfilePhoto(null);
    setValue('profilePhoto', '');
    toast.success('Photo removed');
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Welcome message */}
      <motion.div variants={staggerItem} className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
          <User className="h-8 w-8 text-primary-600 dark:text-primary-400" />
        </div>
        <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          Welcome to Career Copilot! 👋
        </h3>
        <p className="text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
          Your AI-powered copilot for navigating the European tech job market. 
          Let's build your profile to find your dream job.
        </p>
      </motion.div>

      {/* Profile photo upload */}
      <motion.div variants={staggerItem} className="flex flex-col items-center">
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
          Profile Photo (Optional)
        </label>
        
        <div className="relative">
          {profilePhoto ? (
            <div className="relative group">
              <img
                src={profilePhoto}
                alt="Profile"
                className="w-32 h-32 rounded-full object-cover border-4 border-neutral-200 dark:border-neutral-700"
              />
              <button
                type="button"
                onClick={handlePhotoRemove}
                className="absolute -top-2 -right-2 p-2 bg-error-500 text-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label="Remove photo"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <label
              className={cn(
                'flex flex-col items-center justify-center w-32 h-32 rounded-full',
                'border-2 border-dashed border-neutral-300 dark:border-neutral-600',
                'hover:border-primary-500 dark:hover:border-primary-400',
                'cursor-pointer transition-colors',
                isUploading && 'pointer-events-none opacity-50'
              )}
            >
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                className="hidden"
                disabled={isUploading}
              />
              {isUploading ? (
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2" />
                  <span className="text-xs text-neutral-600 dark:text-neutral-400">
                    {uploadProgress}%
                  </span>
                </div>
              ) : (
                <>
                  <Upload className="h-8 w-8 text-neutral-400 mb-2" />
                  <span className="text-xs text-neutral-600 dark:text-neutral-400">
                    Upload photo
                  </span>
                </>
              )}
            </label>
          )}
        </div>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
          JPG, PNG or GIF (max 5MB)
        </p>
      </motion.div>

      {/* Form fields */}
      <motion.div variants={staggerItem} className="space-y-6">
        <Input2
          label="Full Name"
          placeholder="John Doe"
          prefixIcon={<User className="h-4 w-4" />}
          required
          error={errors.name?.message}
          {...register('name')}
        />

        <Input2
          label="Email Address"
          type="email"
          placeholder="john.doe@example.com"
          prefixIcon={<Mail className="h-4 w-4" />}
          required
          error={errors.email?.message}
          helperText="We'll use this to send you job recommendations"
          {...register('email')}
        />

        <Input2
          label="Current Job Title / Role"
          placeholder="e.g., Senior Frontend Developer"
          prefixIcon={<Briefcase className="h-4 w-4" />}
          required
          error={errors.jobTitle?.message}
          helperText="What role are you currently in or seeking?"
          {...register('jobTitle')}
        />

        <Select2
          label="Years of Experience"
          options={experienceOptions}
          placeholder="Select your experience level"
          prefixIcon={<Calendar className="h-4 w-4" />}
          required
          error={errors.yearsOfExperience?.message}
          {...register('yearsOfExperience')}
        />
      </motion.div>

      {/* Value proposition */}
      <motion.div
        variants={staggerItem}
        className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-neutral-200 dark:border-neutral-700"
      >
        {[
          {
            icon: <Check className="h-5 w-5" />,
            title: 'AI-Powered Matching',
            description: 'Get personalized job recommendations',
          },
          {
            icon: <Check className="h-5 w-5" />,
            title: 'Track Applications',
            description: 'Manage all your applications in one place',
          },
          {
            icon: <Check className="h-5 w-5" />,
            title: 'Career Insights',
            description: 'Get analytics on your job search progress',
          },
        ].map((feature, index) => (
          <div
            key={index}
            className="flex items-start gap-3 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-800/50"
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-success-100 dark:bg-success-900/30 flex items-center justify-center text-success-600 dark:text-success-400">
              {feature.icon}
            </div>
            <div>
              <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {feature.title}
              </h4>
              <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                {feature.description}
              </p>
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
};

export default WelcomeStep;
