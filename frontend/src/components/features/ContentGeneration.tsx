'use client';

import { useEffect, useState } from 'react';

import Button2 from '@/components/ui/Button2';
import Card from '@/components/ui/Card';
import Textarea from '@/components/ui/Textarea';
import { apiClient, Job } from '@/lib/api';
import { logger } from '@/lib/logger';

interface GeneratedContent {
  id: string;
  content_type: 'cover_letter' | 'resume_tailoring' | 'email_template';
  generated_content: string;
  user_modifications?: string;
  job_id?: number;
  created_at: string;
}

interface ContentGenerationProps {
  selectedJob?: Job;
  onContentGenerated?: (content: GeneratedContent) => void;
}

export default function ContentGeneration({
  selectedJob,
  onContentGenerated,
}: ContentGenerationProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(
    selectedJob?.id || null,
  );
  const [contentType, setContentType] = useState<
    'cover_letter' | 'resume_tailoring' | 'email_template'
  >('cover_letter');
  const [tone, setTone] = useState<'professional' | 'casual' | 'enthusiastic'>(
    'professional',
  );
  const [customPrompt, setCustomPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(
    null,
  );
  const [editedContent, setEditedContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadJobs();
  }, []);

  useEffect(() => {
    if (selectedJob) {
      setSelectedJobId(selectedJob.id);
    }
  }, [selectedJob]);

  const loadJobs = async () => {
    try {
      const response = await apiClient.getJobs();
      if (response.data) {
        setJobs(response.data);
      }
    } catch (err) {
      logger.error('Failed to load jobs:', err);
    }
  };

  const handleGenerate = async () => {
    if (!selectedJobId) {
      setError('Please select a job first');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const selectedJobData = jobs.find(job => job.id === selectedJobId);

      const requestData = {
        job_id: selectedJobId,
        content_type: contentType,
        tone,
        custom_prompt: customPrompt,
        job_data: selectedJobData,
      };

      const response = await apiClient.generateContent(contentType, requestData);

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data) {
        const content: GeneratedContent = {
          id: Date.now().toString(), // Temporary ID
          content_type: contentType,
          generated_content: response.data.generated_content,
          job_id: selectedJobId,
          created_at: new Date().toISOString(),
        };

        setGeneratedContent(content);
        setEditedContent(response.data.generated_content);
        onContentGenerated?.(content);
      }
    } catch (_err) {
      setError('Failed to generate content. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveModifications = async () => {
    if (!generatedContent) return;

    setSaving(true);
    setError(null);

    try {
      // In a real implementation, you would save to the backend
      // For now, we'll just update the local state
      const updatedContent = {
        ...generatedContent,
        user_modifications: editedContent,
      };

      setGeneratedContent(updatedContent);
      // Show success message
    } catch (_err) {
      setError('Failed to save modifications');
    } finally {
      setSaving(false);
    }
  };

  const handleExport = (format: 'txt' | 'pdf' | 'docx') => {
    if (!generatedContent) return;

    const content = editedContent || generatedContent.generated_content;
    const filename = `${contentType}_${selectedJobId}_${Date.now()}`;

    if (format === 'txt') {
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // For PDF and DOCX, you would typically use a library or backend service
      setError(`${format.toUpperCase()} export not yet implemented`);
    }
  };

  const resetGeneration = () => {
    setGeneratedContent(null);
    setEditedContent('');
    setError(null);
    setCustomPrompt('');
  };

  const getContentTypeLabel = (type: string) => {
    switch (type) {
      case 'cover_letter':
        return 'Cover Letter';
      case 'resume_tailoring':
        return 'Resume Tailoring';
      case 'email_template':
        return 'Email Template';
      default:
        return type;
    }
  };

  const getContentTypeDescription = (type: string) => {
    switch (type) {
      case 'cover_letter':
        return 'Generate a personalized cover letter highlighting your relevant skills and experience for this specific job.';
      case 'resume_tailoring':
        return 'Get suggestions on how to tailor your resume to better match the job requirements and keywords.';
      case 'email_template':
        return 'Create professional email templates for following up on applications or networking.';
      default:
        return '';
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">AI Content Generation</h3>

        {!generatedContent ? (
          <div className="space-y-6">
            {/* Content Type Selection */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-3">
                Content Type
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(['cover_letter', 'resume_tailoring', 'email_template'] as const).map(
                  type => (
                    <div
                      key={type}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        contentType === type
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-neutral-200 hover:border-neutral-300'
                      }`}
                      onClick={() => setContentType(type)}
                    >
                      <h4 className="font-medium text-neutral-900 mb-2">
                        {getContentTypeLabel(type)}
                      </h4>
                      <p className="text-sm text-neutral-600">
                        {getContentTypeDescription(type)}
                      </p>
                    </div>
                  ),
                )}
              </div>
            </div>

            {/* Job Selection */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Select Job
              </label>
              <select
                value={selectedJobId || ''}
                onChange={e => setSelectedJobId(Number(e.target.value) || null)}
                className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Choose a job...</option>
                {jobs.map(job => (
                  <option key={job.id} value={job.id}>
                    {job.title} at {job.company}
                  </option>
                ))}
              </select>
            </div>

            {/* Tone Selection */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Tone
              </label>
              <div className="flex space-x-4">
                {(['professional', 'casual', 'enthusiastic'] as const).map(
                  toneOption => (
                    <label key={toneOption} className="flex items-center">
                      <input
                        type="radio"
                        name="tone"
                        value={toneOption}
                        checked={tone === toneOption}
                        onChange={e => setTone(e.target.value as typeof tone)}
                        className="mr-2"
                      />
                      <span className="capitalize">{toneOption}</span>
                    </label>
                  ),
                )}
              </div>
            </div>

            {/* Custom Prompt */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Additional Instructions (Optional)
              </label>
              <Textarea
                value={customPrompt}
                onChange={e => setCustomPrompt(e.target.value)}
                placeholder="Add any specific requirements or information you'd like to include..."
                rows={3}
              />
            </div>

            {/* Generate Button */}
            <Button2
              onClick={handleGenerate}
              disabled={generating || !selectedJobId}
              className="w-full"
            >
              {generating ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Generating...</span>
                </div>
              ) : (
                `Generate ${getContentTypeLabel(contentType)}`
              )}
            </Button2>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Generated Content Header */}
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-medium">
                  Generated {getContentTypeLabel(generatedContent.content_type)}
                </h4>
                <p className="text-sm text-neutral-600">
                  For: {jobs.find(job => job.id === generatedContent.job_id)?.title} at{' '}
                  {jobs.find(job => job.id === generatedContent.job_id)?.company}
                </p>
              </div>
              <Button2 variant="outline" onClick={resetGeneration}>
                Generate New
              </Button2>
            </div>

            {/* Content Editor */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Content (Click to edit)
              </label>
              <Textarea
                value={editedContent}
                onChange={e => setEditedContent(e.target.value)}
                rows={15}
                className="font-mono text-sm"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              <Button2
                onClick={handleSaveModifications}
                disabled={saving}
                variant="outline"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button2>

              <Button2 onClick={() => handleExport('txt')} variant="outline">
                Export as TXT
              </Button2>

              <Button2 onClick={() => handleExport('pdf')} variant="outline" disabled>
                Export as PDF
              </Button2>

              <Button2 onClick={() => handleExport('docx')} variant="outline" disabled>
                Export as DOCX
              </Button2>
            </div>

            {/* Content Statistics */}
            <div className="bg-neutral-50 p-4 rounded-lg">
              <h5 className="font-medium mb-2">Content Statistics</h5>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-neutral-600">Words:</span>
                  <span className="ml-2 font-medium">
                    {editedContent.split(/\s+/).filter(word => word.length > 0).length}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-600">Characters:</span>
                  <span className="ml-2 font-medium">{editedContent.length}</span>
                </div>
                <div>
                  <span className="text-neutral-600">Paragraphs:</span>
                  <span className="ml-2 font-medium">
                    {
                      editedContent.split('\n\n').filter(p => p.trim().length > 0)
                        .length
                    }
                  </span>
                </div>
                <div>
                  <span className="text-neutral-600">Reading Time:</span>
                  <span className="ml-2 font-medium">
                    {Math.ceil(editedContent.split(/\s+/).length / 200)} min
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </Card>
    </div>
  );
}
