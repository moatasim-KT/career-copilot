import React, { useState, useEffect } from 'react';
import { Button } from './ui/Button';

interface TemplateSection {
  id: string;
  name: string;
  type: string;
  required: boolean;
  dynamic_content: boolean;
  job_matching: boolean;
  order: number;
  fields: Array<{
    name: string;
    type: string;
    required: boolean;
    placeholder: string;
  }>;
}

interface TemplateStructure {
  sections: TemplateSection[];
  styling: {
    font_family: string;
    font_size: string;
    margins: Record<string, string>;
    colors: Record<string, string>;
  };
}

interface Template {
  id?: number;
  name: string;
  description: string;
  template_type: string;
  category: string;
  tags: string[];
  template_structure: TemplateStructure;
  template_content: string;
  template_styles: string;
}

interface TemplateEditorProps {
  template?: Template;
  onSave: (template: Template) => void;
  onCancel: () => void;
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({
  template,
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState<Template>({
    name: '',
    description: '',
    template_type: 'resume',
    category: 'professional',
    tags: [],
    template_structure: {
      sections: [],
      styling: {
        font_family: 'Arial, sans-serif',
        font_size: '11pt',
        margins: { top: '1in', bottom: '1in', left: '1in', right: '1in' },
        colors: { primary: '#000000', accent: '#333333' }
      }
    },
    template_content: '',
    template_styles: ''
  });

  const [newTag, setNewTag] = useState('');
  const [activeTab, setActiveTab] = useState<'basic' | 'structure' | 'content' | 'styles'>('basic');

  useEffect(() => {
    if (template) {
      setFormData(template);
    }
  }, [template]);

  const handleInputChange = (field: keyof Template, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleAddSection = () => {
    const newSection: TemplateSection = {
      id: `section_${Date.now()}`,
      name: 'New Section',
      type: 'text_area',
      required: false,
      dynamic_content: false,
      job_matching: false,
      order: formData.template_structure.sections.length + 1,
      fields: []
    };

    setFormData(prev => ({
      ...prev,
      template_structure: {
        ...prev.template_structure,
        sections: [...prev.template_structure.sections, newSection]
      }
    }));
  };

  const handleUpdateSection = (sectionId: string, updates: Partial<TemplateSection>) => {
    setFormData(prev => ({
      ...prev,
      template_structure: {
        ...prev.template_structure,
        sections: prev.template_structure.sections.map(section =>
          section.id === sectionId ? { ...section, ...updates } : section
        )
      }
    }));
  };

  const handleRemoveSection = (sectionId: string) => {
    setFormData(prev => ({
      ...prev,
      template_structure: {
        ...prev.template_structure,
        sections: prev.template_structure.sections.filter(section => section.id !== sectionId)
      }
    }));
  };

  const handleSave = () => {
    onSave(formData);
  };

  const templateTypes = [
    { value: 'resume', label: 'Resume' },
    { value: 'cover_letter', label: 'Cover Letter' },
    { value: 'portfolio', label: 'Portfolio' },
    { value: 'reference_letter', label: 'Reference Letter' },
    { value: 'thank_you_letter', label: 'Thank You Letter' }
  ];

  const categories = [
    { value: 'professional', label: 'Professional' },
    { value: 'creative', label: 'Creative' },
    { value: 'academic', label: 'Academic' },
    { value: 'technical', label: 'Technical' },
    { value: 'executive', label: 'Executive' },
    { value: 'entry_level', label: 'Entry Level' }
  ];

  const sectionTypes = [
    { value: 'header', label: 'Header' },
    { value: 'text_area', label: 'Text Area' },
    { value: 'list', label: 'List' },
    { value: 'address', label: 'Address' },
    { value: 'contact', label: 'Contact Info' }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {template ? 'Edit Template' : 'Create Template'}
          </h2>
          <div className="flex space-x-2">
            <Button onClick={onCancel} variant="outline">
              Cancel
            </Button>
            <Button onClick={handleSave}>
              Save Template
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-6 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {[
            { key: 'basic', label: 'Basic Info' },
            { key: 'structure', label: 'Structure' },
            { key: 'content', label: 'Content' },
            { key: 'styles', label: 'Styles' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Basic Info Tab */}
        {activeTab === 'basic' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Template Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Enter template name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={3}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Describe this template"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Template Type
                </label>
                <select
                  value={formData.template_type}
                  onChange={(e) => handleInputChange('template_type', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  {templateTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  {categories.map((category) => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tags
              </label>
              <div className="flex flex-wrap gap-2 mb-2">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                  >
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 text-blue-600 hover:text-blue-800 dark:text-blue-300 dark:hover:text-blue-100"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Add a tag"
                />
                <Button onClick={handleAddTag} variant="outline">
                  Add
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Structure Tab */}
        {activeTab === 'structure' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Template Sections
              </h3>
              <Button onClick={handleAddSection} variant="outline">
                Add Section
              </Button>
            </div>

            <div className="space-y-4">
              {formData.template_structure.sections.map((section) => (
                <div
                  key={section.id}
                  className="border border-gray-200 dark:border-gray-600 rounded-lg p-4"
                >
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Section Name
                      </label>
                      <input
                        type="text"
                        value={section.name}
                        onChange={(e) => handleUpdateSection(section.id, { name: e.target.value })}
                        className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Section Type
                      </label>
                      <select
                        value={section.type}
                        onChange={(e) => handleUpdateSection(section.id, { type: e.target.value })}
                        className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      >
                        {sectionTypes.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 mb-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={section.required}
                        onChange={(e) => handleUpdateSection(section.id, { required: e.target.checked })}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Required</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={section.dynamic_content}
                        onChange={(e) => handleUpdateSection(section.id, { dynamic_content: e.target.checked })}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Dynamic Content</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={section.job_matching}
                        onChange={(e) => handleUpdateSection(section.id, { job_matching: e.target.checked })}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Job Matching</span>
                    </label>
                  </div>

                  <div className="flex justify-end">
                    <Button
                      onClick={() => handleRemoveSection(section.id)}
                      variant="outline"
                      size="sm"
                    >
                      Remove Section
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content Tab */}
        {activeTab === 'content' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Template Content (HTML with Jinja2 placeholders)
              </label>
              <textarea
                value={formData.template_content}
                onChange={(e) => handleInputChange('template_content', e.target.value)}
                rows={20}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
                placeholder="Enter HTML template with Jinja2 placeholders like {{ user.profile.full_name }}"
              />
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p className="mb-2">Available template variables:</p>
              <ul className="list-disc list-inside space-y-1">
                <li><code>user.profile.*</code> - User profile data</li>
                <li><code>job.*</code> - Job-specific data (when generating for a job)</li>
                <li><code>tailored.*</code> - Job-tailored content suggestions</li>
                <li><code>customizations.*</code> - User customizations</li>
              </ul>
            </div>
          </div>
        )}

        {/* Styles Tab */}
        {activeTab === 'styles' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                CSS Styles
              </label>
              <textarea
                value={formData.template_styles}
                onChange={(e) => handleInputChange('template_styles', e.target.value)}
                rows={15}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
                placeholder="Enter CSS styles for the template"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateEditor;