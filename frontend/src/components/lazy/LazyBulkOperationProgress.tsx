/**
 * Lazy-loaded BulkOperationProgress component
 * 
 * Dynamically imports the BulkOperationProgress dialog to reduce initial bundle size.
 * This component shows progress for long-running bulk operations.
 */

'use client';

import dynamic from 'next/dynamic';
import React from 'react';

// Lazy load BulkOperationProgress
const BulkOperationProgress = dynamic(
  () => import('@/components/ui/BulkOperationProgress').then((mod) => ({ default: mod.BulkOperationProgress })),
  {
    loading: () => <BulkOperationProgressSkeleton />,
    ssr: false,
  }
);

// Simple skeleton for progress dialog loading state
function BulkOperationProgressSkeleton() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      
      {/* Dialog skeleton */}
      <div className="relative bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6 animate-pulse">
        {/* Header skeleton */}
        <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-6" />
        
        {/* Progress bar skeleton */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between">
            <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-24" />
            <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-20" />
          </div>
          <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded-full w-full" />
          <div className="flex justify-center">
            <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-16" />
          </div>
        </div>
        
        {/* Status text skeleton */}
        <div className="text-center mb-6">
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-48 mx-auto" />
        </div>
        
        {/* Summary skeleton */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="h-8 bg-green-200 dark:bg-green-700 rounded w-12 mb-1" />
            <div className="h-3 bg-green-200 dark:bg-green-700 rounded w-16" />
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="h-8 bg-red-200 dark:bg-red-700 rounded w-12 mb-1" />
            <div className="h-3 bg-red-200 dark:bg-red-700 rounded w-16" />
          </div>
        </div>
        
        {/* Footer skeleton */}
        <div className="flex justify-end space-x-2 pt-4 border-t border-neutral-200 dark:border-neutral-700">
          <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-20" />
        </div>
      </div>
    </div>
  );
}

export default BulkOperationProgress;
