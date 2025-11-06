import React from 'react';

export interface InterviewQuestion {
  id: string;
  question: string;
  type: 'behavioral' | 'technical' | 'situational';
  tips: string[];
}

interface InterviewPreparationProps {
  questions: InterviewQuestion[];
}

export function InterviewPreparation({ questions }: InterviewPreparationProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Interview Preparation</h2>
      {questions.map(q => (
        <div key={q.id} className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-2">{q.question}</h3>
          <p className="text-sm text-gray-500 mb-3">Type: {q.type}</p>
          <div className="space-y-2">
            {q.tips.map((tip, index) => (
              <p key={index} className="text-gray-700">
                <span className="font-medium">Tip {index + 1}:</span> {tip}
              </p>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
