/**
 * LazyEnhancedDashboard
 * 
 * Lazy-loaded wrapper for EnhancedDashboard with react-grid-layout.
 * This component uses dynamic import to code-split the heavy grid layout library.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

import { DashboardSkeleton } from '@/components/loading/DashboardSkeleton';

// Lazy load EnhancedDashboard with react-grid-layout
const EnhancedDashboard = dynamic(
  () => import('@/components/pages/EnhancedDashboard'),
  {
    loading: () => <DashboardSkeleton />,
    ssr: false, // Disable SSR for grid layout as it needs window measurements
  }
);

export default function LazyEnhancedDashboard() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <EnhancedDashboard />
    </Suspense>
  );
}
