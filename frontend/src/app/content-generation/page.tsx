'use client';

import ContentGeneration from '@/components/ui/ContentGeneration';
import Card from '@/components/ui/Card';

export default function ContentGenerationPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Content Generation</h1>
      <Card>
        <ContentGeneration />
      </Card>
    </div>
  );
}