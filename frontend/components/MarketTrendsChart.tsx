import { Card, CardHeader, CardContent } from '@/components/ui'

interface MarketTrendsChartProps {
  data: {
    chart_data?: {
      jobs_over_time?: Array<{ date: string; count: number }>
      weekly_trend?: Array<{ week: string; count: number }>
    }
    growth_metrics?: {
      weekly_growth_rate: number
      monthly_growth_rate: number
    }
    total_jobs?: number
    daily_average?: number
  }
}

export function MarketTrendsChart({ data }: MarketTrendsChartProps) {
  const { chart_data, growth_metrics, total_jobs, daily_average } = data

  // Simple line chart implementation using SVG
  const renderLineChart = (chartData: Array<{ date: string; count: number }>) => {
    if (!chartData || chartData.length === 0) return null

    const maxCount = Math.max(...chartData.map(d => d.count))
    const minCount = Math.min(...chartData.map(d => d.count))
    const range = maxCount - minCount || 1

    const width = 400
    const height = 200
    const padding = 40

    const points = chartData.map((d, i) => {
      const x = padding + (i / (chartData.length - 1)) * (width - 2 * padding)
      const y = height - padding - ((d.count - minCount) / range) * (height - 2 * padding)
      return `${x},${y}`
    }).join(' ')

    return (
      <div className="relative">
        <svg width={width} height={height} className="w-full h-48">
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Line */}
          <polyline
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            points={points}
          />
          
          {/* Points */}
          {chartData.map((d, i) => {
            const x = padding + (i / (chartData.length - 1)) * (width - 2 * padding)
            const y = height - padding - ((d.count - minCount) / range) * (height - 2 * padding)
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r="3"
                fill="#3b82f6"
                className="hover:r-4 transition-all cursor-pointer"
              >
                <title>{`${d.date}: ${d.count} jobs`}</title>
              </circle>
            )
          })}
          
          {/* Y-axis labels */}
          <text x="10" y={padding} className="text-xs fill-gray-600" textAnchor="start">
            {maxCount}
          </text>
          <text x="10" y={height - padding + 5} className="text-xs fill-gray-600" textAnchor="start">
            {minCount}
          </text>
        </svg>
        
        {/* X-axis labels */}
        <div className="flex justify-between text-xs text-gray-600 mt-2 px-10">
          <span>{chartData[0]?.date}</span>
          <span>{chartData[Math.floor(chartData.length / 2)]?.date}</span>
          <span>{chartData[chartData.length - 1]?.date}</span>
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Job Market Trends
          </h3>
          {growth_metrics && (
            <div className="flex items-center space-x-2">
              <span className={`text-sm font-medium ${
                growth_metrics.weekly_growth_rate >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {growth_metrics.weekly_growth_rate >= 0 ? '+' : ''}
                {(growth_metrics.weekly_growth_rate * 100).toFixed(1)}%
              </span>
              <span className="text-xs text-gray-500">weekly</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {chart_data?.jobs_over_time && chart_data.jobs_over_time.length > 0 ? (
          <div className="space-y-4">
            {renderLineChart(chart_data.jobs_over_time)}
            
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {total_jobs?.toLocaleString() || 0}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Jobs</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {daily_average?.toFixed(1) || '0.0'}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Daily Average</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p>No market trend data available</p>
              <p className="text-sm mt-1">Add more jobs to see trends</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}