import { Card, CardHeader, CardContent } from '@/components/ui'

interface IndustryDistributionChartProps {
  data: Record<string, {
    count: number
    percentage: number
    company_count: number
    avg_jobs_per_company: number
  }>
}

export function IndustryDistributionChart({ data }: IndustryDistributionChartProps) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Industry Distribution
          </h3>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p>No industry data available</p>
              <p className="text-sm mt-1">Add more jobs to see industry breakdown</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Sort industries by job count
  const sortedIndustries = Object.entries(data)
    .sort(([, a], [, b]) => b.count - a.count)
    .slice(0, 8) // Show top 8 industries

  // Color palette for industries
  const colors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6b7280'
  ]

  // Simple donut chart using SVG
  const renderDonutChart = () => {
    const total = sortedIndustries.reduce((sum, [, industry]) => sum + industry.count, 0)
    let currentAngle = 0
    const radius = 80
    const innerRadius = 50
    const centerX = 100
    const centerY = 100

    const createArcPath = (startAngle: number, endAngle: number, outerR: number, innerR: number) => {
      const startAngleRad = (startAngle * Math.PI) / 180
      const endAngleRad = (endAngle * Math.PI) / 180
      
      const x1 = centerX + outerR * Math.cos(startAngleRad)
      const y1 = centerY + outerR * Math.sin(startAngleRad)
      const x2 = centerX + outerR * Math.cos(endAngleRad)
      const y2 = centerY + outerR * Math.sin(endAngleRad)
      
      const x3 = centerX + innerR * Math.cos(endAngleRad)
      const y3 = centerY + innerR * Math.sin(endAngleRad)
      const x4 = centerX + innerR * Math.cos(startAngleRad)
      const y4 = centerY + innerR * Math.sin(startAngleRad)
      
      const largeArc = endAngle - startAngle > 180 ? 1 : 0
      
      return `M ${x1} ${y1} A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${innerR} ${innerR} 0 ${largeArc} 0 ${x4} ${y4} Z`
    }

    return (
      <div className="flex items-center space-x-6">
        <div className="relative">
          <svg width="200" height="200" className="transform -rotate-90">
            {sortedIndustries.map(([industry, industryData], index) => {
              const percentage = (industryData.count / total) * 100
              const angle = (percentage / 100) * 360
              const path = createArcPath(currentAngle, currentAngle + angle, radius, innerRadius)
              const color = colors[index % colors.length]
              
              currentAngle += angle
              
              return (
                <path
                  key={industry}
                  d={path}
                  fill={color}
                  className="hover:opacity-80 transition-opacity cursor-pointer"
                >
                  <title>{`${industry}: ${industryData.count} jobs (${percentage.toFixed(1)}%)`}</title>
                </path>
              )
            })}
          </svg>
          
          {/* Center text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{total}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Total Jobs</p>
            </div>
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex-1 space-y-2">
          {sortedIndustries.map(([industry, industryData], index) => (
            <div key={industry} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                  {industry.replace('_', ' ')}
                </span>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {industryData.count}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {industryData.percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Industry Distribution
        </h3>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {renderDonutChart()}
          
          {/* Industry insights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-center">
              <p className="text-lg font-bold text-gray-900 dark:text-white">
                {Object.keys(data).length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Industries</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-gray-900 dark:text-white">
                {sortedIndustries[0]?.[0]?.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') || 'N/A'}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Top Industry</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-gray-900 dark:text-white">
                {sortedIndustries[0]?.[1]?.percentage?.toFixed(1) || '0'}%
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Market Share</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}