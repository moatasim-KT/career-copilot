'use client';

import dynamic from 'next/dynamic';

// Lazy load the AnalyticsPage component
const AnalyticsPage = dynamic(() => import('@/components/pages/AnalyticsPage'), {
  loading: () => (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  ),
});

function Analytics() {
  return <AnalyticsPage />;
}

export default Analytics;
