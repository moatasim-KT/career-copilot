
'use client';

import ContentGeneration from '@/components/ui/ContentGeneration';
import withAuth from '@/components/auth/withAuth';

function ContentGenerationPage() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">AI Content Generation</h1>
      <ContentGeneration />
    </div>
  );
}

export default withAuth(ContentGenerationPage);
