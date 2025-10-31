'use client';

import withAuth from '@/components/auth/withAuth';
import ResponsiveDemo from '@/components/common/ResponsiveDemo';
import Dashboard from '@/components/pages/Dashboard';

function DashboardPage() {
  return (
    <div className="space-y-8">
      <ResponsiveDemo />
      <Dashboard />
    </div>
  );
}

export default withAuth(DashboardPage);
