import { useState } from 'react'
import { Card, CardContent, CardHeader, Input, Button, Badge } from '@/components/ui'
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline'
import { apiClient } from '@/utils/api'
import { Job } from '@/types'

interface AddJobModalProps {
  onClose: () => void
  onJobAdded: (job: Job) => void
}

interface JobFormData {
  title: string
  company: string
  location: string
  salary_min: string
  salary_max: string
  currency: string
  description: string
  application_url: string
  status: string
  source: string
  tags: string[]
}

const initialFormData: JobFormData = {
  title: '',
  company: '',
  location: '',
  salary_min: '',
  salary_max: '',
  currency: 'USD',
  description: '',
  application_url: '',
  status: 'not_applied',
  source: 'manual',
  tags: []
}

const statusOptions = [
  { value: 'not_applied', label: 'Not Applied' },
  { value: 'applied', label: 'Applied' },
  { value: 'phone_screen', label: 'Phone Screen' },
  { value: 'interview_scheduled', label: 'Interview Scheduled' },
  { value: 'interviewed', label: 'Interviewed' },
  { value: 'offer_received', label: 'Offer Received' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'withdrawn', label: 'Withdrawn' }
]

const currencyOptions = [
  { value: 'USD', label: 'USD ($)' },
  { value: 'EUR', label: 'EUR (€)' },
  { value: 'GBP', label: 'GBP (£)' },
  { value: 'CAD', label: 'CAD (C$)' },
  { value: 'AUD', label: 'AUD (A$)' }
]

const commonTags = [
  'React', 'JavaScript', 'TypeScript', 'Python', 'Java', 'Node.js',
  'AWS', 'Docker', 'Kubernetes', 'SQL', 'MongoDB', 'GraphQL',
  'Remote', 'Full-time', 'Part-time', 'Contract', 'Startup', 'Enterprise'
]

export function AddJobModal({ onClose, onJobAdded }: AddJobModalProps) {
  const [formData, setFormData] = useState<JobFormData>(initialFormData)
  const [newTag, setNewTag] = useState('')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleInputChange = (field: keyof JobFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const addTag = (tag: string) => {
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }))
    }
    setNewTag('')
  }

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }))
  }

  const handleTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag(newTag.trim())
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Job title is required'
    }

    if (!formData.company.trim()) {
      newErrors.company = 'Company name is required'
    }

    if (formData.salary_min && formData.salary_max) {
      const minSalary = parseInt(formData.salary_min)
      const maxSalary = parseInt(formData.salary_max)
      if (minSalary > maxSalary) {
        newErrors.salary_max = 'Maximum salary must be greater than minimum salary'
      }
    }

    if (formData.application_url && !isValidUrl(formData.application_url)) {
      newErrors.application_url = 'Please enter a valid URL'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      const jobData = {
        ...formData,
        salary_min: formData.salary_min ? parseInt(formData.salary_min) : undefined,
        salary_max: formData.salary_max ? parseInt(formData.salary_max) : undefined,
        date_applied: formData.status === 'applied' ? new Date().toISOString() : undefined
      }

      const response = await apiClient.createJob(jobData)
      
      if (response.success && response.data) {
        onJobAdded(response.data as Job)
      } else {
        setErrors({ submit: response.error || 'Failed to create job' })
      }
    } catch (error) {
      setErrors({ submit: 'Failed to create job. Please try again.' })
      console.error('Error creating job:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Add New Job
            </h2>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <XMarkIcon className="h-5 w-5" />
            </Button>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Job Title *"
                  placeholder="e.g. Senior Frontend Developer"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  error={errors.title}
                />

                <Input
                  label="Company *"
                  placeholder="e.g. Google, Microsoft"
                  value={formData.company}
                  onChange={(e) => handleInputChange('company', e.target.value)}
                  error={errors.company}
                />
              </div>

              <Input
                label="Location"
                placeholder="e.g. San Francisco, CA or Remote"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                error={errors.location}
              />

              {/* Salary Information */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Min Salary"
                  type="number"
                  placeholder="80000"
                  value={formData.salary_min}
                  onChange={(e) => handleInputChange('salary_min', e.target.value)}
                  error={errors.salary_min}
                />

                <Input
                  label="Max Salary"
                  type="number"
                  placeholder="120000"
                  value={formData.salary_max}
                  onChange={(e) => handleInputChange('salary_max', e.target.value)}
                  error={errors.salary_max}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Currency
                  </label>
                  <select
                    value={formData.currency}
                    onChange={(e) => handleInputChange('currency', e.target.value)}
                    className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    {currencyOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Application URL */}
              <Input
                label="Application URL"
                type="url"
                placeholder="https://company.com/careers/job-id"
                value={formData.application_url}
                onChange={(e) => handleInputChange('application_url', e.target.value)}
                error={errors.application_url}
                helperText="Link to the job posting or application page"
              />

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Application Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => handleInputChange('status', e.target.value)}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  {statusOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Job Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Job Description
                </label>
                <textarea
                  rows={4}
                  placeholder="Paste the job description here..."
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tags
                </label>
                
                {/* Selected Tags */}
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {formData.tags.map((tag) => (
                      <Badge key={tag} variant="info" className="flex items-center gap-1">
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-1 hover:text-red-500"
                        >
                          <XMarkIcon className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Add Tag Input */}
                <div className="flex gap-2 mb-3">
                  <Input
                    placeholder="Add tag (e.g. React, Remote)"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={handleTagKeyPress}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => addTag(newTag.trim())}
                    disabled={!newTag.trim() || formData.tags.includes(newTag.trim())}
                  >
                    <PlusIcon className="h-4 w-4" />
                  </Button>
                </div>

                {/* Common Tags */}
                <div className="flex flex-wrap gap-2">
                  {commonTags
                    .filter(tag => !formData.tags.includes(tag))
                    .slice(0, 8)
                    .map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => addTag(tag)}
                        className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                      >
                        + {tag}
                      </button>
                    ))}
                </div>
              </div>

              {/* Error Message */}
              {errors.submit && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                  <p className="text-sm text-red-600 dark:text-red-400">{errors.submit}</p>
                </div>
              )}

              {/* Form Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button type="button" variant="secondary" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" loading={loading}>
                  Add Job
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}