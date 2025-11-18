'use client';

import dynamic from 'next/dynamic';

// Lazy load dashboard component for better code splitting
const Dashboard = dynamic(() => import('@/components/pages/EnhancedDashboard'), {
  loading: () => (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  ),
});

function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
            Dashboard
          </h1>
          <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
            Welcome back! Here's an overview of your job search activity.
          </p>
        </div>
      </div>
      <Dashboard />
    </div>
  );
}

export default DashboardPage;
