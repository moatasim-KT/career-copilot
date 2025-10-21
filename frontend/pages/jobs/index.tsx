import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/router'
import { Layout } from '@/components/Layout'
import { Card, CardContent, Button, Badge, Input } from '@/components/ui'
import { JobCard } from '@/components/JobCard'
import { JobFilters } from '@/components/JobFilters'
import { AdvancedJobFilters } from '@/components/AdvancedJobFilters'
import { DragDropJobBoard } from '@/components/DragDropJobBoard'
import { AddJobModal } from '@/components/AddJobModal'
import { ResponsiveStack, ResponsiveText, ResponsiveShow } from '@/components/ResponsiveContainer'
import { ResponsiveIcon } from '@/components/ResponsiveImage'
import { ResponsiveModal } from '@/components/ResponsiveModal'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  PlusIcon,
  AdjustmentsHorizontalIcon,
  Squares2X2Icon,
  ListBulletIcon
} from '@heroicons/react/24/outline'
import { apiClient } from '@/utils/api'
import { useResponsive } from '@/hooks/useResponsive'
import { Job, PaginatedResponse } from '@/types'

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

export default function Jobs() {
  const router = useRouter()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [viewMode, setViewMode] = useState<'list' | 'board'>('list')
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalJobs, setTotalJobs] = useState(0)
  const pageSize = 10

  // Filter state
  const [filters, setFilters] = useState<JobFiltersState>({
    search: '',
    status: '',
    location: '',
    company: '',
    salaryMin: '',
    salaryMax: '',
    source: '',
    tags: [],
    datePostedAfter: '',
    dateAppliedAfter: '',
    recommendationScoreMin: '',
    hasApplicationUrl: false,
    remoteOnly: false
  })

  const [appliedFilters, setAppliedFilters] = useState<JobFiltersState>(filters)

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const params: any = {
        page: currentPage,
        pageSize
      }

      // Add non-empty filters to params
      if (appliedFilters.search) params.search = appliedFilters.search
      if (appliedFilters.status) params.status = appliedFilters.status
      if (appliedFilters.location) params.location = appliedFilters.location
      if (appliedFilters.company) params.company = appliedFilters.company
      if (appliedFilters.salaryMin) params.salary_min = parseInt(appliedFilters.salaryMin)
      if (appliedFilters.salaryMax) params.salary_max = parseInt(appliedFilters.salaryMax)
      if (appliedFilters.source) params.source = appliedFilters.source
      if (appliedFilters.tags.length > 0) params.tags = appliedFilters.tags

      const response = await apiClient.getJobs(params)
      
      if (response.success && response.data) {
        const data = response.data as PaginatedResponse<Job>
        setJobs(data.items)
        setTotalPages(data.totalPages)
        setTotalJobs(data.total)
      } else {
        setError(response.error || 'Failed to fetch jobs')
      }
    } catch (err) {
      setError('Failed to fetch jobs')
      console.error('Error fetching jobs:', err)
    } finally {
      setLoading(false)
    }
  }, [currentPage, appliedFilters])

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  const handleSearch = () => {
    setAppliedFilters(filters)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    const emptyFilters = {
      search: '',
      status: '',
      location: '',
      company: '',
      salaryMin: '',
      salaryMax: '',
      source: '',
      tags: [],
      datePostedAfter: '',
      dateAppliedAfter: '',
      recommendationScoreMin: '',
      hasApplicationUrl: false,
      remoteOnly: false
    }
    setFilters(emptyFilters)
    setAppliedFilters(emptyFilters)
    setCurrentPage(1)
  }

  const handleJobUpdate = (updatedJob: Job) => {
    setJobs(prevJobs => 
      prevJobs.map(job => job.id === updatedJob.id ? updatedJob : job)
    )
  }

  const handleJobDelete = (jobId: number) => {
    setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId))
    setTotalJobs(prev => prev - 1)
  }

  const handleJobAdd = (newJob: Job) => {
    setJobs(prevJobs => [newJob, ...prevJobs])
    setTotalJobs(prev => prev + 1)
    setShowAddModal(false)
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const getActiveFiltersCount = () => {
    return Object.entries(appliedFilters).reduce((count, [key, value]) => {
      if (key === 'tags') {
        return count + (Array.isArray(value) ? value.length : 0)
      }
      if (typeof value === 'boolean') {
        return count + (value ? 1 : 0)
      }
      return count + (value ? 1 : 0)
    }, 0)
  }

  if (error) {
    return (
      <Layout title="Jobs - Career Co-Pilot">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
            <Button onClick={fetchJobs}>Try Again</Button>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout title="Jobs - Career Co-Pilot">
      <div className="space-y-6">
        {/* Header */}
        <ResponsiveStack direction="responsive" justify="between" align="start" spacing="md">
          <div>
            <ResponsiveText as="h1" size="3xl" weight="bold" color="primary">
              Job Opportunities
            </ResponsiveText>
            <ResponsiveText size="base" color="muted">
              {totalJobs > 0 ? `${totalJobs} jobs found` : 'Manage and track your job applications'}
            </ResponsiveText>
          </div>
          <div className="flex gap-2">
            {/* View Mode Toggle */}
            <div className="flex border border-gray-300 dark:border-gray-600 rounded-md">
              <Button
                variant={viewMode === 'list' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('list')}
                className="rounded-r-none"
              >
                <ListBulletIcon className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'board' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('board')}
                className="rounded-l-none"
              >
                <Squares2X2Icon className="h-4 w-4" />
              </Button>
            </div>
            <Button onClick={() => setShowAddModal(true)} className="w-full sm:w-auto touch-friendly">
              <ResponsiveIcon icon={PlusIcon} size="sm" className="mr-2" />
              Add Job
            </Button>
          </div>
        </ResponsiveStack>

        {/* Search and Filters */}
        <AdvancedJobFilters
          filters={filters}
          onFiltersChange={setFilters}
          onApply={handleSearch}
          onClear={handleClearFilters}
          showAdvanced={showAdvancedFilters}
          onToggleAdvanced={() => setShowAdvancedFilters(!showAdvancedFilters)}
        />

        {/* Job Content */}
        {loading ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading jobs...</p>
            </div>
          </div>
        ) : jobs.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <div className="text-gray-400 dark:text-gray-500 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2M8 6v10a2 2 0 002 2h4a2 2 0 002-2V6" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No jobs found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {getActiveFiltersCount() > 0 
                  ? 'Try adjusting your filters or search terms.'
                  : 'Get started by adding your first job opportunity.'
                }
              </p>
              <div className="flex justify-center gap-2">
                {getActiveFiltersCount() > 0 && (
                  <Button variant="secondary" onClick={handleClearFilters}>
                    Clear Filters
                  </Button>
                )}
                <Button onClick={() => setShowAddModal(true)}>
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Job
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : viewMode === 'board' ? (
          <DragDropJobBoard
            jobs={jobs}
            onJobUpdate={handleJobUpdate}
            onJobDelete={handleJobDelete}
            onJobClick={(job) => router.push(`/jobs/${job.id}`)}
          />
        ) : (
          <div className="space-y-4">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onUpdate={handleJobUpdate}
                onDelete={handleJobDelete}
                onClick={() => router.push(`/jobs/${job.id}`)}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <div className="flex gap-2">
              <Button 
                variant="secondary" 
                size="sm" 
                disabled={currentPage === 1}
                onClick={() => handlePageChange(currentPage - 1)}
              >
                Previous
              </Button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = i + 1
                const isActive = page === currentPage
                return (
                  <Button
                    key={page}
                    variant={isActive ? "primary" : "secondary"}
                    size="sm"
                    onClick={() => handlePageChange(page)}
                  >
                    {page}
                  </Button>
                )
              })}
              
              {totalPages > 5 && currentPage < totalPages - 2 && (
                <>
                  <span className="px-2 py-1 text-gray-500">...</span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handlePageChange(totalPages)}
                  >
                    {totalPages}
                  </Button>
                </>
              )}
              
              <Button 
                variant="secondary" 
                size="sm" 
                disabled={currentPage === totalPages}
                onClick={() => handlePageChange(currentPage + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Add Job Modal */}
      {showAddModal && (
        <AddJobModal
          onClose={() => setShowAddModal(false)}
          onJobAdded={handleJobAdd}
        />
      )}
    </Layout>
  )
}