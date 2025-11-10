/**
 * CommandPaletteSkeleton Component
 * 
 * Loading skeleton for CommandPalette while it's being lazy loaded.
 */

'use client';

export function CommandPaletteSkeleton() {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] px-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
      
      {/* Command palette container */}
      <div className="relative w-full max-w-2xl bg-white dark:bg-neutral-900 rounded-lg shadow-2xl border border-neutral-200 dark:border-neutral-700 overflow-hidden animate-pulse">
        {/* Search input skeleton */}
        <div className="flex items-center border-b border-neutral-200 dark:border-neutral-700 p-4">
          <div className="w-5 h-5 bg-neutral-300 dark:bg-neutral-600 rounded mr-3"></div>
          <div className="flex-1 h-6 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
        
        {/* Results skeleton */}
        <div className="p-2 space-y-1 max-h-96">
          {/* Category header */}
          <div className="px-3 py-2">
            <div className="h-3 w-24 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          </div>
          
          {/* Command items */}
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center space-x-3 px-3 py-2 rounded">
              <div className="w-5 h-5 bg-neutral-300 dark:bg-neutral-600 rounded"></div>
              <div className="flex-1 h-4 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
              <div className="w-12 h-4 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            </div>
          ))}
          
          {/* Another category */}
          <div className="px-3 py-2 mt-4">
            <div className="h-3 w-20 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          </div>
          
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center space-x-3 px-3 py-2 rounded">
              <div className="w-5 h-5 bg-neutral-300 dark:bg-neutral-600 rounded"></div>
              <div className="flex-1 h-4 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            </div>
          ))}
        </div>
        
        {/* Footer skeleton */}
        <div className="border-t border-neutral-200 dark:border-neutral-700 p-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-3 w-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          </div>
          <div className="h-3 w-24 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
      </div>
    </div>
  );
}
