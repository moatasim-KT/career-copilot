/**
 * Lazy-loaded BulkActionBar component
 * 
 * Dynamically imports the BulkActionBar component to reduce initial bundle size.
 * This component is only loaded when items are selected for bulk operations.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

import type { BulkActionBarProps } from '@/components/ui/BulkActionBar';

// Simple skeleton for BulkActionBar
function BulkActionBarSkeleton() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 glass border-t border-neutral-200 dark:border-neutral-700 shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-4 w-32 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse" />
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-9 w-24 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse" />
            <div className="h-9 w-24 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Lazy load BulkActionBar
const BulkActionBar = dynamic(
  () => import('@/components/ui/BulkActionBar').then((mod) => ({ default: mod.BulkActionBar })),
  {
    loading: () => <BulkActionBarSkeleton />,
    ssr: false,
  },
);

export function LazyBulkActionBar(props: BulkActionBarProps) {
  return (
    <Suspense fallback={<BulkActionBarSkeleton />}>
      <BulkActionBar {...props} />
    </Suspense>
  );
}
