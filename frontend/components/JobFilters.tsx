import { useState } from 'react'
import { Input, Button, Badge } from '@/components/ui'
import { XMarkIcon } from '@heroicons/react/24/outline'

interface JobFiltersProps {
  filters: {
    search: string
    status: string
    location: string
    company: string
    salaryMin: string
    salaryMax: string
    source: string
    tags: string[]
  }
  onFiltersChange: (filters: any) => void
  onApply: () => void
  onClear: () => void
}

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'not_applied', label: 'Not Applied' },
  { value: 'applied', label: 'Applied' },
  { value: 'phone_screen', label: 'Phone Screen' },
  { value: 'interview_scheduled', label: 'Interview Scheduled' },
  { value: 'interviewed', label: 'Interviewed' },
  { value: 'offer_received', label: 'Offer Received' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'withdrawn', label: 'Withdrawn' },
  { value: 'archived', label: 'Archived' }
]

const sourceOptions = [
  { value: '', label: 'All Sources' },
  { value: 'manual', label: 'Manual' },
  { value: 'scraped', label: 'Scraped' },
  { value: 'api', label: 'API' },
  { value: 'rss', label: 'RSS' },
  { value: 'referral', label: 'Referral' }
]

const commonTags = [
  'React', 'JavaScript', 'TypeScript', 'Python', 'Java', 'Node.js',
  'AWS', 'Docker', 'Kubernetes', 'SQL', 'MongoDB', 'GraphQL',
  'Remote', 'Full-time', 'Part-time', 'Contract', 'Startup', 'Enterprise'
]

export function JobFilters({ filters, onFiltersChange, onApply, onClear }: JobFiltersProps) {
  const [newTag, setNewTag] = useState('')

  const handleFilterChange = (key: string, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    })
  }

  const addTag = (tag: string) => {
    if (tag && !filters.tags.includes(tag)) {
      handleFilterChange('tags', [...filters.tags, tag])
    }
    setNewTag('')
  }

  const removeTag = (tagToRemove: string) => {
    handleFilterChange('tags', filters.tags.filter(tag => tag !== tagToRemove))
  }

  const handleTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag(newTag.trim())
    }
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Status
          </label>
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:focus:border-blue-400 dark:focus:ring-blue-400"
          >
            {statusOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Location Filter */}
        <div>
          <Input
            label="Location"
            placeholder="e.g. San Francisco, Remote"
            value={filters.location}
            onChange={(e) => handleFilterChange('location', e.target.value)}
          />
        </div>

        {/* Company Filter */}
        <div>
          <Input
            label="Company"
            placeholder="e.g. Google, Microsoft"
            value={filters.company}
            onChange={(e) => handleFilterChange('company', e.target.value)}
          />
        </div>

        {/* Salary Min */}
        <div>
          <Input
            label="Min Salary"
            type="number"
            placeholder="e.g. 80000"
            value={filters.salaryMin}
            onChange={(e) => handleFilterChange('salaryMin', e.target.value)}
          />
        </div>

        {/* Salary Max */}
        <div>
          <Input
            label="Max Salary"
            type="number"
            placeholder="e.g. 150000"
            value={filters.salaryMax}
            onChange={(e) => handleFilterChange('salaryMax', e.target.value)}
          />
        </div>

        {/* Source Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Source
          </label>
          <select
            value={filters.source}
            onChange={(e) => handleFilterChange('source', e.target.value)}
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:focus:border-blue-400 dark:focus:ring-blue-400"
          >
            {sourceOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tags Section */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Tags
        </label>
        
        {/* Selected Tags */}
        {filters.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {filters.tags.map((tag) => (
              <Badge key={tag} variant="info" className="flex items-center gap-1">
                {tag}
                <button
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
            variant="secondary"
            size="sm"
            onClick={() => addTag(newTag.trim())}
            disabled={!newTag.trim() || filters.tags.includes(newTag.trim())}
          >
            Add
          </Button>
        </div>

        {/* Common Tags */}
        <div className="flex flex-wrap gap-2">
          {commonTags
            .filter(tag => !filters.tags.includes(tag))
            .slice(0, 8)
            .map((tag) => (
              <button
                key={tag}
                onClick={() => addTag(tag)}
                className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                + {tag}
              </button>
            ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Button variant="secondary" onClick={onClear}>
          Clear All Filters
        </Button>
        <div className="flex gap-2">
          <Button variant="primary" onClick={onApply}>
            Apply Filters
          </Button>
        </div>
      </div>
    </div>
  )
}