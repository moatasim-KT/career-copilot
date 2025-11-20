/**
 * Lazy-loaded Modal component
 * 
 * Dynamically imports the Modal component to reduce initial bundle size.
 * Modals are only loaded when they are actually opened.
 */

'use client';

import dynamic from 'next/dynamic';
import React from 'react';

// Lazy load Modal
const Modal2 = dynamic(
  () => import('@/components/ui/Modal2').then((mod) => ({ default: mod.Modal2 })),
  {
    loading: () => <ModalSkeleton />,
    ssr: false,
  },
);

// Lazy load ModalFooter
export const LazyModalFooter = dynamic(
  () => import('@/components/ui/Modal2').then((mod) => ({ default: mod.ModalFooter })),
  {
    ssr: false,
  },
);

// Simple skeleton for modal loading state
function ModalSkeleton() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      
      {/* Modal skeleton */}
      <div className="relative bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6 animate-pulse">
        {/* Header skeleton */}
        <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-4" />
        
        {/* Content skeleton */}
        <div className="space-y-3">
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-4/6" />
        </div>
        
        {/* Footer skeleton */}
        <div className="flex justify-end space-x-2 mt-6">
          <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-20" />
          <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-24" />
        </div>
      </div>
    </div>
  );
}

export default Modal2;