'use client';

import React, { useState } from 'react';

import ContentGeneration from '@/components/features/ContentGeneration';
import InterviewPractice from '@/components/features/InterviewPractice';
import ResumeUpload from '@/components/features/ResumeUpload';
import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';
import { logger } from '@/lib/logger';

type ActiveFeature = 'resume' | 'content' | 'interview' | null;

export default function AdvancedFeaturesPage() {
  const [activeFeature, setActiveFeature] = useState<ActiveFeature>(null);

  const features = [
    {
      id: 'resume' as const,
      title: 'Resume Upload & Analysis',
      description: 'Upload your resume and get AI-powered analysis with skill extraction and profile suggestions.',
      icon: (
        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      color: 'blue',
    },
    {
      id: 'content' as const,
      title: 'AI Content Generation',
      description: 'Generate personalized cover letters, tailored resumes, and professional email templates.',
      icon: (
        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      color: 'green',
    },
    {
      id: 'interview' as const,
      title: 'Interview Practice',
      description: 'Practice interviews with AI-powered questions and get detailed feedback on your performance.',
      icon: (
        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      ),
      color: 'purple',
    },
  ];

  const getColorClasses = (color: string, variant: 'bg' | 'text' | 'border' | 'hover') => {
    const colorMap = {
      blue: {
        bg: 'bg-blue-50',
        text: 'text-blue-600',
        border: 'border-blue-200',
        hover: 'hover:bg-blue-100',
      },
      green: {
        bg: 'bg-green-50',
        text: 'text-green-600',
        border: 'border-green-200',
        hover: 'hover:bg-green-100',
      },
      purple: {
        bg: 'bg-purple-50',
        text: 'text-purple-600',
        border: 'border-purple-200',
        hover: 'hover:bg-purple-100',
      },
    };
    return colorMap[color as keyof typeof colorMap]?.[variant] || '';
  };

  if (activeFeature) {
    return (
      <div className="space-y-6">
        {/* Header with Back Button */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {features.find(f => f.id === activeFeature)?.title}
            </h1>
            <p className="text-gray-600 mt-1">
              {features.find(f => f.id === activeFeature)?.description}
            </p>
          </div>
          <Button2
            variant="outline"
            onClick={() => setActiveFeature(null)}
          >
            ← Back to Features
          </Button2>
        </div>

        {/* Feature Content */}
        <div>
          {activeFeature === 'resume' && (
            <ResumeUpload
              onUploadComplete={(data) => {
                logger.log('Resume upload completed:', data);
              }}
              onProfileUpdate={(updates) => {
                logger.log('Profile updated:', updates);
              }}
            />
          )}

          {activeFeature === 'content' && (
            <ContentGeneration
              onContentGenerated={(content) => {
                logger.log('Content generated:', content);
              }}
            />
          )}

          {activeFeature === 'interview' && (
            <InterviewPractice
              onSessionComplete={(session) => {
                logger.log('Interview session completed:', session);
              }}
            />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Advanced Features</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Supercharge your job search with AI-powered tools designed to help you stand out from the competition.
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature) => (
          <div
            key={feature.id}
            className="cursor-pointer transition-all duration-200"
            onClick={() => setActiveFeature(feature.id)}
          >
            <Card2
              className={`p-6 border-2 ${getColorClasses(feature.color, 'border')} ${getColorClasses(feature.color, 'hover')}`}
            >
              <div className="text-center space-y-4">
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${getColorClasses(feature.color, 'bg')}`}>
                  <div className={getColorClasses(feature.color, 'text')}>
                    {feature.icon}
                  </div>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>

                <Button2
                  className={`w-full ${getColorClasses(feature.color, 'text')} border-current`}
                  variant="outline"
                >
                  Get Started
                </Button2>
              </div>
            </Card2>
          </div>
        ))}
      </div>

      {/* Feature Benefits */}
      <Card2 className="p-8 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Why Use Advanced Features?</h2>
          <p className="text-gray-600 max-w-3xl mx-auto">
            Our AI-powered tools are designed to give you a competitive edge in today&apos;s job market.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="bg-white rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3 shadow-sm">
              <span className="text-2xl">⚡</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Save Time</h4>
            <p className="text-sm text-gray-600">
              Generate content in minutes instead of hours
            </p>
          </div>

          <div className="text-center">
            <div className="bg-white rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3 shadow-sm">
              <span className="text-2xl">🎯</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Personalized</h4>
            <p className="text-sm text-gray-600">
              Tailored content for each specific job application
            </p>
          </div>

          <div className="text-center">
            <div className="bg-white rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3 shadow-sm">
              <span className="text-2xl">📈</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Improve Skills</h4>
            <p className="text-sm text-gray-600">
              Get feedback and improve your interview performance
            </p>
          </div>

          <div className="text-center">
            <div className="bg-white rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3 shadow-sm">
              <span className="text-2xl">🚀</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Stand Out</h4>
            <p className="text-sm text-gray-600">
              Professional, polished applications that get noticed
            </p>
          </div>
        </div>
      </Card2>

      {/* Getting Started Tips */}
      <Card2 className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Getting Started Tips</h3>
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
              1
            </div>
            <div>
              <h4 className="font-medium text-gray-900">Start with Resume Upload</h4>
              <p className="text-sm text-gray-600">
                Upload your current resume to extract skills and get profile suggestions.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm font-medium">
              2
            </div>
            <div>
              <h4 className="font-medium text-gray-900">Generate Content for Jobs</h4>
              <p className="text-sm text-gray-600">
                Create personalized cover letters and tailored resumes for specific positions.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-sm font-medium">
              3
            </div>
            <div>
              <h4 className="font-medium text-gray-900">Practice Interviews</h4>
              <p className="text-sm text-gray-600">
                Use the interview practice tool to prepare for upcoming interviews and improve your responses.
              </p>
            </div>
          </div>
        </div>
      </Card2>
    </div>
  );
}