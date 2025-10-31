'use client';

import withAuth from '@/components/auth/withAuth';
import AdvancedFeaturesPage from '@/components/pages/AdvancedFeaturesPage';

function AdvancedFeatures() {
  return <AdvancedFeaturesPage />;
}

export default withAuth(AdvancedFeatures);