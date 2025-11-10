/**
 * LazyAnalyticsPage
 * 
 * Lazy-loaded wrapper for AnalyticsPage with Recharts.
 * This component uses React.lazy() to code-split the heavy Recharts library.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

import { ChartSkeleton } from '@/components/loading/ChartSkeleton';

// Lazy load AnalyticsPage with Recharts
const AnalyticsPage = dynamic(
  () => import('@/components/pages/AnalyticsPage'),
  {
    loading: () => (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Analytics Dashboard</h1>
          <div className="h-10 w-24 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse"></div>
        </div>
        
        {/* Metric cards skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700 animate-pulse">
              <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
        
        {/* Charts skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
            <ChartSkeleton />
          </div>
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
            <ChartSkeleton />
          </div>
        </div>
      </div>
    ),
    ssr: false, // Disable SSR for charts as they're client-side only
  }
);

export default function LazyAnalyticsPage() {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <AnalyticsPage />
    </Suspense>
  );
}
