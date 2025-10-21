import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, Button, Badge, Input } from '@/components/ui'
import { 
  MagnifyingGlassIcon,
  BookmarkIcon,
  TrashIcon,
  PlusIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon,
  StarIcon
} from '@heroicons/react/24/outline'
import { BookmarkIcon as BookmarkSolidIcon, StarIcon as StarSolidIcon } from '@heroicons/react/24/solid'
import { apiClient } from '@/utils/api'

interface JobFiltersState {
  search: string
  status: string
  location: string
  company: string
  salaryMin: string
  salaryMax: string
  source: string
  tags: string[]
  datePostedAfter: string
  dateAppliedAfter: string
  recommendationScoreMin: string
  hasApplicationUrl: boolean
  remoteOnly: boolean
}

interface SavedSearch {
  id: string
  name: string
  filters: JobFiltersState
  isDefault: boolean
  createdAt: string
  lastUsed: string
}

interface AdvancedJobFiltersProps {
  filters: JobFiltersState
  onFiltersChange: (filters: JobFiltersState) => void
  onApply: () => void
  onClear: () => void
  showAdvanced?: boolean
  onToggleAdvanced?: () => void
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

const quickFilters = [
  { name: 'Not Applied', filters: { status: 'not_applied' } },
  { name: 'Applied This Week', filters: { status: 'applied', dateAppliedAfter: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] } },
  { name: 'High Match Score', filters: { recommendationScoreMin: '0.8' } },
  { name: 'Remote Only', filters: { remoteOnly: true } },
  { name: 'Posted This Week', filters: { datePostedAfter: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] } },
  { name: 'Has Application Link', filters: { hasApplicationUrl: true } }
]

export function AdvancedJobFilters({ 
  filters, 
  onFiltersChange, 
  onApply, 
  onClear,
  showAdvanced = false,
  onToggleAdvanced
}: AdvancedJobFiltersProps) {
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [saveSearchName, setSaveSearchName] = useState('')
  const [newTag, setNewTag] = useState('')
  const [loading, setLoading] = useState(false)

  // Load saved searches on component mount
  useEffect(() => {
    loadSavedSearches()
  }, [])

  const loadSavedSearches = async () => {
    try {
      const response = await apiClient.getSavedSearches()
      if (response.success && response.data) {
        setSavedSearches(response.data as SavedSearch[])
      }
    } catch (error) {
      console.error('Failed to load saved searches:', error)
    }
  }

  const handleFilterChange = (key: keyof JobFiltersState, value: any) => {
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

  const applyQuickFilter = (quickFilter: typeof quickFilters[0]) => {
    const newFilters = { ...filters }
    Object.entries(quickFilter.filters).forEach(([key, value]) => {
      (newFilters as any)[key] = value
    })
    onFiltersChange(newFilters)
    onApply()
  }

  const saveCurrentSearch = async () => {
    if (!saveSearchName.trim()) return

    setLoading(true)
    try {
      const newSearch: Omit<SavedSearch, 'id' | 'createdAt' | 'lastUsed'> = {
        name: saveSearchName.trim(),
        filters: filters,
        isDefault: false
      }

      const response = await apiClient.saveSearch(newSearch)
      if (response.success && response.data) {
        setSavedSearches([...savedSearches, response.data as SavedSearch])
        setSaveSearchName('')
        setShowSaveModal(false)
      }
    } catch (error) {
      console.error('Failed to save search:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSavedSearch = async (search: SavedSearch) => {
    onFiltersChange(search.filters)
    onApply()

    // Update last used timestamp
    try {
      await apiClient.updateSearchLastUsed(search.id)
      setSavedSearches(savedSearches.map(s => 
        s.id === search.id ? { ...s, lastUsed: new Date().toISOString() } : s
      ))
    } catch (error) {
      console.error('Failed to update search last used:', error)
    }
  }

  const deleteSavedSearch = async (searchId: string) => {
    try {
      const response = await apiClient.deleteSavedSearch(searchId)
      if (response.success) {
        setSavedSearches(savedSearches.filter(s => s.id !== searchId))
      }
    } catch (error) {
      console.error('Failed to delete saved search:', error)
    }
  }

  const toggleDefaultSearch = async (searchId: string) => {
    try {
      const response = await apiClient.toggleDefaultSearch(searchId)
      if (response.success) {
        setSavedSearches(savedSearches.map(s => ({
          ...s,
          isDefault: s.id === searchId ? !s.isDefault : false
        })))
      }
    } catch (error) {
      console.error('Failed to toggle default search:', error)
    }
  }

  const getActiveFiltersCount = () => {
    return Object.entries(filters).reduce((count, [key, value]) => {
      if (key === 'tags') {
        return count + (Array.isArray(value) ? value.length : 0)
      }
      if (typeof value === 'boolean') {
        return count + (value ? 1 : 0)
      }
      return count + (value ? 1 : 0)
    }, 0)
  }

  return (
    <div className="space-y-4">
      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        {quickFilters.map((quickFilter) => (
          <Button
            key={quickFilter.name}
            variant="secondary"
            size="sm"
            onClick={() => applyQuickFilter(quickFilter)}
            className="text-xs"
          >
            {quickFilter.name}
          </Button>
        ))}
      </div>

      {/* Saved Searches */}
      {savedSearches.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900 dark:text-white">Saved Searches</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSaveModal(true)}
              >
                <BookmarkIcon className="h-4 w-4 mr-1" />
                Save Current
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex flex-wrap gap-2">
              {savedSearches.map((search) => (
                <div key={search.id} className="flex items-center gap-1">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => loadSavedSearch(search)}
                    className="flex items-center gap-1"
                  >
                    {search.isDefault ? (
                      <StarSolidIcon className="h-3 w-3 text-yellow-500" />
                    ) : (
                      <BookmarkSolidIcon className="h-3 w-3" />
                    )}
                    {search.name}
                  </Button>
                  <div className="flex">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleDefaultSearch(search.id)}
                      className="p-1 h-6 w-6"
                    >
                      {search.isDefault ? (
                        <StarSolidIcon className="h-3 w-3 text-yellow-500" />
                      ) : (
                        <StarIcon className="h-3 w-3" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteSavedSearch(search.id)}
                      className="p-1 h-6 w-6 text-red-600 hover:text-red-700"
                    >
                      <TrashIcon className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  placeholder="Search jobs, companies, or skills..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && onApply()}
                />
              </div>
              <Button onClick={onApply}>
                <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
                Search
              </Button>
              {onToggleAdvanced && (
                <Button
                  variant="secondary"
                  onClick={onToggleAdvanced}
                >
                  <AdjustmentsHorizontalIcon className="h-4 w-4 mr-2" />
                  {showAdvanced ? 'Simple' : 'Advanced'}
                  {getActiveFiltersCount() > 0 && (
                    <Badge variant="info" size="sm" className="ml-2">
                      {getActiveFiltersCount()}
                    </Badge>
                  )}
                </Button>
              )}
            </div>

            {/* Advanced Filters */}
            {showAdvanced && (
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
                      className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
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
                      className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    >
                      {sourceOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Date Posted After */}
                  <div>
                    <Input
                      label="Posted After"
                      type="date"
                      value={filters.datePostedAfter}
                      onChange={(e) => handleFilterChange('datePostedAfter', e.target.value)}
                    />
                  </div>

                  {/* Date Applied After */}
                  <div>
                    <Input
                      label="Applied After"
                      type="date"
                      value={filters.dateAppliedAfter}
                      onChange={(e) => handleFilterChange('dateAppliedAfter', e.target.value)}
                    />
                  </div>

                  {/* Recommendation Score Min */}
                  <div>
                    <Input
                      label="Min Match Score (%)"
                      type="number"
                      min="0"
                      max="100"
                      placeholder="e.g. 80"
                      value={filters.recommendationScoreMin}
                      onChange={(e) => handleFilterChange('recommendationScoreMin', e.target.value)}
                    />
                  </div>
                </div>

                {/* Boolean Filters */}
                <div className="mt-4 space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.hasApplicationUrl}
                      onChange={(e) => handleFilterChange('hasApplicationUrl', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Has application link
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.remoteOnly}
                      onChange={(e) => handleFilterChange('remoteOnly', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Remote positions only
                    </span>
                  </label>
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
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex gap-2">
                <Button variant="secondary" onClick={onClear}>
                  Clear All
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setShowSaveModal(true)}
                  disabled={getActiveFiltersCount() === 0}
                >
                  <BookmarkIcon className="h-4 w-4 mr-1" />
                  Save Search
                </Button>
              </div>
              <Button onClick={onApply}>
                Apply Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Search Modal */}
      {showSaveModal && (
        <Card className="border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20">
          <CardContent className="p-4">
            <h4 className="font-medium text-gray-900 dark:text-white mb-3">Save Current Search</h4>
            <div className="flex items-center gap-2">
              <Input
                placeholder="Search name"
                value={saveSearchName}
                onChange={(e) => setSaveSearchName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveCurrentSearch()
                  if (e.key === 'Escape') setShowSaveModal(false)
                }}
                className="flex-1"
                autoFocus
              />
              <Button onClick={saveCurrentSearch} loading={loading}>
                Save
              </Button>
              <Button variant="secondary" onClick={() => setShowSaveModal(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}