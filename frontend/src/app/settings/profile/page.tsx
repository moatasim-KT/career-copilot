/**
 * Profile Settings Page
 * 
 * Allows users to edit their profile information including:
 * - Name, email, photo
 * - Job title, experience
 * - Skills
 * - Bio/summary
 */

'use client';

import { useState, useRef } from 'react';
import { User, Upload, Save, X, Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import Image from 'next/image';

import Button2 from '@/components/ui/Button2';
import Input2 from '@/components/ui/Input2';
import Textarea2 from '@/components/ui/Textarea2';
import Select2 from '@/components/ui/Select2';
import { MultiSelect2 } from '@/components/ui/MultiSelect2';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api/client';

interface ProfileData {
  name: string;
  email: string;
  photoUrl: string | null;
  jobTitle: string;
  experience: string;
  skills: string[];
  bio: string;
}

const experienceLevels = [
  { value: '0-1', label: '0-1 years' },
  { value: '1-3', label: '1-3 years' },
  { value: '3-5', label: '3-5 years' },
  { value: '5-10', label: '5-10 years' },
  { value: '10+', label: '10+ years' },
];

const popularSkills = [
  'JavaScript',
  'TypeScript',
  'React',
  'Node.js',
  'Python',
  'Java',
  'C++',
  'SQL',
  'MongoDB',
  'AWS',
  'Docker',
  'Kubernetes',
  'Git',
  'Agile',
  'REST APIs',
  'GraphQL',
  'Machine Learning',
  'Data Analysis',
  'UI/UX Design',
  'Project Management',
];

export default function ProfileSettingsPage() {
  const [profile, setProfile] = useState<ProfileData>({
    name: 'John Doe',
    email: 'john.doe@example.com',
    photoUrl: null,
    jobTitle: 'Software Engineer',
    experience: '3-5',
    skills: ['JavaScript', 'React', 'Node.js', 'TypeScript'],
    bio: 'Passionate software engineer with experience in full-stack development.',
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(profile.photoUrl);
  const [customSkill, setCustomSkill] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = (field: keyof ProfileData, value: any) => {
    setProfile(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handlePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('Image size must be less than 5MB');
        return;
      }

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result as string);
        setHasChanges(true);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemovePhoto = () => {
    setPhotoPreview(null);
    setProfile(prev => ({ ...prev, photoUrl: null }));
    setHasChanges(true);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAddCustomSkill = () => {
    if (customSkill.trim() && !profile.skills.includes(customSkill.trim())) {
      setProfile(prev => ({
        ...prev,
        skills: [...prev.skills, customSkill.trim()],
      }));
      setCustomSkill('');
      setHasChanges(true);
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setProfile(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s !== skill),
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);

    try {
      // In production, upload photo first if changed
      // const photoUrl = photoPreview ? await uploadPhoto(photoPreview) : profile.photoUrl;

      // Save profile to backend
      await apiClient.user.updateProfile({
        ...profile,
        photoUrl: photoPreview,
      });

      setHasChanges(false);
      
      // Show success message
      console.log('Profile saved successfully');
    } catch (error) {
      console.error('Failed to save profile:', error);
      // Show error message
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
          Profile Settings
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          Manage your personal information and professional details
        </p>
      </div>

      {/* Profile Photo */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
          Profile Photo
        </label>
        <div className="flex items-center gap-6">
          {/* Photo Preview */}
          <div className="relative">
            {photoPreview ? (
              <div className="relative w-24 h-24 rounded-full overflow-hidden border-2 border-neutral-200 dark:border-neutral-700">
                <Image
                  src={photoPreview}
                  alt="Profile photo"
                  fill
                  className="object-cover"
                />
                <button
                  onClick={handleRemovePhoto}
                  className="absolute inset-0 bg-black/50 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center"
                  aria-label="Remove photo"
                >
                  <X className="w-6 h-6 text-white" />
                </button>
              </div>
            ) : (
              <div className="w-24 h-24 rounded-full bg-neutral-200 dark:bg-neutral-700 flex items-center justify-center">
                <User className="w-12 h-12 text-neutral-400 dark:text-neutral-500" />
              </div>
            )}
          </div>

          {/* Upload Button */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handlePhotoUpload}
              className="hidden"
              id="photo-upload"
            />
            <Button2
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="w-4 h-4 mr-2" />
              Upload Photo
            </Button2>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
              JPG, PNG or GIF. Max size 5MB.
            </p>
          </div>
        </div>
      </div>

      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Basic Information
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Full Name
            </label>
            <Input2
              id="name"
              value={profile.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Enter your full name"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Email Address
            </label>
            <Input2
              id="email"
              type="email"
              value={profile.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="your.email@example.com"
            />
          </div>
        </div>
      </div>

      {/* Professional Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Professional Information
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="jobTitle" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Job Title
            </label>
            <Input2
              id="jobTitle"
              value={profile.jobTitle}
              onChange={(e) => handleInputChange('jobTitle', e.target.value)}
              placeholder="e.g., Software Engineer"
            />
          </div>

          <div>
            <label htmlFor="experience" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Years of Experience
            </label>
            <Select2
              id="experience"
              value={profile.experience}
              onChange={(e) => handleInputChange('experience', e.target.value)}
            >
              {experienceLevels.map(level => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </Select2>
          </div>
        </div>
      </div>

      {/* Skills */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Skills
        </h3>

        {/* Selected Skills */}
        <div className="flex flex-wrap gap-2">
          {profile.skills.map(skill => (
            <motion.div
              key={skill}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm font-medium"
            >
              {skill}
              <button
                onClick={() => handleRemoveSkill(skill)}
                className="ml-1 hover:bg-primary-200 dark:hover:bg-primary-800/50 rounded-full p-0.5 transition-colors"
                aria-label={`Remove ${skill}`}
              >
                <X className="w-3 h-3" />
              </button>
            </motion.div>
          ))}
        </div>

        {/* Add Custom Skill */}
        <div className="flex gap-2">
          <Input2
            value={customSkill}
            onChange={(e) => setCustomSkill(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddCustomSkill();
              }
            }}
            placeholder="Add a skill..."
            className="flex-1"
          />
          <Button2
            variant="outline"
            size="sm"
            onClick={handleAddCustomSkill}
            disabled={!customSkill.trim()}
          >
            <Plus className="w-4 h-4 mr-1" />
            Add
          </Button2>
        </div>

        {/* Popular Skills */}
        <div>
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
            Popular skills:
          </p>
          <div className="flex flex-wrap gap-2">
            {popularSkills
              .filter(skill => !profile.skills.includes(skill))
              .slice(0, 10)
              .map(skill => (
                <button
                  key={skill}
                  onClick={() => {
                    setProfile(prev => ({
                      ...prev,
                      skills: [...prev.skills, skill],
                    }));
                    setHasChanges(true);
                  }}
                  className="px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-full text-sm hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                >
                  + {skill}
                </button>
              ))}
          </div>
        </div>
      </div>

      {/* Bio */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Bio / Summary
        </h3>

        <div>
          <label htmlFor="bio" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
            Tell us about yourself
          </label>
          <Textarea2
            id="bio"
            value={profile.bio}
            onChange={(e) => handleInputChange('bio', e.target.value)}
            placeholder="Write a brief summary about your professional background and goals..."
            rows={5}
          />
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
            {profile.bio.length} / 500 characters
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-6 border-t border-neutral-200 dark:border-neutral-700">
        <Button2
          variant="outline"
          onClick={() => {
            // Reset to original values
            setProfile({
              name: 'John Doe',
              email: 'john.doe@example.com',
              photoUrl: null,
              jobTitle: 'Software Engineer',
              experience: '3-5',
              skills: ['JavaScript', 'React', 'Node.js', 'TypeScript'],
              bio: 'Passionate software engineer with experience in full-stack development.',
            });
            setPhotoPreview(null);
            setHasChanges(false);
          }}
          disabled={!hasChanges || isSaving}
        >
          Cancel
        </Button2>

        <Button2
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          loading={isSaving}
        >
          <Save className="w-4 h-4 mr-2" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button2>
      </div>
    </div>
  );
}
