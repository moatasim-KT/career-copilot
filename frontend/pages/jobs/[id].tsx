import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { Layout } from '@/components/Layout'
import { Card, CardContent, CardHeader, Button, Badge, Input } from '@/components/ui'
import { 
  ArrowLeftIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  ClockIcon,
  ArrowTopRightOnSquareIcon as ExternalLinkIcon,
  PencilIcon,
  TrashIcon,
  DocumentTextIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { apiClient } from '@/utils/api'
import { Job } from '@/types'
import { formatDate, formatSalary } from '@/utils/helpers'

export default function JobDetail() {
  const router = useRouter()
  const { id } = router.query
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const [notes, setNotes] = useState('')
  const [editingNotes, setEditingNotes] = useState(false)

  useEffect(() => {
    if (id) {
      fetchJob()
    }
  }, [id])

  const fetchJob = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.getJob(Number(id))
      
      if (response.success && response.data) {
        const jobData = response.data as Job
        setJob(jobData)
        setNotes(jobData.notes || '')
      } else {
        setError(response.error || 'Failed to fetch job details')
      }
    } catch (err) {
      setError('Failed to fetch job details')
      console.error('Error fetching job:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (newStatus: string) => {
    if (!job) return

    setUpdating(true)
    try {
      const response = await apiClient.updateJob(job.id, { 
        status: newStatus,
        date_applied: newStatus === 'applied' ? new Date().toISOString() : job.date_applied
      })
      
      if (response.success && response.data) {
        setJob(response.data as Job)
      }
    } catch (error) {
      console.error('Failed to update job status:', error)
    } finally {
      setUpdating(false)
    }
  }

  const handleNotesUpdate = async () => {
    if (!job) return

    try {
      const response = await apiClient.updateJob(job.id, { notes })
      
      if (response.success && response.data) {
        setJob(response.data as Job)
        setEditingNotes(false)
      }
    } catch (error) {
      console.error('Failed to update notes:', error)
    }
  }

  const handleDelete = async () => {
    if (!job || !confirm('Are you sure you want to delete this job?')) return
    
    try {
      const response = await apiClient.deleteJob(job.id)
      if (response.success) {
        router.push('/jobs')
      }
    } catch (error) {
      console.error('Failed to delete job:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      not_applied: { variant: 'default' as const, label: 'Not Applied' },
      applied: { variant: 'info' as const, label: 'Applied' },
      phone_screen: { variant: 'warning' as const, label: 'Phone Screen' },
      interview_scheduled: { variant: 'warning' as const, label: 'Interview Scheduled' },
      interviewed: { variant: 'warning' as const, label: 'Interviewed' },
      offer_received: { variant: 'success' as const, label: 'Offer Received' },
      rejected: { variant: 'danger' as const, label: 'Rejected' },
      withdrawn: { variant: 'default' as const, label: 'Withdrawn' },
      archived: { variant: 'default' as const, label: 'Archived' }
    }

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.not_applied
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const getSourceBadge = (source: string) => {
    const sourceConfig = {
      manual: { variant: 'default' as const, label: 'Manual' },
      scraped: { variant: 'info' as const, label: 'Scraped' },
      api: { variant: 'info' as const, label: 'API' },
      rss: { variant: 'info' as const, label: 'RSS' },
      referral: { variant: 'success' as const, label: 'Referral' }
    }

    const config = sourceConfig[source as keyof typeof sourceConfig] || sourceConfig.manual
    return <Badge variant={config.variant} size="sm">{config.label}</Badge>
  }

  if (loading) {
    return (
      <Layout title="Loading Job - Career Co-Pilot">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading job details...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (error || !job) {
    return (
      <Layout title="Job Not Found - Career Co-Pilot">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-red-600 dark:text-red-400 mb-4">{error || 'Job not found'}</p>
            <Button onClick={() => router.push('/jobs')}>
              Back to Jobs
            </Button>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout title={`${job.title} at ${job.company} - Career Co-Pilot`}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button 
            variant="ghost" 
            onClick={() => router.push('/jobs')}
            className="flex items-center"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Jobs
          </Button>

          <div className="flex gap-2">
            <Button variant="secondary" size="sm">
              <PencilIcon className="h-4 w-4 mr-2" />
              Edit
            </Button>
            <Button variant="danger" size="sm" onClick={handleDelete}>
              <TrashIcon className="h-4 w-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>

        {/* Job Header */}
        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {job.title}
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-400 font-medium mb-4">
                  {job.company}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {job.location && (
                    <div className="flex items-center">
                      <MapPinIcon className="h-4 w-4 mr-1" />
                      {job.location}
                    </div>
                  )}
                  
                  {(job.salary_min || job.salary_max) && (
                    <div className="flex items-center">
                      <CurrencyDollarIcon className="h-4 w-4 mr-1" />
                      {formatSalary(job.salary_min, job.salary_max, job.currency)}
                    </div>
                  )}
                  
                  {job.date_posted && (
                    <div className="flex items-center">
                      <CalendarIcon className="h-4 w-4 mr-1" />
                      Posted {formatDate(job.date_posted)}
                    </div>
                  )}

                  {job.date_applied && (
                    <div className="flex items-center">
                      <ClockIcon className="h-4 w-4 mr-1" />
                      Applied {formatDate(job.date_applied)}
                    </div>
                  )}
                </div>

                {/* Tags */}
                {job.tags && job.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {job.tags.map((tag, index) => (
                      <Badge key={index} variant="default" size="sm">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex flex-col items-end gap-3">
                {getStatusBadge(job.status)}
                {getSourceBadge(job.source)}
                
                {job.application_url && (
                  <Button 
                    size="sm"
                    onClick={() => window.open(job.application_url, '_blank')}
                  >
                    <ExternalLinkIcon className="h-4 w-4 mr-2" />
                    View Posting
                  </Button>
                )}
              </div>
            </div>

            {/* Recommendation Score */}
            {job.recommendation_score && (
              <div className="flex items-center justify-between p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center">
                  <ChartBarIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
                  <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Match Score: {Math.round(job.recommendation_score * 100)}%
                  </span>
                </div>
                <div className="w-32 bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                  <div 
                    className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full" 
                    style={{ width: `${job.recommendation_score * 100}%` }}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Job Description */}
            {job.description && (
              <Card>
                <CardHeader>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                    <DocumentTextIcon className="h-5 w-5 mr-2" />
                    Job Description
                  </h2>
                </CardHeader>
                <CardContent>
                  <div className="prose dark:prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-sans">
                      {job.description}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Notes */}
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Notes
                  </h2>
                  {!editingNotes ? (
                    <Button 
                      variant="secondary" 
                      size="sm"
                      onClick={() => setEditingNotes(true)}
                    >
                      <PencilIcon className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  ) : (
                    <div className="flex gap-2">
                      <Button 
                        variant="secondary" 
                        size="sm"
                        onClick={() => {
                          setNotes(job.notes || '')
                          setEditingNotes(false)
                        }}
                      >
                        Cancel
                      </Button>
                      <Button 
                        size="sm"
                        onClick={handleNotesUpdate}
                      >
                        Save
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {editingNotes ? (
                  <textarea
                    rows={6}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add your notes about this job opportunity..."
                    className="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                ) : (
                  <div className="min-h-[100px]">
                    {job.notes ? (
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-sans">
                        {job.notes}
                      </pre>
                    ) : (
                      <p className="text-gray-500 dark:text-gray-400 italic">
                        No notes added yet. Click Edit to add your thoughts about this opportunity.
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status Management */}
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Application Status
                </h2>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {['not_applied', 'applied', 'phone_screen', 'interview_scheduled', 'interviewed', 'offer_received', 'rejected'].map((status) => (
                    <button
                      key={status}
                      onClick={() => handleStatusUpdate(status)}
                      disabled={job.status === status || updating}
                      className={`w-full text-left p-3 rounded-md border transition-colors ${
                        job.status === status
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                      } ${updating ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <div className="flex items-center justify-between">
                        {getStatusBadge(status)}
                        {job.status === status && (
                          <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                            Current
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Job Metadata */}
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Job Information
                </h2>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Source:</span>
                    <span className="font-medium">{getSourceBadge(job.source)}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Added:</span>
                    <span className="font-medium">{formatDate(job.created_at)}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Updated:</span>
                    <span className="font-medium">{formatDate(job.updated_at)}</span>
                  </div>

                  {job.date_posted && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Posted:</span>
                      <span className="font-medium">{formatDate(job.date_posted)}</span>
                    </div>
                  )}

                  {job.date_applied && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Applied:</span>
                      <span className="font-medium">{formatDate(job.date_applied)}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  )
}