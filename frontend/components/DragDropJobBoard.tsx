import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from './ui/Card'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'

interface Job {
  id: number
  title: string
  company: string
  status: string
  date_applied?: string
  location?: string
}

interface Column {
  id: string
  title: string
  jobs: Job[]
}

export function DragDropJobBoard() {
  const [columns, setColumns] = useState<Column[]>([
    { id: 'not_applied', title: 'Not Applied', jobs: [] },
    { id: 'applied', title: 'Applied', jobs: [] },
    { id: 'phone_screen', title: 'Phone Screen', jobs: [] },
    { id: 'interview_scheduled', title: 'Interview Scheduled', jobs: [] },
    { id: 'interviewed', title: 'Interviewed', jobs: [] },
    { id: 'offer_received', title: 'Offer Received', jobs: [] },
    { id: 'rejected', title: 'Rejected', jobs: [] }
  ])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading
    setTimeout(() => setLoading(false), 1000)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Job Board
        </h2>
        <Button>Add Job</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
        {columns.map((column) => (
          <Card key={column.id} className="min-h-[400px]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                  {column.title}
                </h3>
                <Badge variant="secondary" size="sm">
                  {column.jobs.length}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {column.jobs.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
                  No jobs in this stage
                </div>
              ) : (
                column.jobs.map((job) => (
                  <div
                    key={job.id}
                    className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                  >
                    <h4 className="font-medium text-sm text-gray-900 dark:text-white truncate">
                      {job.title}
                    </h4>
                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                      {job.company}
                    </p>
                    {job.location && (
                      <p className="text-xs text-gray-500 dark:text-gray-500 truncate mt-1">
                        {job.location}
                      </p>
                    )}
                    {job.date_applied && (
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        Applied: {new Date(job.date_applied).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        Drag and drop functionality coming soon! For now, use the job details page to update status.
      </div>
    </div>
  )
}