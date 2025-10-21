import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Layout } from '@/components/Layout'
import { Card, CardContent, Button } from '@/components/ui'
import { 
  BriefcaseIcon, 
  ChartBarIcon, 
  DocumentTextIcon,
  ArrowRightIcon 
} from '@heroicons/react/24/outline'

interface ApiStatus {
  message: string
  version: string
  status: string
}

export default function Home() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/`)
        const data = await response.json()
        setApiStatus(data)
      } catch (error) {
        console.error('Failed to connect to API:', error)
      } finally {
        setLoading(false)
      }
    }

    checkApiStatus()
  }, [])

  return (
    <Layout title="Career Co-Pilot - Intelligent Career Management">
      <div className="space-y-12">
        {/* Hero Section */}
        <div className="text-center py-12">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
            Career Co-Pilot
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-400 mb-8 max-w-3xl mx-auto">
            Your intelligent career management companion that consolidates job tracking, 
            automates discovery, and provides personalized insights.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="lg">
                Get Started
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/jobs">
              <Button variant="secondary" size="lg">
                View Jobs
              </Button>
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="text-center p-8">
            <CardContent>
              <div className="mx-auto h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mb-4">
                <BriefcaseIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Job Management
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Centralize all your job opportunities and track applications in one place
              </p>
            </CardContent>
          </Card>

          <Card className="text-center p-8">
            <CardContent>
              <div className="mx-auto h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center mb-4">
                <ChartBarIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Smart Analytics
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get insights into your job search patterns and success rates
              </p>
            </CardContent>
          </Card>

          <Card className="text-center p-8">
            <CardContent>
              <div className="mx-auto h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center mb-4">
                <DocumentTextIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Document Management
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Organize resumes, cover letters, and track application materials
              </p>
            </CardContent>
          </Card>
        </div>

        {/* System Status */}
        <Card className="max-w-md mx-auto">
          <CardContent className="p-6 text-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              System Status
            </h2>
            
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Checking API...</span>
              </div>
            ) : apiStatus ? (
              <div className="space-y-2">
                <div className="flex items-center justify-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 dark:text-green-400 font-medium">API Connected</span>
                </div>
                <p className="text-gray-600 dark:text-gray-400">Version: {apiStatus.version}</p>
                <p className="text-gray-600 dark:text-gray-400">Status: {apiStatus.status}</p>
              </div>
            ) : (
              <div className="flex items-center justify-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                <span className="text-red-600 dark:text-red-400 font-medium">API Disconnected</span>
              </div>
            )}
            
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400">
              <p>Frontend: Running on port 3000</p>
              <p>Backend API: {process.env.NEXT_PUBLIC_API_URL}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}