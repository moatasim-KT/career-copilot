import { Card, CardHeader, CardContent } from '@/components/ui'

interface SalaryTrendsChartProps {
  data: {
    chart_data?: {
      monthly_trend?: Array<{ month: string; salary: number }>
      location_comparison?: Array<{ location: string; salary: number }>
    }
    overall_salary_range?: {
      min: number
      max: number
      median: number
      average: number
    }
    salary_growth_rate?: number
    growth_percentage?: string
  }
}

export function SalaryTrendsChart({ data }: SalaryTrendsChartProps) {
  const { chart_data, overall_salary_range, salary_growth_rate, growth_percentage } = data

  // Simple bar chart for salary comparison
  const renderBarChart = (chartData: Array<{ location: string; salary: number }>) => {
    if (!chartData || chartData.length === 0) return null

    const maxSalary = Math.max(...chartData.map(d => d.salary))
    const sortedData = chartData.sort((a, b) => b.salary - a.salary).slice(0, 6) // Top 6 locations

    return (
      <div className="space-y-3">
        {sortedData.map((item, index) => (
          <div key={index} className="flex items-center space-x-3">
            <div className="w-20 text-sm text-gray-600 dark:text-gray-400 truncate">
              {item.location}
            </div>
            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-6 relative">
              <div
                className="bg-gradient-to-r from-green-400 to-green-600 h-6 rounded-full flex items-center justify-end pr-2"
                style={{ width: `${(item.salary / maxSalary) * 100}%` }}
              >
                <span className="text-xs text-white font-medium">
                  ${(item.salary / 1000).toFixed(0)}k
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Line chart for monthly salary trends
  const renderSalaryTrendLine = (chartData: Array<{ month: string; salary: number }>) => {
    if (!chartData || chartData.length === 0) return null

    const maxSalary = Math.max(...chartData.map(d => d.salary))
    const minSalary = Math.min(...chartData.map(d => d.salary))
    const range = maxSalary - minSalary || 1

    const width = 400
    const height = 150
    const padding = 30

    const points = chartData.map((d, i) => {
      const x = padding + (i / (chartData.length - 1)) * (width - 2 * padding)
      const y = height - padding - ((d.salary - minSalary) / range) * (height - 2 * padding)
      return `${x},${y}`
    }).join(' ')

    return (
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Monthly Salary Trends
        </h4>
        <svg width={width} height={height} className="w-full h-32">
          {/* Grid */}
          <defs>
            <pattern id="salary-grid" width="40" height="15" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 15" fill="none" stroke="#e5e7eb" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#salary-grid)" />
          
          {/* Trend line */}
          <polyline
            fill="none"
            stroke="#10b981"
            strokeWidth="2"
            points={points}
          />
          
          {/* Data points */}
          {chartData.map((d, i) => {
            const x = padding + (i / (chartData.length - 1)) * (width - 2 * padding)
            const y = height - padding - ((d.salary - minSalary) / range) * (height - 2 * padding)
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r="3"
                fill="#10b981"
                className="hover:r-4 transition-all cursor-pointer"
              >
                <title>{`${d.month}: $${d.salary.toLocaleString()}`}</title>
              </circle>
            )
          })}
        </svg>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Salary Trends
          </h3>
          {salary_growth_rate !== undefined && (
            <div className="flex items-center space-x-2">
              <span className={`text-sm font-medium ${
                salary_growth_rate >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {growth_percentage || `${(salary_growth_rate * 100).toFixed(1)}%`}
              </span>
              <span className="text-xs text-gray-500">growth</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {overall_salary_range || chart_data ? (
          <div className="space-y-6">
            {/* Monthly trend line */}
            {chart_data?.monthly_trend && renderSalaryTrendLine(chart_data.monthly_trend)}
            
            {/* Salary range summary */}
            {overall_salary_range && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    ${(overall_salary_range.min / 1000).toFixed(0)}k
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Min</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    ${(overall_salary_range.median / 1000).toFixed(0)}k
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Median</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    ${(overall_salary_range.average / 1000).toFixed(0)}k
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Average</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    ${(overall_salary_range.max / 1000).toFixed(0)}k
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Max</p>
                </div>
              </div>
            )}
            
            {/* Location comparison */}
            {chart_data?.location_comparison && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Salary by Location
                </h4>
                {renderBarChart(chart_data.location_comparison)}
              </div>
            )}
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
              <p>No salary data available</p>
              <p className="text-sm mt-1">Add jobs with salary information to see trends</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}