'use client';

import dynamic from 'next/dynamic';

// Lazy load dashboard components for better code splitting
const ResponsiveDemo = dynamic(() => import('@/components/common/ResponsiveDemo'), {
  loading: () => <div className="h-8 bg-gray-100 animate-pulse rounded"></div>,
});

const Dashboard = dynamic(() => import('@/components/pages/Dashboard'), {
  loading: () => (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  ),
});

function DashboardPage() {
  return (
    <div className="space-y-8">
      <ResponsiveDemo />
      <Dashboard />
    </div>
  );
}

export default DashboardPage;
