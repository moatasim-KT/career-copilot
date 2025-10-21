import { useState, useEffect } from 'react'
import { Layout } from '@/components/Layout'
import { Card, CardHeader, CardContent } from '@/components/ui'
import { MarketTrendsChart } from '@/components/MarketTrendsChart'
import { SalaryTrendsChart } from '@/components/SalaryTrendsChart'
import { IndustryDistributionChart } from '@/components/IndustryDistributionChart'
import { OpportunityAlerts } from '@/components/OpportunityAlerts'
import { MarketInsights } from '@/components/MarketInsights'
import { api } from '@/utils/api'

interface AnalyticsData {
  salary_trends?: any
  market_patterns?: any
  opportunity_alerts?: any[]
  summary?: {
    total_jobs_analyzed: number
    salary_growth_rate: number
    market_growth_rate: number
    active_alerts: number
    avg_salary: number
  }
}

export default function Analytics() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTimeframe, setSelectedTimeframe] = useState(90)

  useEffect(() => {
    fetchAnalyticsData()
  }, [selectedTimeframe])

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await api.get(`/analytics/market-trends-comprehensive?days=${selectedTimeframe}`)
      setAnalyticsData(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  const refreshAnalytics = () => {
    fetchAnalyticsData()
  }

  if (loading) {
    return (
      <Layout title="Analytics - Career Co-Pilot">
        <div className="space-y-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                  <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout title="Analytics - Career Co-Pilot">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Career Analytics
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Insights into your job search performance and market trends
            </p>
          </div>
          
          <Card>
            <CardContent>
              <div className="text-center py-8">
                <div className="text-red-500 mb-4">
                  <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Unable to Load Analytics
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
                <button
                  onClick={refreshAnalytics}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    )
  }

  const { summary } = analyticsData

  return (
    <Layout title="Analytics - Career Co-Pilot">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Career Analytics
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Insights into your job search performance and market trends
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(Number(e.target.value))}
              className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm"
            >
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={180}>Last 6 months</option>
              <option value={365}>Last year</option>
            </select>
            
            <button
              onClick={refreshAnalytics}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Jobs Analyzed</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {summary.total_jobs_analyzed.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-blue-500">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Avg Salary</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      ${summary.avg_salary.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-green-500">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Market Growth</p>
                    <p className={`text-2xl font-bold ${summary.market_growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {summary.market_growth_rate >= 0 ? '+' : ''}{(summary.market_growth_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className={summary.market_growth_rate >= 0 ? 'text-green-500' : 'text-red-500'}>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Active Alerts</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {summary.active_alerts}
                    </p>
                  </div>
                  <div className="text-orange-500">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM4 19h6v-2H4v2zM4 15h8v-2H4v2zM4 11h10V9H4v2z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Opportunity Alerts */}
        {analyticsData.opportunity_alerts && analyticsData.opportunity_alerts.length > 0 && (
          <OpportunityAlerts alerts={analyticsData.opportunity_alerts} />
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Market Trends Chart */}
          {analyticsData.market_patterns && (
            <MarketTrendsChart data={analyticsData.market_patterns} />
          )}

          {/* Salary Trends Chart */}
          {analyticsData.salary_trends && (
            <SalaryTrendsChart data={analyticsData.salary_trends} />
          )}

          {/* Industry Distribution */}
          {analyticsData.market_patterns?.industry_distribution && (
            <IndustryDistributionChart data={analyticsData.market_patterns.industry_distribution} />
          )}

          {/* Market Insights */}
          <MarketInsights 
            salaryInsights={analyticsData.salary_trends?.market_insights || []}
            marketInsights={analyticsData.market_patterns?.market_insights || []}
          />
        </div>
      </div>
    </Layout>
  )
}