/**
 * ResumeStep Component
 * 
 * Third step of onboarding wizard - resume upload with AI parsing.
 * 
 * Features:
 * - File upload with drag & drop
 * - Support PDF and DOCX formats
 * - AI resume parsing (optional)
 * - Auto-fill skills from resume
 * - Skip option
 * - File preview
 * 
 * @module components/onboarding/steps/ResumeStep
 */

'use client';

import { Upload, FileText, Check, X, AlertCircle, Loader2 } from 'lucide-react';
import React, { useState, useCallback } from 'react';
import { toast } from 'sonner';

import Button2 from '@/components/ui/Button2';
import { staggerContainer, staggerItem } from '@/lib/animations';
import { logger } from '@/lib/logger';
import { m } from '@/lib/motion';
import { cn } from '@/lib/utils';

import type { StepProps } from '../OnboardingWizard';


/**
 * Supported file types
 */
const SUPPORTED_TYPES = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'application/msword': '.doc',
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

/**
 * ResumeStep Component
 */
const ResumeStep: React.FC<StepProps> = ({ data, onChange, onSkip }) => {
  const [file, setFile] = useState<File | null>(data.resumeFile || null);
  const [fileName, setFileName] = useState<string>(data.resumeName || '');
  const [isUploading, setIsUploading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [parseResult, setParseResult] = useState<any>(data.parseResult || null);
  const [isDragging, setIsDragging] = useState(false);

  /**
   * Validate file
   */
  const validateFile = (file: File): string | null => {
    // Check file type
    if (!Object.keys(SUPPORTED_TYPES).includes(file.type)) {
      return 'Please upload a PDF or DOCX file';
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be less than 10MB';
    }

    return null;
  };

  /**
   * Parse resume with AI
   */
  const handleParse = useCallback(async (fileToparse: File) => {
    setIsParsing(true);

    try {
      const formData = new FormData();
      formData.append('resume', fileToparse);

      // In production, call actual API endpoint
      // const response = await apiClient.post('/resume/parse', formData);

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Mock parse result
      const mockResult = {
        skills: [
          { value: 'react', label: 'React', proficiency: 'Advanced' },
          { value: 'typescript', label: 'TypeScript', proficiency: 'Advanced' },
          { value: 'nodejs', label: 'Node.js', proficiency: 'Intermediate' },
          { value: 'python', label: 'Python', proficiency: 'Intermediate' },
        ],
        experience: '5-10',
        jobTitle: 'Senior Full-Stack Developer',
        summary: 'Experienced developer with 7 years in web development',
      };

      setParseResult(mockResult);
      onChange({
        parseResult: mockResult,
        parsedAt: new Date().toISOString(),
      });

      toast.success('Resume parsed successfully! Skills extracted.');
    } catch (error) {
      logger.error('Parse error:', error);
      toast.error('Failed to parse resume. You can still continue.');
    } finally {
      setIsParsing(false);
    }
  }, [onChange]);

  /**
   * Handle file upload
   */
  const handleFileUpload = useCallback(
    async (selectedFile: File) => {
      const error = validateFile(selectedFile);
      if (error) {
        toast.error(error);
        return;
      }

      setFile(selectedFile);
      setFileName(selectedFile.name);
      setIsUploading(true);
      setUploadProgress(0);

      try {
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress((prev) => Math.min(prev + 10, 90));
        }, 100);

        // In production, upload to server
        // For now, just store file reference
        await new Promise((resolve) => setTimeout(resolve, 1000));

        clearInterval(progressInterval);
        setUploadProgress(100);
        setIsUploading(false);

        onChange({
          resumeFile: selectedFile,
          resumeName: selectedFile.name,
          resumeSize: selectedFile.size,
          resumeType: selectedFile.type,
          uploadedAt: new Date().toISOString(),
        });

        toast.success('Resume uploaded successfully');

        // Auto-parse resume
        handleParse(selectedFile);
      } catch (error) {
        logger.error('Upload error:', error);
        setIsUploading(false);
        toast.error('Failed to upload resume');
      }
    },
    [handleParse, onChange],
  );

  /**
   * Handle drag events
   */
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileUpload(droppedFile);
    }
  };

  /**
   * Handle file input change
   */
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileUpload(selectedFile);
    }
  };

  /**
   * Remove file
   */
  const handleRemoveFile = () => {
    setFile(null);
    setFileName('');
    setParseResult(null);
    setUploadProgress(0);
    onChange({
      resumeFile: null,
      resumeName: null,
      parseResult: null,
    });
    toast.success('Resume removed');
  };

  return (
    <m.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Header */}
      <m.div variants={staggerItem} className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
          <FileText className="h-8 w-8 text-primary-600 dark:text-primary-400" />
        </div>
        <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          Upload Your Resume
        </h3>
        <p className="text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
          Upload your resume and we&apos;ll use AI to extract your skills and experience.
          This step is optional but helps us provide better recommendations.
        </p>
      </m.div>

      {/* Upload area */}
      <m.div variants={staggerItem}>
        {!file ? (
          <div
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              'relative border-2 border-dashed rounded-xl p-12 transition-all',
              isDragging
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-neutral-300 dark:border-neutral-700 hover:border-primary-400 dark:hover:border-primary-600',
              isUploading && 'pointer-events-none opacity-50',
            )}
          >
            <input
              type="file"
              accept={Object.values(SUPPORTED_TYPES).join(',')}
              onChange={handleFileInputChange}
              disabled={isUploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              aria-label="Upload resume"
            />

            <div className="text-center">
              {isUploading ? (
                <>
                  <Loader2 className="h-12 w-12 text-primary-600 dark:text-primary-400 mx-auto mb-4 animate-spin" />
                  <p className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                    Uploading...
                  </p>
                  <div className="max-w-xs mx-auto">
                    <div className="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                      <m.div
                        className="h-full bg-primary-600"
                        initial={{ width: 0 }}
                        animate={{ width: `${uploadProgress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                      {uploadProgress}%
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <Upload className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                    {isDragging ? 'Drop your resume here' : 'Drag & drop your resume'}
                  </p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
                    or click to browse
                  </p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">
                    Supports PDF, DOC, DOCX (max 10MB)
                  </p>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="border-2 border-success-200 dark:border-success-800 bg-success-50 dark:bg-success-900/20 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-success-100 dark:bg-success-900/30 flex items-center justify-center">
                <FileText className="h-6 w-6 text-success-600 dark:text-success-400" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-neutral-900 dark:text-neutral-100 truncate">
                      {fileName}
                    </p>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                      {file && `${(file.size / 1024 / 1024).toFixed(2)} MB`}
                    </p>
                  </div>

                  <button
                    onClick={handleRemoveFile}
                    className="flex-shrink-0 p-2 text-neutral-400 hover:text-error-600 dark:hover:text-error-400 transition-colors"
                    aria-label="Remove resume"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {isParsing && (
                  <div className="mt-4 flex items-center gap-2 text-sm text-primary-600 dark:text-primary-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Parsing resume with AI...</span>
                  </div>
                )}

                {parseResult && !isParsing && (
                  <div className="mt-4 space-y-3">
                    <div className="flex items-center gap-2 text-sm text-success-600 dark:text-success-400">
                      <Check className="h-4 w-4" />
                      <span>Resume parsed successfully!</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3 bg-white dark:bg-neutral-800 rounded-lg">
                        <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                          Skills Found
                        </p>
                        <p className="font-medium text-neutral-900 dark:text-neutral-100">
                          {parseResult.skills?.length || 0} skills
                        </p>
                      </div>
                      <div className="p-3 bg-white dark:bg-neutral-800 rounded-lg">
                        <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                          Experience Level
                        </p>
                        <p className="font-medium text-neutral-900 dark:text-neutral-100">
                          {parseResult.experience || 'Not detected'}
                        </p>
                      </div>
                    </div>

                    {parseResult.skills && parseResult.skills.length > 0 && (
                      <div className="p-3 bg-white dark:bg-neutral-800 rounded-lg">
                        <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                          Extracted Skills
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {parseResult.skills.slice(0, 6).map((skill: any) => (
                            <span
                              key={skill.value}
                              className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded text-xs font-medium"
                            >
                              {skill.label}
                            </span>
                          ))}
                          {parseResult.skills.length > 6 && (
                            <span className="px-2 py-1 text-neutral-600 dark:text-neutral-400 text-xs">
                              +{parseResult.skills.length - 6} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </m.div>

      {/* Info cards */}
      <m.div
        variants={staggerItem}
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                Your Privacy Matters
              </h4>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Your resume is processed securely and never shared with third parties.
                We only extract relevant information to improve your experience.
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
          <div className="flex items-start gap-3">
            <Check className="h-5 w-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-purple-900 dark:text-purple-100 mb-1">
                AI-Powered Parsing
              </h4>
              <p className="text-xs text-purple-700 dark:text-purple-300">
                Our AI automatically extracts skills, experience, and job titles from
                your resume to save you time.
              </p>
            </div>
          </div>
        </div>
      </m.div>

      {/* Skip option */}
      {!file && (
        <m.div variants={staggerItem} className="text-center pt-4">
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-3">
            Don&apos;t have your resume handy?
          </p>
          <Button2 variant="ghost" onClick={onSkip}>
            Skip this step
          </Button2>
        </m.div>
      )}
    </m.div>
  );
};

export default ResumeStep;
