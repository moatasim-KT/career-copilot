import { useState } from 'react'
import { Card, CardHeader, CardContent, Button, Badge, Input } from '@/components/ui'
import { 
  ChartBarIcon, 
  CalendarIcon, 
  DocumentTextIcon,
  FunnelIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { useApplicationHistory, useProgressStats } from '@/hooks/useProfile'
import { format } from 'date-fns'

export function ApplicationHistory() {
  const [filters, setFilters] = useState({
    status_filter: '',
    date_from: '',
    date_to: '',
    page: 1,
    per_page: 20
  })
  
  const { history, loading, error, refetch } = useApplicationHistory()
  const { stats, loading: statsLoading } = useProgressStats()

  const handleFilterChange = (field: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      page: 1 // Reset to first page when filtering
    }))
  }

  const applyFilters = () => {
    refetch(filters)
  }

  const clearFilters = () => {
    const clearedFilters = {
      status_filter: '',
      date_from: '',
      date_to: '',
      page: 1,
      per_page: 20
    }
    setFilters(clearedFilters)
    refetch(clearedFilters)
  }

  const getStatusColor = (status: string): "secondary" | "danger" | "warning" | "info" | "default" | "success" => {
    const statusColors: Record<string, "secondary" | "danger" | "warning" | "info" | "default" | "success"> = {
      'applied': 'info',
      'under_review': 'warning',
      'phone_screen_scheduled': 'warning',
      'phone_screen_completed': 'warning',
      'interview_scheduled': 'warning',
      'interview_completed': 'warning',
      'final_round': 'warning',
      'offer_received': 'success',
      'offer_accepted': 'success',
      'offer_declined': 'secondary',
      'rejected': 'danger',
      'withdrawn': 'secondary',
      'ghosted': 'danger'
    }
    return statusColors[status] || 'secondary'
  }

  const formatStatus = (status: string) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  if (loading && !history) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 dark:text-red-400">Error loading application history: {error}</p>
        <Button onClick={() => refetch()} className="mt-4">
          <ArrowPathIcon className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Progress Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <ChartBarIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Total Applications
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.total_applications}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
                  <span className="text-green-600 dark:text-green-400 font-bold text-sm">%</span>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Response Rate
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.response_rate}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <CalendarIcon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Interview Rate
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.interview_rate}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-yellow-100 dark:bg-yellow-900/20 rounded-full flex items-center justify-center">
                  <span className="text-yellow-600 dark:text-yellow-400 font-bold text-sm">★</span>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Offer Rate
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.offer_rate}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Filter Applications
            </h3>
            <div className="flex space-x-2">
              <Button onClick={applyFilters} variant="primary" size="sm">
                <FunnelIcon className="h-4 w-4 mr-2" />
                Apply Filters
              </Button>
              <Button onClick={clearFilters} variant="secondary" size="sm">
                Clear
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
              <select
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={filters.status_filter}
                onChange={(e) => handleFilterChange('status_filter', e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="applied">Applied</option>
                <option value="under_review">Under Review</option>
                <option value="phone_screen_scheduled">Phone Screen Scheduled</option>
                <option value="interview_scheduled">Interview Scheduled</option>
                <option value="offer_received">Offer Received</option>
                <option value="rejected">Rejected</option>
                <option value="withdrawn">Withdrawn</option>
              </select>
            </div>

            <Input
              label="From Date"
              type="date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
            />

            <Input
              label="To Date"
              type="date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Per Page</label>
              <select
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={filters.per_page}
                onChange={(e) => handleFilterChange('per_page', parseInt(e.target.value))}
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Application List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Application History
            </h3>
            {history && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Showing {history.applications.length} of {history.total_count} applications
              </p>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {history && history.applications.length > 0 ? (
            <div className="space-y-4">
              {history.applications.map((application: any) => (
                <div
                  key={application.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h4 className="text-lg font-medium text-gray-900 dark:text-white">
                          {application.job_title}
                        </h4>
                        <Badge variant={getStatusColor(application.status)}>
                          {formatStatus(application.status)}
                        </Badge>
                      </div>
                      
                      <p className="text-gray-600 dark:text-gray-400 mb-2">
                        {application.company_name}
                      </p>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center">
                          <CalendarIcon className="h-4 w-4 mr-1" />
                          Applied: {format(new Date(application.applied_at), 'MMM d, yyyy')}
                        </div>
                        
                        {application.response_date && (
                          <div className="flex items-center">
                            <CalendarIcon className="h-4 w-4 mr-1" />
                            Response: {format(new Date(application.response_date), 'MMM d, yyyy')}
                          </div>
                        )}
                        
                        {application.documents_count > 0 && (
                          <div className="flex items-center">
                            <DocumentTextIcon className="h-4 w-4 mr-1" />
                            {application.documents_count} document{application.documents_count !== 1 ? 's' : ''}
                          </div>
                        )}
                        
                        {application.interview_rounds > 0 && (
                          <div className="flex items-center">
                            <span className="text-purple-600 dark:text-purple-400">
                              {application.interview_rounds} interview{application.interview_rounds !== 1 ? 's' : ''}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      {application.notes && (
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 italic">
                          "{application.notes}"
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Pagination */}
              {history.total_count > history.per_page && (
                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Page {history.page} of {Math.ceil(history.total_count / history.per_page)}
                  </p>
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => {
                        const newFilters = { ...filters, page: filters.page - 1 }
                        setFilters(newFilters)
                        refetch(newFilters)
                      }}
                      disabled={history.page <= 1}
                      variant="secondary"
                      size="sm"
                    >
                      Previous
                    </Button>
                    <Button
                      onClick={() => {
                        const newFilters = { ...filters, page: filters.page + 1 }
                        setFilters(newFilters)
                        refetch(newFilters)
                      }}
                      disabled={history.page >= Math.ceil(history.total_count / history.per_page)}
                      variant="secondary"
                      size="sm"
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No applications found. Start applying to jobs to see your history here.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}