import { Card, CardHeader, CardContent } from '@/components/ui'

interface MarketInsightsProps {
  salaryInsights: string[]
  marketInsights: string[]
}

export function MarketInsights({ salaryInsights, marketInsights }: MarketInsightsProps) {
  const allInsights = [...(salaryInsights || []), ...(marketInsights || [])]

  if (allInsights.length === 0) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Market Insights
          </h3>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <p>No insights available</p>
              <p className="text-sm mt-1">Add more job data to generate insights</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getInsightIcon = (insight: string) => {
    if (insight.includes('📈') || insight.includes('growth') || insight.includes('increase')) {
      return (
        <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      )
    } else if (insight.includes('📉') || insight.includes('decline') || insight.includes('decrease')) {
      return (
        <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>
      )
    } else if (insight.includes('💰') || insight.includes('salary') || insight.includes('pay')) {
      return (
        <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
        </svg>
      )
    } else if (insight.includes('🏢') || insight.includes('industry') || insight.includes('company')) {
      return (
        <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    } else if (insight.includes('🏠') || insight.includes('remote') || insight.includes('location')) {
      return (
        <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    } else if (insight.includes('📅') || insight.includes('time') || insight.includes('season')) {
      return (
        <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    } else {
      return (
        <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      )
    }
  }

  const cleanInsightText = (insight: string) => {
    // Remove emoji from the beginning of the insight
    return insight.replace(/^[📈📉💰🏢🏠📅🚀⚠️📊🎯🔥]+\s*/, '')
  }

  const getInsightType = (insight: string) => {
    if (insight.includes('📈') || insight.includes('growth') || insight.includes('increase')) {
      return 'positive'
    } else if (insight.includes('📉') || insight.includes('decline') || insight.includes('decrease')) {
      return 'negative'
    } else if (insight.includes('⚠️') || insight.includes('warning') || insight.includes('caution')) {
      return 'warning'
    } else {
      return 'neutral'
    }
  }

  const getInsightBadge = (type: string) => {
    switch (type) {
      case 'positive':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'negative':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Market Insights
          </h3>
          <span className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 text-xs font-medium px-2.5 py-0.5 rounded-full">
            {allInsights.length} Insights
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {allInsights.map((insight, index) => {
            const type = getInsightType(insight)
            const cleanText = cleanInsightText(insight)
            
            return (
              <div
                key={index}
                className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getInsightIcon(insight)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      {cleanText}
                    </p>
                    <span className={`ml-2 text-xs font-medium px-2 py-1 rounded-full flex-shrink-0 ${getInsightBadge(type)}`}>
                      {type === 'positive' ? 'Opportunity' : 
                       type === 'negative' ? 'Challenge' :
                       type === 'warning' ? 'Caution' : 'Info'}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
        
        {/* Insight Categories Summary */}
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-lg font-bold text-green-600 dark:text-green-400">
                {allInsights.filter(i => getInsightType(i) === 'positive').length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Opportunities</p>
            </div>
            <div>
              <p className="text-lg font-bold text-red-600 dark:text-red-400">
                {allInsights.filter(i => getInsightType(i) === 'negative').length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Challenges</p>
            </div>
            <div>
              <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                {allInsights.filter(i => getInsightType(i) === 'warning').length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Warnings</p>
            </div>
            <div>
              <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {allInsights.filter(i => getInsightType(i) === 'neutral').length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">General</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}