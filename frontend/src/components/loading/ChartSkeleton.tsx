/**
 * ChartSkeleton Component
 * 
 * Loading skeleton for chart components while they are being lazy loaded.
 */

'use client';

export function ChartSkeleton() {
  return (
    <div className="w-full h-full animate-pulse">
      <div className="space-y-4">
        {/* Chart title skeleton */}
        <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-1/3"></div>
        
        {/* Chart area skeleton */}
        <div className="relative h-64 bg-neutral-100 dark:bg-neutral-800 rounded-lg overflow-hidden">
          {/* Simulated chart bars/lines */}
          <div className="absolute bottom-0 left-0 right-0 flex items-end justify-around p-4 space-x-2">
            {[40, 70, 55, 80, 60, 90, 45].map((height, i) => (
              <div
                key={i}
                className="flex-1 bg-neutral-300 dark:bg-neutral-600 rounded-t"
                style={{ height: `${height}%` }}
              />
            ))}
          </div>
        </div>
        
        {/* Legend skeleton */}
        <div className="flex items-center justify-center space-x-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-neutral-300 dark:bg-neutral-600 rounded-full"></div>
              <div className="h-4 w-16 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function PieChartSkeleton() {
  return (
    <div className="w-full h-full animate-pulse">
      <div className="space-y-4">
        {/* Chart title skeleton */}
        <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-1/3"></div>
        
        {/* Pie chart skeleton */}
        <div className="flex items-center justify-center h-64">
          <div className="relative w-48 h-48">
            <div className="absolute inset-0 rounded-full bg-neutral-200 dark:bg-neutral-700"></div>
            <div className="absolute inset-8 rounded-full bg-white dark:bg-neutral-900"></div>
          </div>
        </div>
        
        {/* Legend skeleton */}
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-neutral-300 dark:bg-neutral-600 rounded"></div>
              <div className="h-4 flex-1 bg-neutral-200 dark:bg-neutral-700 rounded max-w-xs"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function LineChartSkeleton() {
  return (
    <div className="w-full h-full animate-pulse">
      <div className="space-y-4">
        {/* Chart title skeleton */}
        <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-1/3"></div>
        
        {/* Line chart skeleton */}
        <div className="relative h-64 bg-neutral-100 dark:bg-neutral-800 rounded-lg overflow-hidden">
          {/* Simulated line chart path */}
          <svg className="w-full h-full p-4" viewBox="0 0 400 200">
            <path
              d="M 0 150 Q 50 100, 100 120 T 200 80 T 300 100 T 400 60"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              className="text-neutral-300 dark:text-neutral-600"
            />
            <path
              d="M 0 180 Q 50 160, 100 170 T 200 140 T 300 150 T 400 120"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              className="text-neutral-300 dark:text-neutral-600"
            />
          </svg>
        </div>
        
        {/* Legend skeleton */}
        <div className="flex items-center justify-center space-x-4">
          {[1, 2].map((i) => (
            <div key={i} className="flex items-center space-x-2">
              <div className="w-8 h-0.5 bg-neutral-300 dark:bg-neutral-600"></div>
              <div className="h-4 w-20 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
