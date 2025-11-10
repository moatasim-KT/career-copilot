/**
 * DashboardSkeleton Component
 * 
 * Loading skeleton for dashboard components with grid layout.
 */

'use client';

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-48 bg-neutral-200 dark:bg-neutral-700 rounded mb-2"></div>
          <div className="h-4 w-64 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
        <div className="flex items-center space-x-3">
          <div className="h-10 w-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          <div className="h-10 w-24 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
      </div>
      
      {/* Grid layout skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Widget skeletons */}
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6"
            style={{ height: i === 1 || i === 2 ? '300px' : '200px' }}
          >
            <div className="h-6 w-32 bg-neutral-200 dark:bg-neutral-700 rounded mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
              <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6"></div>
              <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-4/6"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="h-4 w-24 bg-neutral-200 dark:bg-neutral-700 rounded mb-2"></div>
          <div className="h-8 w-16 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
        <div className="w-12 h-12 bg-neutral-200 dark:bg-neutral-700 rounded-full"></div>
      </div>
      <div className="mt-4 flex items-center space-x-2">
        <div className="h-3 w-12 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        <div className="h-3 w-20 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
      </div>
    </div>
  );
}
