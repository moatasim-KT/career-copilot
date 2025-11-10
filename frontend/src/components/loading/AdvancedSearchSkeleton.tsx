/**
 * AdvancedSearchSkeleton Component
 * 
 * Loading skeleton for AdvancedSearch panel while it's being lazy loaded.
 */

'use client';

export function AdvancedSearchSkeleton() {
  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-white dark:bg-neutral-900 shadow-2xl border-l border-neutral-200 dark:border-neutral-700 z-40 animate-pulse">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-neutral-200 dark:border-neutral-700">
        <div className="h-7 w-48 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        <div className="w-8 h-8 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
      </div>
      
      {/* Content */}
      <div className="p-6 space-y-6 overflow-y-auto" style={{ height: 'calc(100vh - 180px)' }}>
        {/* Query builder skeleton */}
        <div className="space-y-4">
          {/* Group header */}
          <div className="flex items-center justify-between">
            <div className="h-5 w-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            <div className="flex space-x-2">
              <div className="w-20 h-8 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
              <div className="w-8 h-8 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            </div>
          </div>
          
          {/* Rules */}
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-neutral-50 dark:bg-neutral-800 p-4 rounded-lg space-y-3">
              <div className="flex items-center space-x-3">
                <div className="flex-1 h-10 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
                <div className="flex-1 h-10 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
                <div className="flex-1 h-10 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
                <div className="w-10 h-10 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
              </div>
            </div>
          ))}
          
          {/* Add buttons */}
          <div className="flex space-x-2">
            <div className="w-28 h-9 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            <div className="w-28 h-9 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          </div>
        </div>
        
        {/* Preview section */}
        <div className="border-t border-neutral-200 dark:border-neutral-700 pt-6">
          <div className="h-5 w-32 bg-neutral-200 dark:bg-neutral-700 rounded mb-3"></div>
          <div className="h-16 bg-neutral-100 dark:bg-neutral-800 rounded"></div>
        </div>
      </div>
      
      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900">
        <div className="flex items-center justify-between">
          <div className="h-10 w-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          <div className="flex space-x-3">
            <div className="h-10 w-24 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            <div className="h-10 w-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
