'use client';

import React, { useState, useCallback } from 'react';

import Button from '@/components/ui/Button2';
import Card from '@/components/ui/Card2';
import { apiClient } from '@/lib/api';

interface ParsedResumeData {
  upload_id: string;
  parsing_status: 'pending' | 'completed' | 'failed';
  extracted_data?: {
    skills: string[];
    experience_level: string;
    contact_info: {
      name?: string;
      email?: string;
      phone?: string;
    };
    work_experience: Array<{
      company: string;
      title: string;
      duration: string;
      description: string;
    }>;
    education: Array<{
      institution: string;
      degree: string;
      year: string;
    }>;
  };
  suggestions?: {
    profile_updates: {
      skills_to_add: string[];
      experience_level_suggestion: string;
    };
  };
}

interface ResumeUploadProps {
  onUploadComplete?: (data: ParsedResumeData) => void;
  onProfileUpdate?: (updates: any) => void;
}

export default function ResumeUpload({ onUploadComplete, onProfileUpdate }: ResumeUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [uploadResult, setUploadResult] = useState<ParsedResumeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        setError(null);
      }
    }
  }, []);

  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];

    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF, DOC, or DOCX file');
      return false;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      setError('File size must be less than 10MB');
      return false;
    }

    return true;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        setError(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const response = await apiClient.uploadResume(file);

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data) {
        setUploadResult(response.data as ParsedResumeData);

        // Start polling for parsing status if pending
        if (response.data.parsing_status === 'pending') {
          setParsing(true);
          pollParsingStatus(response.data.upload_id);
        }

        onUploadComplete?.(response.data as ParsedResumeData);
      }
    } catch (_err) {
      setError('Failed to upload resume. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const pollParsingStatus = async (uploadId: string) => {
    const maxAttempts = 30; // 30 seconds max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/resume/${uploadId}/status`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (response.ok) {
          const data = await response.json();

          if (data.parsing_status === 'completed') {
            setUploadResult(prev => prev ? { ...prev, ...data } : data);
            setParsing(false);
            return;
          } else if (data.parsing_status === 'failed') {
            setError('Failed to parse resume. Please try uploading again.');
            setParsing(false);
            return;
          }
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // Poll every second
        } else {
          setError('Parsing is taking longer than expected. Please refresh to check status.');
          setParsing(false);
        }
      } catch (_err) {
        setError('Error checking parsing status');
        setParsing(false);
      }
    };

    poll();
  };

  const handleApplyProfileUpdates = async () => {
    if (!uploadResult?.suggestions?.profile_updates) return;

    const updates = {
      skills: uploadResult.suggestions.profile_updates.skills_to_add,
      experience_level: uploadResult.suggestions.profile_updates.experience_level_suggestion,
    };

    try {
      const response = await apiClient.updateUserProfile(updates);

      if (response.error) {
        setError(response.error);
        return;
      }

      onProfileUpdate?.(updates);
      // Show success message or update UI
    } catch (_err) {
      setError('Failed to update profile');
    }
  };

  const resetUpload = () => {
    setFile(null);
    setUploadResult(null);
    setError(null);
    setUploading(false);
    setParsing(false);
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Upload Resume</h3>

        {!file && !uploadResult && (
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
              }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-4">
              <div className="text-neutral-500">
                <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div>
                <p className="text-lg">Drop your resume here, or</p>
                <label className="cursor-pointer">
                  <span className="text-blue-600 hover:text-blue-500">browse files</span>
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileSelect}
                  />
                </label>
              </div>
              <p className="text-sm text-neutral-500">
                Supports PDF, DOC, and DOCX files up to 10MB
              </p>
            </div>
          </div>
        )}

        {file && !uploadResult && (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-neutral-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-neutral-900">{file.name}</p>
                  <p className="text-sm text-neutral-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={resetUpload}
                disabled={uploading}
              >
                Remove
              </Button>
            </div>

            <div className="flex space-x-3">
              <Button
                onClick={handleUpload}
                disabled={uploading}
                className="flex-1"
              >
                {uploading ? 'Uploading...' : 'Upload & Parse Resume'}
              </Button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </Card>

      {uploadResult && (
        <Card className="p-6">
          <h4 className="text-lg font-semibold mb-4">Parsing Results</h4>

          {parsing && (
            <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-lg">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <p className="text-blue-700">Parsing your resume...</p>
            </div>
          )}

          {uploadResult.parsing_status === 'completed' && uploadResult.extracted_data && (
            <div className="space-y-6">
              {/* Contact Information */}
              {uploadResult.extracted_data.contact_info && (
                <div>
                  <h5 className="font-medium mb-2">Contact Information</h5>
                  <div className="bg-neutral-50 p-3 rounded-lg">
                    <p><strong>Name:</strong> {uploadResult.extracted_data.contact_info.name || 'Not found'}</p>
                    <p><strong>Email:</strong> {uploadResult.extracted_data.contact_info.email || 'Not found'}</p>
                    <p><strong>Phone:</strong> {uploadResult.extracted_data.contact_info.phone || 'Not found'}</p>
                  </div>
                </div>
              )}

              {/* Skills */}
              {uploadResult.extracted_data.skills && uploadResult.extracted_data.skills.length > 0 && (
                <div>
                  <h5 className="font-medium mb-2">Extracted Skills</h5>
                  <div className="flex flex-wrap gap-2">
                    {uploadResult.extracted_data.skills.map((skill, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience Level */}
              {uploadResult.extracted_data.experience_level && (
                <div>
                  <h5 className="font-medium mb-2">Experience Level</h5>
                  <p className="text-neutral-700 capitalize">{uploadResult.extracted_data.experience_level}</p>
                </div>
              )}

              {/* Profile Update Suggestions */}
              {uploadResult.suggestions?.profile_updates && (
                <div className="border-t pt-4">
                  <h5 className="font-medium mb-3">Profile Update Suggestions</h5>

                  {uploadResult.suggestions.profile_updates.skills_to_add.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm text-neutral-600 mb-2">Skills to add to your profile:</p>
                      <div className="flex flex-wrap gap-2">
                        {uploadResult.suggestions.profile_updates.skills_to_add.map((skill, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                          >
                            + {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <Button
                    onClick={handleApplyProfileUpdates}
                    className="w-full"
                  >
                    Apply Profile Updates
                  </Button>
                </div>
              )}
            </div>
          )}

          {uploadResult.parsing_status === 'failed' && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">Failed to parse resume. Please try uploading again or contact support.</p>
            </div>
          )}

          <div className="mt-4 pt-4 border-t">
            <Button
              variant="outline"
              onClick={resetUpload}
              className="w-full"
            >
              Upload Another Resume
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}