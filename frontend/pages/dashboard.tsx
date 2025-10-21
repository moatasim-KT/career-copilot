import { useState, useEffect } from 'react'
import { Layout } from '@/components/Layout'
import { Card, CardHeader, CardContent, Button, Badge } from '@/components/ui'
import { PersonalizedDashboard } from '@/components/PersonalizedDashboard'
import { ResponsiveGrid, ResponsiveStack, ResponsiveText, ResponsiveShow } from '@/components/ResponsiveContainer'
import { ResponsiveIcon } from '@/components/ResponsiveImage'
import { 
  BriefcaseIcon, 
  ChartBarIcon, 
  DocumentTextIcon,
  PlusIcon,
  UserIcon,
  TrendingUpIcon,
  Squares2X2Icon,
  ListBulletIcon
} from '@heroicons/react/24/outline'
import { useDashboardStats } from '@/hooks/useProfile'
import { useResponsive } from '@/hooks/useResponsive'
import Link from 'next/link'

export default function Dashboard() {
  const { stats, loading, error } = useDashboardStats()
  const { isMobile } = useResponsive()
  const [viewMode, setViewMode] = useState<'classic' | 'personalized'>('personalized')

  return (
    <Layout title="Dashboard - Career Co-Pilot" maxWidth="xl" padding="responsive">
      <div className="space-responsive-y">
        {/* Header */}
        <ResponsiveStack direction="responsive" justify="between" align="start" spacing="md">
          <div>
            <ResponsiveText as="h1" size="3xl" weight="bold" color="primary">
              Dashboard
            </ResponsiveText>
            <ResponsiveText size="base" color="muted">
              Welcome back! Here's your career overview.
            </ResponsiveText>
          </div>
          
          <ResponsiveStack direction={isMobile ? "vertical" : "horizontal"} spacing="sm" className="w-full sm:w-auto">
            {/* View Mode Toggle */}
            <div className="flex border border-gray-300 dark:border-gray-600 rounded-md">
              <Button
                variant={viewMode === 'classic' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('classic')}
                className="rounded-r-none"
              >
                <ListBulletIcon className="h-4 w-4 mr-1" />
                Classic
              </Button>
              <Button
                variant={viewMode === 'personalized' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('personalized')}
                className="rounded-l-none"
              >
                <Squares2X2Icon className="h-4 w-4 mr-1" />
                Custom
              </Button>
            </div>
            
            <Link href="/profile" className="w-full sm:w-auto">
              <Button variant="secondary" className="w-full sm:w-auto touch-friendly">
                <ResponsiveIcon icon={UserIcon} size="sm" className="mr-2" />
                Profile
              </Button>
            </Link>
            <Link href="/jobs" className="w-full sm:w-auto">
              <Button className="w-full sm:w-auto touch-friendly">
                <ResponsiveIcon icon={PlusIcon} size="sm" className="mr-2" />
                Add Job
              </Button>
            </Link>
          </ResponsiveStack>
        </ResponsiveStack>

        {/* Dashboard Content */}
        {viewMode === 'personalized' ? (
          <PersonalizedDashboard />
        ) : (
          <>
            {/* Profile Completion Alert */}
            {stats && stats.profile_completion < 80 && (
          <Card className="border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <UserIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                      Complete your profile to get better job recommendations
                    </p>
                    <p className="text-sm text-yellow-600 dark:text-yellow-400">
                      Your profile is {stats.profile_completion}% complete
                    </p>
                  </div>
                </div>
                <Link href="/profile">
                  <Button variant="warning" size="sm">
                    Complete Profile
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Cards */}
        {loading ? (
          <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 4 }} gap="md">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardContent className="card-responsive">
                  <div className="animate-pulse">
                    <div className="flex items-center">
                      <div className="h-8 w-8 bg-gray-300 dark:bg-gray-600 rounded"></div>
                      <div className="ml-4 flex-1">
                        <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
                        <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded"></div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </ResponsiveGrid>
        ) : stats ? (
          <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 4 }} gap="md">
            <Card>
              <CardContent className="card-responsive">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ResponsiveIcon icon={BriefcaseIcon} size="lg" className="text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="ml-4">
                    <ResponsiveText size="sm" color="muted" className="font-medium">
                      Total Applications
                    </ResponsiveText>
                    <ResponsiveText size="2xl" weight="bold" color="primary">
                      {stats.total_applications}
                    </ResponsiveText>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="card-responsive">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ResponsiveIcon icon={TrendingUpIcon} size="lg" className="text-green-600 dark:text-green-400" />
                  </div>
                  <div className="ml-4">
                    <ResponsiveText size="sm" color="muted" className="font-medium">
                      This Week
                    </ResponsiveText>
                    <ResponsiveText size="2xl" weight="bold" color="primary">
                      {stats.applications_this_week}
                    </ResponsiveText>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="card-responsive">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ResponsiveIcon icon={ChartBarIcon} size="lg" className="text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="ml-4">
                    <ResponsiveText size="sm" color="muted" className="font-medium">
                      Interview Rate
                    </ResponsiveText>
                    <ResponsiveText size="2xl" weight="bold" color="primary">
                      {stats.interview_rate}%
                    </ResponsiveText>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="card-responsive">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ResponsiveIcon icon={DocumentTextIcon} size="lg" className="text-yellow-600 dark:text-yellow-400" />
                  </div>
                  <div className="ml-4">
                    <ResponsiveText size="sm" color="muted" className="font-medium">
                      Documents
                    </ResponsiveText>
                    <ResponsiveText size="2xl" weight="bold" color="primary">
                      {stats.total_documents}
                    </ResponsiveText>
                  </div>
                </div>
              </CardContent>
            </Card>
          </ResponsiveGrid>
        ) : (
          <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 4 }} gap="md">
            <Card>
              <CardContent className="card-responsive">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <p>Unable to load statistics</p>
                </div>
              </CardContent>
            </Card>
          </ResponsiveGrid>
        )}

        {/* Weekly Progress and Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weekly Goal Progress */}
          {stats && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Weekly Goal Progress
                </h3>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600 dark:text-gray-400">Applications Goal</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {stats.applications_this_week} / 5
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(stats.weekly_goal_progress, 100)}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {stats.weekly_goal_progress}% complete
                    </p>
                  </div>

                  {/* Application Status Distribution */}
                  {stats.status_distribution && Object.keys(stats.status_distribution).length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                        Application Status
                      </h4>
                      <div className="space-y-2">
                        {Object.entries(stats.status_distribution).slice(0, 3).map(([status, count]) => (
                          <div key={status} className="flex justify-between text-sm">
                            <span className="text-gray-600 dark:text-gray-400 capitalize">
                              {status.replace('_', ' ')}
                            </span>
                            <span className="font-medium text-gray-900 dark:text-white">
                              {count}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Quick Actions
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Link href="/jobs">
                  <Button variant="outline" className="w-full justify-start">
                    <BriefcaseIcon className="h-4 w-4 mr-3" />
                    Browse Job Opportunities
                  </Button>
                </Link>
                
                <Link href="/profile?tab=history">
                  <Button variant="outline" className="w-full justify-start">
                    <ChartBarIcon className="h-4 w-4 mr-3" />
                    View Application History
                  </Button>
                </Link>
                
                <Link href="/profile?tab=documents">
                  <Button variant="outline" className="w-full justify-start">
                    <DocumentTextIcon className="h-4 w-4 mr-3" />
                    Manage Documents
                  </Button>
                </Link>
                
                <Link href="/profile">
                  <Button variant="outline" className="w-full justify-start">
                    <UserIcon className="h-4 w-4 mr-3" />
                    Update Profile
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Weekly Trend Chart */}
        {stats && stats.weekly_trend && stats.weekly_trend.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Application Trend (Last 4 Weeks)
              </h3>
            </CardHeader>
            <CardContent>
              <div className="flex items-end space-x-2 h-32">
                {stats.weekly_trend.map((week: any, index: number) => (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div 
                      className="w-full bg-blue-600 rounded-t transition-all duration-300 min-h-[4px]"
                      style={{ 
                        height: `${Math.max((week.applications / Math.max(...stats.weekly_trend.map((w: any) => w.applications), 1)) * 100, 4)}%` 
                      }}
                    ></div>
                    <div className="mt-2 text-center">
                      <p className="text-xs font-medium text-gray-900 dark:text-white">
                        {week.applications}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Week {index + 1}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
          </>
        )}
      </div>
    </Layout>
  )
}