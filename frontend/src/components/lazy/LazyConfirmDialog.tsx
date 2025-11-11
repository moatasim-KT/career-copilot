/**
 * Lazy-loaded ConfirmDialog component
 * 
 * Dynamically imports the ConfirmDialog component to reduce initial bundle size.
 * This is a generic confirmation dialog used throughout the application.
 */

'use client';

import dynamic from 'next/dynamic';
import React from 'react';

// Lazy load ConfirmDialog
const ConfirmDialog = dynamic(
  () => import('@/components/ui/ConfirmDialog').then((mod) => ({ default: mod.ConfirmDialog })),
  {
    loading: () => <ConfirmDialogSkeleton />,
    ssr: false,
  }
);

// Simple skeleton for confirmation dialog loading state
function ConfirmDialogSkeleton() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      
      {/* Dialog skeleton */}
      <div className="relative bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-sm w-full mx-4 p-6 animate-pulse">
        {/* Header skeleton */}
        <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-4" />
        
        {/* Content skeleton */}
        <div className="space-y-2 mb-6">
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6" />
        </div>
        
        {/* Footer skeleton */}
        <div className="flex justify-end space-x-2">
          <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-20" />
          <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-24" />
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
