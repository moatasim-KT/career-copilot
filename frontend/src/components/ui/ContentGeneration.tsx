
'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { Sparkles, Loader, AlertCircle } from 'lucide-react';

export default function ContentGeneration() {
  const [contentType, setContentType] = useState<'cover_letter' | 'resume_summary'>('cover_letter');
  const [context, setContext] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!context) {
      setError('Please provide some context for generation.');
      return;
    }

    setIsLoading(true);
    setError('');
    setGeneratedContent('');

    try {
      const response = await apiClient.generateContent(contentType, { context });
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setGeneratedContent(response.data.generated_content);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Sparkles className="h-5 w-5 text-blue-600 mr-2" />
          AI Content Generation
        </h3>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="contentType" className="block text-sm font-medium text-gray-700">
              Content Type
            </label>
            <select
              id="contentType"
              name="contentType"
              value={contentType}
              onChange={(e) => setContentType(e.target.value as any)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="cover_letter">Cover Letter</option>
              <option value="resume_summary">Resume Summary</option>
            </select>
          </div>

          <div>
            <label htmlFor="context" className="block text-sm font-medium text-gray-700">
              Context (e.g., job description, key skills)
            </label>
            <textarea
              id="context"
              name="context"
              rows={6}
              value={context}
              onChange={(e) => setContext(e.target.value)}
              className="mt-1 shadow-sm block w-full sm:text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Paste a job description or describe your desired role..."
            />
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader className="animate-spin h-5 w-5 mr-3" />
                Generating...
              </>
            ) : (
              'Generate Content'
            )}
          </button>
        </div>

        {generatedContent && (
          <div className="mt-6 border-t pt-6">
            <h4 className="text-md font-semibold text-gray-800 mb-2">Generated Content:</h4>
            <div className="prose prose-sm max-w-none p-4 bg-gray-50 rounded-md border">
              {generatedContent}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
