import { useState, useRef } from 'react'
import { Card, CardContent, Button, Badge } from '@/components/ui'
import { 
  MapPinIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon,
  ArrowTopRightOnSquareIcon as ExternalLinkIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { Job } from '@/types'
import { apiClient } from '@/utils/api'
import { formatDate, formatSalary } from '@/utils/helpers'
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation'
import { useAccessibility } from '@/contexts/AccessibilityContext'
import { ScreenReader } from '@/utils/accessibility'

interface JobCardProps {
  job: Job
  onUpdate: (job: Job) => void
  onDelete: (jobId: number) => void
  onClick: () => void
}

export function JobCard({ job, onUpdate, onDelete, onClick }: JobCardProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [updating, setUpdating] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)
  const { announceToScreenReader } = useAccessibility()

  // Generate accessible description for screen readers
  const jobDescription = ScreenReader.generateJobCardDescription(job)

  useKeyboardNavigation(cardRef, {
    enableEscape: showMenu,
    onEscape: () => setShowMenu(false),
    onEnter: () => onClick()
  })

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

  const handleStatusUpdate = async (newStatus: string) => {
    setUpdating(true)
    const oldStatus = job.status
    
    try {
      const response = await apiClient.updateJob(job.id, { 
        status: newStatus,
        date_applied: newStatus === 'applied' ? new Date().toISOString() : job.date_applied
      })
      
      if (response.success && response.data) {
        onUpdate(response.data as Job)
        announceToScreenReader(
          ScreenReader.generateStatusAnnouncement(
            `Updated job status from ${oldStatus.replace('_', ' ')} to ${newStatus.replace('_', ' ')}`,
            job.title,
            true
          )
        )
      }
    } catch (error) {
      console.error('Failed to update job status:', error)
      announceToScreenReader(
        ScreenReader.generateStatusAnnouncement('update job status', job.title, false)
      )
    } finally {
      setUpdating(false)
      setShowMenu(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete the job "${job.title}" at ${job.company}?`)) return
    
    try {
      const response = await apiClient.deleteJob(job.id)
      if (response.success) {
        onDelete(job.id)
        announceToScreenReader(
          ScreenReader.generateStatusAnnouncement('delete job', `${job.title} at ${job.company}`, true)
        )
      }
    } catch (error) {
      console.error('Failed to delete job:', error)
      announceToScreenReader(
        ScreenReader.generateStatusAnnouncement('delete job', `${job.title} at ${job.company}`, false)
      )
    }
  }

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger onClick if clicking on interactive elements
    if ((e.target as HTMLElement).closest('button, a')) {
      return
    }
    onClick()
  }

  return (
    <Card 
      ref={cardRef}
      className="hover:shadow-md transition-shadow cursor-pointer relative focus-within:ring-2 focus-within:ring-blue-500"
      interactive
      role="article"
      aria-label={jobDescription}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
    >
      <CardContent className="p-6" onClick={handleCardClick}>
        <div className="flex justify-between items-start">
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="min-w-0 flex-1">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                  {job.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 font-medium truncate">
                  {job.company}
                </p>
              </div>
              <div className="flex items-center gap-2 ml-4">
                {getStatusBadge(job.status)}
                {getSourceBadge(job.source)}
              </div>
            </div>

            {/* Job Details */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
              {job.location && (
                <div className="flex items-center">
                  <MapPinIcon className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span className="truncate">{job.location}</span>
                </div>
              )}
              
              {(job.salary_min || job.salary_max) && (
                <div className="flex items-center">
                  <CurrencyDollarIcon className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span>{formatSalary(job.salary_min, job.salary_max, job.currency)}</span>
                </div>
              )}
              
              {job.date_posted && (
                <div className="flex items-center">
                  <CalendarIcon className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span>Posted {formatDate(job.date_posted)}</span>
                </div>
              )}

              {job.date_applied && (
                <div className="flex items-center">
                  <ClockIcon className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span>Applied {formatDate(job.date_applied)}</span>
                </div>
              )}
            </div>

            {/* Tags */}
            {job.tags && job.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {job.tags.slice(0, 5).map((tag, index) => (
                  <Badge key={index} variant="default" size="sm">
                    {tag}
                  </Badge>
                ))}
                {job.tags.length > 5 && (
                  <Badge variant="default" size="sm">
                    +{job.tags.length - 5} more
                  </Badge>
                )}
              </div>
            )}

            {/* Recommendation Score */}
            {job.recommendation_score && (
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <span className="mr-2">Match Score:</span>
                <div className="flex items-center">
                  <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${(job.recommendation_score * 100)}%` }}
                    />
                  </div>
                  <span className="font-medium">{Math.round(job.recommendation_score * 100)}%</span>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="ml-4 flex flex-col gap-2 relative">
            <Button 
              size="sm" 
              onClick={onClick}
              aria-label={`View details for ${job.title} at ${job.company}`}
            >
              View Details
            </Button>
            
            {job.application_url && (
              <Button 
                variant="secondary" 
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  window.open(job.application_url, '_blank')
                }}
                aria-label={`Apply to ${job.title} at ${job.company} (opens in new tab)`}
              >
                <ExternalLinkIcon className="h-4 w-4 mr-1" aria-hidden="true" />
                Apply
              </Button>
            )}

            {/* Quick Status Updates */}
            {job.status === 'not_applied' && (
              <Button 
                variant="secondary" 
                size="sm"
                loading={updating}
                loadingText={`Marking ${job.title} as applied`}
                onClick={(e) => {
                  e.stopPropagation()
                  handleStatusUpdate('applied')
                }}
                aria-label={`Mark ${job.title} at ${job.company} as applied`}
              >
                Mark Applied
              </Button>
            )}

            {/* Menu Button */}
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowMenu(!showMenu)
                }}
                aria-label={`More actions for ${job.title} at ${job.company}`}
                aria-expanded={showMenu}
                aria-haspopup="menu"
              >
                <EllipsisVerticalIcon className="h-4 w-4" aria-hidden="true" />
              </Button>

              {/* Dropdown Menu */}
              {showMenu && (
                <div 
                  className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg z-10"
                  role="menu"
                  aria-label={`Actions for ${job.title} at ${job.company}`}
                >
                  <div className="py-1">
                    <button
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center focus:outline-none focus:bg-gray-100 dark:focus:bg-gray-700"
                      onClick={(e) => {
                        e.stopPropagation()
                        // TODO: Open edit modal
                        setShowMenu(false)
                      }}
                      role="menuitem"
                      aria-label={`Edit ${job.title} at ${job.company}`}
                    >
                      <PencilIcon className="h-4 w-4 mr-2" aria-hidden="true" />
                      Edit Job
                    </button>
                    
                    <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                    
                    {/* Status Update Options */}
                    <div className="px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                      Update Status
                    </div>
                    
                    {['not_applied', 'applied', 'phone_screen', 'interview_scheduled', 'interviewed', 'offer_received', 'rejected'].map((status) => (
                      <button
                        key={status}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStatusUpdate(status)
                        }}
                        disabled={job.status === status}
                      >
                        {getStatusBadge(status).props.children}
                        {job.status === status && (
                          <span className="ml-2 text-xs text-gray-500">(current)</span>
                        )}
                      </button>
                    ))}
                    
                    <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                    
                    <button
                      className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete()
                      }}
                    >
                      <TrashIcon className="h-4 w-4 mr-2" />
                      Delete Job
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>

      {/* Click outside to close menu */}
      {showMenu && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setShowMenu(false)}
        />
      )}
    </Card>
  )
}