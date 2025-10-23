'use client';

import { useState } from 'react';

interface InterviewQuestion {
  question: string;
  feedback: string | null;
}

export default function InterviewPractice() {
  const [interviewSession, setInterviewSession] = useState<any>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startInterview = async () => {
    setLoading(true);
    setError(null);
    try {
      // This is a placeholder for the actual API call
      const response = {
        data: {
          id: '123',
          questions: [
            'Tell me about yourself.',
            'What are your strengths and weaknesses?',
            'Why do you want to work for this company?'
          ]
        }
      };
      setInterviewSession(response.data);
      setQuestions(response.data.questions.map((q: string) => ({ question: q, feedback: null })));
      setCurrentQuestionIndex(0);
    } catch (err) {
      setError('Failed to start interview session');
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!userAnswer) return;
    setLoading(true);
    setError(null);
    try {
      // This is a placeholder for the actual API call
      const response = { data: { feedback: 'That was a good answer, but you could have elaborated more on your experience.' } };
      const newQuestions = [...questions];
      newQuestions[currentQuestionIndex].feedback = response.data.feedback;
      setQuestions(newQuestions);
      setUserAnswer('');
    } catch (err) {
      setError('Failed to submit answer');
    } finally {
      setLoading(false);
    }
  };

  const [finished, setFinished] = useState(false);

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      setFinished(true);
    }
  };

  const practiceAgain = () => {
    setInterviewSession(null);
    setCurrentQuestionIndex(0);
    setUserAnswer('');
    setQuestions([]);
    setFinished(false);
    setError(null);
  };

  if (finished) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Interview Summary</h2>
        <div className="space-y-4">
          {questions.map((q, i) => (
            <div key={i} className="p-4 bg-gray-100 rounded-md">
              <h3 className="text-lg font-semibold">Question {i + 1}:</h3>
              <p>{q.question}</p>
              <h4 className="text-md font-semibold mt-2">Feedback:</h4>
              <p>{q.feedback || 'No feedback provided.'}</p>
            </div>
          ))}
        </div>
        <button onClick={practiceAgain} className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md">
          Practice Again
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Interview Practice</h2>
      {!interviewSession ? (
        <button onClick={startInterview} disabled={loading} className="px-4 py-2 bg-blue-500 text-white rounded-md disabled:bg-gray-400">
          {loading ? 'Starting...' : 'Start Interview'}
        </button>
      ) : (
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold">Question {currentQuestionIndex + 1} of {questions.length}:</h3>
            <p>{questions[currentQuestionIndex].question}</p>
          </div>
          <textarea
            rows={5}
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="Your answer..."
          />
          <div className="flex gap-4">
            <button onClick={submitAnswer} disabled={loading} className="px-4 py-2 bg-blue-500 text-white rounded-md disabled:bg-gray-400">
              {loading ? 'Submitting...' : 'Submit Answer'}
            </button>
            {questions[currentQuestionIndex].feedback && (
              <button onClick={nextQuestion} className="px-4 py-2 bg-green-500 text-white rounded-md">
                {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Interview'}
              </button>
            )}
          </div>
          {questions[currentQuestionIndex].feedback && (
            <div className="mt-4 p-4 bg-gray-100 rounded-md">
              <h3 className="text-lg font-semibold">Feedback:</h3>
              <p>{questions[currentQuestionIndex].feedback}</p>
            </div>
          )}
        </div>
      )}
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div>
  );
}