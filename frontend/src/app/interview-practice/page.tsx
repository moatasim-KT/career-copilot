'use client';

import InterviewPractice from '@/components/ui/InterviewPractice';
import Card from '@/components/ui/Card';
import Card from '@/components/ui/Card';

export default function InterviewPracticePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Interview Practice</h1>
      <Card>
        <InterviewPractice />
      </Card>
    </div>
  );
}