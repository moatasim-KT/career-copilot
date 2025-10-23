'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import Card from './Card';
import { Copy } from 'lucide-react';

export default function ContentGeneration() {
  const [contentType, setContentType] = useState('cover_letter');
  const [context, setContext] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setGeneratedContent('');

    try {
      const response = await apiClient.generateContent(contentType, { context });
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setGeneratedContent(response.data.generated_content);
      }
    } catch (err) {
      setError('An unknown error occurred');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Content Generation</h2>
      <div className="space-y-4">
        <div>
          <label htmlFor="contentType" className="block text-sm font-medium text-gray-700">Content Type</label>
          <select
            id="contentType"
            name="contentType"
            value={contentType}
            onChange={(e) => setContentType(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="cover_letter">Cover Letter</option>
            <option value="resume_summary">Resume Summary</option>
          </select>
        </div>
        <div>
          <label htmlFor="context" className="block text-sm font-medium text-gray-700">Context</label>
          <textarea
            id="context"
            name="context"
            rows={5}
            value={context}
            onChange={(e) => setContext(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="Provide context for the content generation, such as job description, company details, etc."
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-4 py-2 bg-blue-500 text-white rounded-md disabled:bg-gray-400"
        >
          {generating ? 'Generating...' : 'Generate'}
        </button>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        {generatedContent && (
          <div className="mt-4 p-4 bg-gray-100 rounded-md relative">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Generated Content</h3>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{generatedContent}</p>
            <button onClick={handleCopy} className="absolute top-2 right-2 p-1 bg-gray-200 rounded-md hover:bg-gray-300">
              <Copy className="w-4 h-4" />
            </button>
            {copied && <span className="absolute top-2 right-10 text-xs bg-gray-800 text-white px-2 py-1 rounded">Copied!</span>}
          </div>
        )}
      </div>
    </div>
  );
}