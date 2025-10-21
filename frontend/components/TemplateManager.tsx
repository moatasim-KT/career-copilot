import React, { useState, useEffect } from 'react';
import { Button } from './ui/Button';

interface Template {
  id: number;
  name: string;
  description: string;
  template_type: string;
  category: string;
  tags: string[];
  is_system_template: boolean;
  usage_count: number;
  created_at: string;
}

interface GeneratedDocument {
  id: number;
  name: string;
  document_type: string;
  template_id: number;
  job_id?: number;
  file_format: string;
  status: string;
  created_at: string;
}

interface TemplateManagerProps {
  onTemplateSelect?: (template: Template) => void;
  onDocumentGenerate?: (document: GeneratedDocument) => void;
}

const TemplateManager: React.FC<TemplateManagerProps> = ({
  onTemplateSelect,
  onDocumentGenerate
}) => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [generatedDocuments, setGeneratedDocuments] = useState<GeneratedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'templates' | 'generated'>('templates');
  const [selectedTemplateType, setSelectedTemplateType] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    fetchTemplates();
    fetchGeneratedDocuments();
  }, [selectedTemplateType, selectedCategory]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedTemplateType !== 'all') {
        params.append('template_type', selectedTemplateType);
      }
      if (selectedCategory !== 'all') {
        params.append('category', selectedCategory);
      }

      const response = await fetch(`/api/v1/templates?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch templates');
      }

      const data = await response.json();
      setTemplates(data.templates);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchGeneratedDocuments = async () => {
    try {
      const response = await fetch('/api/v1/templates/generated/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch generated documents');
      }

      const data = await response.json();
      setGeneratedDocuments(data);
    } catch (err) {
      console.error('Error fetching generated documents:', err);
    }
  };

  const handleGenerateDocument = async (templateId: number, jobId?: number) => {
    try {
      const response = await fetch(`/api/v1/templates/${templateId}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          template_id: templateId,
          job_id: jobId,
          output_format: 'html',
          include_job_matching: !!jobId,
          customizations: {}
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate document');
      }

      const generatedDoc = await response.json();
      setGeneratedDocuments(prev => [generatedDoc, ...prev]);
      
      if (onDocumentGenerate) {
        onDocumentGenerate(generatedDoc);
      }

      // Switch to generated documents tab to show the new document
      setActiveTab('generated');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate document');
    }
  };

  const initializeSystemTemplates = async () => {
    try {
      const response = await fetch('/api/v1/templates/initialize-system-templates', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to initialize system templates');
      }

      // Refresh templates list
      fetchTemplates();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize templates');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Document Templates
          </h2>
          <div className="flex space-x-2">
            <Button
              onClick={initializeSystemTemplates}
              variant="outline"
              size="sm"
            >
              Initialize System Templates
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-6 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('templates')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'templates'
                ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Templates ({templates.length})
          </button>
          <button
            onClick={() => setActiveTab('generated')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'generated'
                ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Generated Documents ({generatedDocuments.length})
          </button>
        </div>

        {activeTab === 'templates' && (
          <>
            {/* Filters */}
            <div className="flex space-x-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Type
                </label>
                <select
                  value={selectedTemplateType}
                  onChange={(e) => setSelectedTemplateType(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="all">All Types</option>
                  <option value="resume">Resume</option>
                  <option value="cover_letter">Cover Letter</option>
                  <option value="portfolio">Portfolio</option>
                  <option value="reference_letter">Reference Letter</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="all">All Categories</option>
                  <option value="professional">Professional</option>
                  <option value="creative">Creative</option>
                  <option value="academic">Academic</option>
                  <option value="technical">Technical</option>
                </select>
              </div>
            </div>

            {/* Templates Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onTemplateSelect?.(template)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {template.name}
                    </h3>
                    {template.is_system_template && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                        System
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {template.description}
                  </p>
                  
                  <div className="flex items-center justify-between mb-3">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                      {template.template_type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Used {template.usage_count} times
                    </span>
                  </div>
                  
                  <div className="flex flex-wrap gap-1 mb-3">
                    {template.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  
                  <div className="flex space-x-2">
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleGenerateDocument(template.id);
                      }}
                      size="sm"
                      className="flex-1"
                    >
                      Generate
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {templates.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">
                  No templates found. Try adjusting your filters or initialize system templates.
                </p>
              </div>
            )}
          </>
        )}

        {activeTab === 'generated' && (
          <div className="space-y-4">
            {generatedDocuments.map((doc) => (
              <div
                key={doc.id}
                className="border border-gray-200 dark:border-gray-600 rounded-lg p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-white mb-1">
                      {doc.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {doc.document_type.replace('_', ' ')} • {doc.file_format.toUpperCase()}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                      <span>Created {formatDate(doc.created_at)}</span>
                      <span className={`px-2 py-1 rounded-full ${
                        doc.status === 'generated' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                      }`}>
                        {doc.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => {
                        // In a real implementation, this would download or view the document
                        console.log('View document:', doc.id);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      View
                    </Button>
                    <Button
                      onClick={() => {
                        // In a real implementation, this would download the document
                        console.log('Download document:', doc.id);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      Download
                    </Button>
                  </div>
                </div>
              </div>
            ))}

            {generatedDocuments.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">
                  No generated documents yet. Generate your first document from a template.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateManager;