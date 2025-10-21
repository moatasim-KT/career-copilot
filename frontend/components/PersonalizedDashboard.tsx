import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'

interface DashboardWidget {
  id: string
  type: 'stats' | 'chart' | 'list' | 'progress'
  title: string
  position: { x: number; y: number }
  size: { width: number; height: number }
  data?: any
}

export function PersonalizedDashboard() {
  const [widgets, setWidgets] = useState<DashboardWidget[]>([
    {
      id: 'applications-stats',
      type: 'stats',
      title: 'Application Stats',
      position: { x: 0, y: 0 },
      size: { width: 2, height: 1 },
      data: { total: 25, thisWeek: 5, interviewRate: 20 }
    },
    {
      id: 'recent-applications',
      type: 'list',
      title: 'Recent Applications',
      position: { x: 2, y: 0 },
      size: { width: 2, height: 2 },
      data: []
    },
    {
      id: 'goals-progress',
      type: 'progress',
      title: 'Goals Progress',
      position: { x: 0, y: 1 },
      size: { width: 2, height: 1 },
      data: { completed: 3, total: 5 }
    }
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
          Personalized Dashboard
        </h2>
        <Button variant="secondary">Customize Layout</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {widgets.map((widget) => (
          <Card 
            key={widget.id} 
            className={`
              ${widget.size.width === 2 ? 'md:col-span-2' : ''}
              ${widget.size.height === 2 ? 'row-span-2' : ''}
            `}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                  {widget.title}
                </h3>
                <Badge variant="secondary" size="sm">
                  {widget.type}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {widget.type === 'stats' && widget.data && (
                <div className="space-y-2">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {widget.data.total}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {widget.data.thisWeek} this week
                  </div>
                  <div className="text-sm text-green-600">
                    {widget.data.interviewRate}% interview rate
                  </div>
                </div>
              )}
              
              {widget.type === 'progress' && widget.data && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>{widget.data.completed}/{widget.data.total}</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${(widget.data.completed / widget.data.total) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              
              {widget.type === 'list' && (
                <div className="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
                  No recent applications
                </div>
              )}
              
              {widget.type === 'chart' && (
                <div className="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
                  Chart placeholder
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        Drag and drop customization coming soon! For now, widgets are arranged in a fixed grid.
      </div>
    </div>
  )
}