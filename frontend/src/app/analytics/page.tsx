'use client';

import dynamic from 'next/dynamic';

import { AnalyticsLoadingSkeleton } from '@/components/ui/LoadingSkeletons';

// Lazy load the AnalyticsPage component
const AnalyticsPage = dynamic(() => import('@/components/pages/AnalyticsPage'), {
  loading: () => <AnalyticsLoadingSkeleton />,
});

function Analytics() {
  return <AnalyticsPage />;
}

export default Analytics;
