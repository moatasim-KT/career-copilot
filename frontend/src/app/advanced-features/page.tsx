'use client';

import withAuth from '@/components/auth/withAuth';
import AdvancedFeaturesPage from '@/components/AdvancedFeaturesPage';

function AdvancedFeatures() {
  return <AdvancedFeaturesPage />;
}

export default withAuth(AdvancedFeatures);