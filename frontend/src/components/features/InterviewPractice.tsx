'use client';

import React, { useState, useEffect, useRef } from 'react';

import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Textarea from '@/components/ui/Textarea';
import { apiClient, Job } from '@/lib/api';
import { logger } from '@/lib/logger';

interface InterviewQuestion {
  id: string;
  question: string;
  type: 'behavioral' | 'technical' | 'general' | 'company_specific';
  difficulty: 'easy' | 'medium' | 'hard';
  expected_duration: number; // in minutes
}

interface InterviewAnswer {
  question_id: string;
  answer: string;
  duration: number; // in seconds
  timestamp: string;
}

interface InterviewFeedback {
  question_id: string;
  score: number; // 1-10
  strengths: string[];
  improvements: string[];
  suggestions: string[];
}

interface InterviewSession {
  id: string;
  job_id?: number;
  session_type: 'general' | 'job_specific' | 'behavioral' | 'technical';
  questions: InterviewQuestion[];
  answers: InterviewAnswer[];
  feedback: InterviewFeedback[];
  overall_score?: number;
  duration_minutes: number;
  status: 'active' | 'completed' | 'paused';
  created_at: string;
}

interface InterviewPracticeProps {
  selectedJob?: Job;
  onSessionComplete?: (session: InterviewSession) => void;
}

export default function InterviewPractice({ selectedJob, onSessionComplete }: InterviewPracticeProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(selectedJob?.id || null);
  const [sessionType, setSessionType] = useState<InterviewSession['session_type']>('general');
  const [currentSession, setCurrentSession] = useState<InterviewSession | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [sessionHistory, setSessionHistory] = useState<InterviewSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    loadJobs();
    loadSessionHistory();
  }, []);

  useEffect(() => {
    if (selectedJob) {
      setSelectedJobId(selectedJob.id);
      setSessionType('job_specific');
    }
  }, [selectedJob]);

  useEffect(() => {
    if (isRecording && startTime) {
      timerRef.current = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime.getTime()) / 1000));
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording, startTime]);

  const loadJobs = async () => {
    try {
      const response = await apiClient.getJobs();
      if (response.data) {
        setJobs(response.data);
      }
    } catch (err) {
      logger.error('Failed to load jobs:', err);
    }
  };

  const loadSessionHistory = async () => {
    // In a real implementation, this would load from the backend
    // For now, we'll use localStorage
    const stored = localStorage.getItem('interview_sessions');
    if (stored) {
      setSessionHistory(JSON.parse(stored));
    }
  };

  const startSession = async () => {
    setLoading(true);
    setError(null);

    try {
      // In a real implementation, this would call the backend API
      const sessionData = {
        job_id: selectedJobId,
        session_type: sessionType,
      };

      const response = await apiClient.post('/api/v1/interview/start', sessionData);
      setCurrentSession(response.data);
      setCurrentQuestionIndex(0);
      setCurrentAnswer('');
      setStartTime(new Date());
      setIsRecording(true);
    } catch (err) {
      setError('Failed to start interview session');
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!currentSession || !currentAnswer.trim()) return;

    const answerDuration = startTime ? Math.floor((Date.now() - startTime.getTime()) / 1000) : 0;
    
    const answer: InterviewAnswer = {
      question_id: currentSession.questions[currentQuestionIndex].id,
      answer: currentAnswer,
      duration: answerDuration,
      timestamp: new Date().toISOString(),
    };

    const response = await apiClient.post(`/api/v1/interview/${currentSession.id}/answer`, answer);
    const { feedback, next_question } = response.data;

    const updatedSession = {
      ...currentSession,
      answers: [...currentSession.answers, answer],
      feedback: [...currentSession.feedback, feedback],
    };

    setCurrentSession(updatedSession);
    setCurrentAnswer('');
    setStartTime(new Date());

    if (next_question) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      completeSession(updatedSession);
    }
  };

  const completeSession = (session: InterviewSession) => {
    const overallScore = session.feedback.reduce((sum, f) => sum + f.score, 0) / session.feedback.length;
    const totalDuration = Math.floor(elapsedTime / 60);

    const completedSession = {
      ...session,
      overall_score: overallScore,
      duration_minutes: totalDuration,
      status: 'completed' as const,
    };

    setCurrentSession(completedSession);
    setIsRecording(false);
    setShowFeedback(true);

    // Save to history
    const updatedHistory = [...sessionHistory, completedSession];
    setSessionHistory(updatedHistory);
    localStorage.setItem('interview_sessions', JSON.stringify(updatedHistory));

    onSessionComplete?.(completedSession);
  };

  const resetSession = () => {
    setCurrentSession(null);
    setCurrentQuestionIndex(0);
    setCurrentAnswer('');
    setIsRecording(false);
    setStartTime(null);
    setElapsedTime(0);
    setShowFeedback(false);
    setError(null);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSessionTypeLabel = (type: string) => {
    switch (type) {
      case 'general': return 'General Interview';
      case 'job_specific': return 'Job-Specific Interview';
      case 'behavioral': return 'Behavioral Interview';
      case 'technical': return 'Technical Interview';
      default: return type;
    }
  };

  if (!currentSession) {
    return (
      <div className="space-y-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Interview Practice</h3>
          
          <div className="space-y-6">
            {/* Session Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Interview Type
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(['general', 'job_specific', 'behavioral', 'technical'] as const).map((type) => (
                  <div
                    key={type}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      sessionType === type
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSessionType(type)}
                  >
                    <h4 className="font-medium text-gray-900 mb-2">
                      {getSessionTypeLabel(type)}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {type === 'general' && 'Practice common interview questions'}
                      {type === 'job_specific' && 'Tailored questions for a specific job'}
                      {type === 'behavioral' && 'Situational and behavioral questions'}
                      {type === 'technical' && 'Technical and problem-solving questions'}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Job Selection (for job-specific interviews) */}
            {sessionType === 'job_specific' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Job
                </label>
                <select
                  value={selectedJobId || ''}
                  onChange={(e) => setSelectedJobId(Number(e.target.value) || null)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Choose a job...</option>
                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title} at {job.company}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Start Session Button */}
            <Button
              onClick={startSession}
              disabled={loading || (sessionType === 'job_specific' && !selectedJobId)}
              className="w-full"
            >
              {loading ? 'Starting Session...' : `Start ${getSessionTypeLabel(sessionType)}`}
            </Button>
          </div>
        </Card>

        {/* Session History */}
        {sessionHistory.length > 0 && (
          <Card className="p-6">
            <h4 className="text-lg font-semibold mb-4">Recent Sessions</h4>
            <div className="space-y-3">
              {sessionHistory.slice(-5).reverse().map((session) => (
                <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{getSessionTypeLabel(session.session_type)}</p>
                    <p className="text-sm text-gray-600">
                      {session.overall_score ? `Score: ${session.overall_score.toFixed(1)}/10` : 'In Progress'} • 
                      {session.duration_minutes} minutes • 
                      {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      session.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {session.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>
    );
  }

  if (showFeedback && currentSession.status === 'completed') {
    return (
      <div className="space-y-6">
        <Card className="p-6">
          <div className="text-center mb-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Interview Complete!</h3>
            <div className="flex items-center justify-center space-x-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">{currentSession.overall_score?.toFixed(1)}</p>
                <p className="text-sm text-gray-600">Overall Score</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600">{currentSession.duration_minutes}</p>
                <p className="text-sm text-gray-600">Minutes</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-600">{currentSession.questions.length}</p>
                <p className="text-sm text-gray-600">Questions</p>
              </div>
            </div>
          </div>

          {/* Detailed Feedback */}
          <div className="space-y-6">
            {currentSession.questions.map((question, index) => {
              const answer = currentSession.answers[index];
              const feedback = currentSession.feedback[index];
              
              return (
                <div key={question.id} className="border rounded-lg p-4">
                  <div className="mb-3">
                    <h4 className="font-medium text-gray-900 mb-1">
                      Question {index + 1}: {question.question}
                    </h4>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>Type: {question.type}</span>
                      <span>Difficulty: {question.difficulty}</span>
                      <span>Your time: {formatTime(answer?.duration || 0)}</span>
                      <span className={`font-medium ${
                        feedback?.score >= 7 ? 'text-green-600' : 
                        feedback?.score >= 5 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        Score: {feedback?.score}/10
                      </span>
                    </div>
                  </div>

                  {feedback && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                      <div>
                        <h5 className="font-medium text-green-700 mb-2">Strengths</h5>
                        <ul className="text-sm space-y-1">
                          {feedback.strengths.map((strength, i) => (
                            <li key={i} className="flex items-start">
                              <span className="text-green-500 mr-2">✓</span>
                              {strength}
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-yellow-700 mb-2">Areas for Improvement</h5>
                        <ul className="text-sm space-y-1">
                          {feedback.improvements.map((improvement, i) => (
                            <li key={i} className="flex items-start">
                              <span className="text-yellow-500 mr-2">!</span>
                              {improvement}
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-blue-700 mb-2">Suggestions</h5>
                        <ul className="text-sm space-y-1">
                          {feedback.suggestions.map((suggestion, i) => (
                            <li key={i} className="flex items-start">
                              <span className="text-blue-500 mr-2">💡</span>
                              {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex space-x-4 mt-6">
            <Button onClick={resetSession} className="flex-1">
              Start New Session
            </Button>
            <Button variant="outline" onClick={() => setShowFeedback(false)} className="flex-1">
              Review Answers
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Active session view
  const currentQuestion = currentSession.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / currentSession.questions.length) * 100;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        {/* Session Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold">
              {getSessionTypeLabel(currentSession.session_type)}
            </h3>
            <p className="text-sm text-gray-600">
              Question {currentQuestionIndex + 1} of {currentSession.questions.length}
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-blue-600">{formatTime(elapsedTime)}</p>
            <p className="text-sm text-gray-600">Elapsed Time</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Current Question */}
        <div className="mb-6">
          <div className="bg-blue-50 p-4 rounded-lg mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                currentQuestion.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                currentQuestion.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {currentQuestion.difficulty}
              </span>
              <span className="text-sm text-gray-600">
                Expected: {currentQuestion.expected_duration} min
              </span>
            </div>
            <h4 className="text-lg font-medium text-gray-900">
              {currentQuestion.question}
            </h4>
          </div>

          {/* Answer Input */}
          <Textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            placeholder="Type your answer here..."
            rows={8}
            className="mb-4"
          />

          {/* Answer Actions */}
          <div className="flex space-x-4">
            <Button
              onClick={submitAnswer}
              disabled={!currentAnswer.trim()}
              className="flex-1"
            >
              {currentQuestionIndex < currentSession.questions.length - 1 ? 'Next Question' : 'Complete Interview'}
            </Button>
            <Button
              variant="outline"
              onClick={resetSession}
            >
              End Session
            </Button>
          </div>
        </div>

        {/* Answer Stats */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Words:</span>
              <span className="ml-2 font-medium">
                {currentAnswer.split(/\s+/).filter(word => word.length > 0).length}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Characters:</span>
              <span className="ml-2 font-medium">{currentAnswer.length}</span>
            </div>
            <div>
              <span className="text-gray-600">Est. Speaking Time:</span>
              <span className="ml-2 font-medium">
                {Math.ceil(currentAnswer.split(/\s+/).length / 150)} min
              </span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}