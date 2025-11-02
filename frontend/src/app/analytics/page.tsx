'use client';

import withAuth from '@/components/auth/withAuth';
import AnalyticsPage from '@/components/pages/AnalyticsPage';

function Analytics() {
  return <AnalyticsPage />;
}

export default withAuth(Analytics);
