'use client';

import withAuth from '@/components/auth/withAuth';
import Dashboard from '@/components/Dashboard';
import ResponsiveDemo from '@/components/ResponsiveDemo';

function DashboardPage() {
  return (
    <div className="space-y-8">
      <ResponsiveDemo />
      <Dashboard />
    </div>
  );
}

export default withAuth(DashboardPage);
