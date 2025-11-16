'use client';

import dynamic from 'next/dynamic';

import Card2 from '@/components/ui/Card2';

// Lazy load the InterviewPractice component
const InterviewPractice = dynamic(() => import('@/components/features/InterviewPractice'), {
  loading: () => (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  ),
});

export default function InterviewPracticePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Interview Practice</h1>
      <Card2>
        <InterviewPractice />
      </Card2>
    </div>
  );
}