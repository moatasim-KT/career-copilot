/**
 * NotificationCenterSkeleton Component
 * 
 * Loading skeleton for NotificationCenter dropdown.
 */

'use client';

export function NotificationCenterSkeleton() {
  return (
    <div className="w-96 max-h-[32rem] bg-white dark:bg-neutral-900 rounded-lg shadow-xl border border-neutral-200 dark:border-neutral-700 overflow-hidden animate-pulse">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-700">
        <div className="h-6 w-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        <div className="h-8 w-24 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
      </div>
      
      {/* Notification items */}
      <div className="divide-y divide-neutral-200 dark:divide-neutral-700">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="p-4 space-y-2">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 bg-neutral-200 dark:bg-neutral-700 rounded-full flex-shrink-0"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4"></div>
                <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-full"></div>
                <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6"></div>
                <div className="flex items-center justify-between mt-2">
                  <div className="h-3 w-20 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
                  <div className="h-6 w-16 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-neutral-200 dark:border-neutral-700 text-center">
        <div className="h-4 w-32 bg-neutral-200 dark:bg-neutral-700 rounded mx-auto"></div>
      </div>
    </div>
  );
}
