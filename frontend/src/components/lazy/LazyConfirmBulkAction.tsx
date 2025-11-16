/**
 * Lazy-loaded ConfirmBulkAction component
 * 
 * Dynamically imports the ConfirmBulkAction dialog to reduce initial bundle size.
 * This component is only loaded when bulk operations require confirmation.
 */

'use client';

import dynamic from 'next/dynamic';
import React from 'react';

// Lazy load ConfirmBulkAction
const ConfirmBulkAction = dynamic(
  () => import('@/components/ui/ConfirmBulkAction').then((mod) => ({ default: mod.ConfirmBulkAction })),
  {
    loading: () => <ConfirmBulkActionSkeleton />,
    ssr: false,
  },
);

// Simple skeleton for confirmation dialog loading state
function ConfirmBulkActionSkeleton() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      
      {/* Dialog skeleton */}
      <div className="relative bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6 animate-pulse">
        {/* Header skeleton */}
        <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-4" />
        
        {/* Warning icon skeleton */}
        <div className="flex items-start space-x-3 mb-4">
          <div className="h-12 w-12 bg-red-100 dark:bg-red-900/30 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
            <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6" />
          </div>
        </div>
        
        {/* Item list skeleton */}
        <div className="bg-neutral-50 dark:bg-neutral-800 rounded-lg p-4 mb-4">
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-2/3 mb-3" />
          <div className="space-y-2">
            <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
            <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-4/5" />
            <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4" />
          </div>
        </div>
        
        {/* Footer skeleton */}
        <div className="flex justify-end space-x-2 pt-4 border-t border-neutral-200 dark:border-neutral-700">
          <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-20" />
          <div className="h-10 bg-red-200 dark:bg-red-900/30 rounded w-24" />
        </div>
      </div>
    </div>
  );
}

export default ConfirmBulkAction;
