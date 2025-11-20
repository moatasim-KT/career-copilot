'use client';

import dynamic from 'next/dynamic';

import Card from '@/components/ui/Card2';

// Lazy load the ContentGeneration component
const ContentGeneration = dynamic(() => import('@/components/features/ContentGeneration'), {
  loading: () => (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  ),
});

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