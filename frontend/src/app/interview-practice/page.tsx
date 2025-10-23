
'use client';

import InterviewPractice from '@/components/ui/InterviewPractice';
import withAuth from '@/components/auth/withAuth';

function InterviewPracticePage() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">AI Interview Practice</h1>
      <InterviewPractice />
    </div>
  );
}

export default withAuth(InterviewPracticePage);
