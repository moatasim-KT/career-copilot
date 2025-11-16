/**
 * Lazy-loaded Drawer2 component
 * 
 * Dynamically imports the Drawer2 component to reduce initial bundle size.
 * Drawers are slide-in panels typically used for mobile navigation or side panels.
 */

'use client';

import dynamic from 'next/dynamic';
import React from 'react';

// Lazy load Drawer2
const Drawer2 = dynamic(
  () => import('@/components/ui/Drawer2'),
  {
    loading: () => <Drawer2Skeleton />,
    ssr: false,
  },
);

// Simple skeleton for drawer loading state
function Drawer2Skeleton() {
  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      
      {/* Drawer skeleton - slide from right */}
      <div className="absolute right-0 top-0 bottom-0 w-80 max-w-full bg-white dark:bg-neutral-800 shadow-xl animate-pulse">
        {/* Header skeleton */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200 dark:border-neutral-700">
          <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4" />
          <div className="h-6 w-6 bg-neutral-200 dark:bg-neutral-700 rounded" />
        </div>
        
        {/* Content skeleton */}
        <div className="p-6 space-y-4">
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-4/6" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4" />
        </div>
      </div>
    </div>
  );
}

export default Drawer2;
