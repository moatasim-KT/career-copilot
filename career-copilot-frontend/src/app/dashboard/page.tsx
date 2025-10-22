'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAnalyticsSummary, getInterviewTrends } from '@/lib/analytics';
import Cookies from 'js-cookie';
import { PieChart } from '@/components/PieChart'; // Assuming you'll create this component

interface AnalyticsSummaryData {
  total_jobs: number;
  total_applications: number;
  pending_applications: number;
  interviews_scheduled: number;
  offers_received: number;
  rejections_received: number;
  acceptance_rate: number;
  daily_applications_today: number;
  weekly_applications: number;
  monthly_applications: number;
  daily_application_goal: number;
  daily_goal_progress: number;
  top_skills_in_jobs: { skill: string; count: number }[];
  top_companies_applied: { company: string; count: number }[];
  application_status_breakdown: { [key: string]: number };
}

interface InterviewTrendsData {
  total_interviews_analyzed: number;
  top_common_questions: [string, number][];
  top_skill_areas_discussed: [string, number][];
  common_tech_stack_in_interviews: [string, number][];
}

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [summary, setSummary] = useState<AnalyticsSummaryData | null>(null);
  const [interviewTrends, setInterviewTrends] = useState<InterviewTrendsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = Cookies.get('auth_token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
  }, [router]);

  useEffect(() => {
    if (token) {
      fetchAnalytics();
      fetchInterviewTrends();
    }
  }, [token]);

  const fetchAnalytics = async () => {
    setLoading(true);
    const response = await getAnalyticsSummary(token!); // token is guaranteed to be non-null here
    if (response.error) {
      setError(response.error);
      if (response.error.includes('Authentication required')) {
        Cookies.remove('auth_token');
        router.push('/login');
      }
    } else if (response.data) {
      setSummary(response.data);
    }
    setLoading(false);
  };

  const fetchInterviewTrends = async () => {
    const response = await getInterviewTrends(token!); // token is guaranteed to be non-null here
    if (response.error) {
      // Handle error, but don't block main dashboard if trends fail
      console.error('Failed to fetch interview trends:', response.error);
    } else if (response.data) {
      setInterviewTrends(response.data);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">Error: {error}</div>;
  }

  if (!summary) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-6">Analytics Dashboard</h1>
        <p>No analytics data available. Make sure you have updated your profile and added some jobs/applications.</p>
      </div>
    );
  }

  const statusData = Object.entries(summary.application_status_breakdown).map(([status, count]) => ({
    name: status.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    value: count,
  }));

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Analytics Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white shadow-md rounded-lg p-4 text-center">
          <h2 className="text-lg font-semibold text-gray-600">Total Jobs</h2>
          <p className="text-3xl font-bold text-blue-600">{summary.total_jobs}</p>
        </div>
        <div className="bg-white shadow-md rounded-lg p-4 text-center">
          <h2 className="text-lg font-semibold text-gray-600">Total Applications</h2>
          <p className="text-3xl font-bold text-green-600">{summary.total_applications}</p>
        </div>
        <div className="bg-white shadow-md rounded-lg p-4 text-center">
          <h2 className="text-lg font-semibold text-gray-600">Interviews Scheduled</h2>
          <p className="text-3xl font-bold text-purple-600">{summary.interviews_scheduled}</p>
        </div>
        <div className="bg-white shadow-md rounded-lg p-4 text-center">
          <h2 className="text-lg font-semibold text-gray-600">Offers Received</h2>
          <p className="text-3xl font-bold text-yellow-600">{summary.offers_received}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Application Status Breakdown</h2>
          {statusData.length > 0 ? (
            <PieChart data={statusData} />
          ) : (
            <p>No application data to display.</p>
          )}
        </div>
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Daily Application Goal</h2>
          <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
            <div
              className="bg-blue-600 h-4 rounded-full"
              style={{ width: `${summary.daily_goal_progress}%` }}
            ></div>
          </div>
          <p className="text-lg font-medium">{summary.daily_applications_today} / {summary.daily_application_goal} applications today</p>
          <p className="text-sm text-gray-500">Progress: {summary.daily_goal_progress.toFixed(1)}%</p>

          <h2 className="text-xl font-semibold mt-6 mb-4">Top Skills in Jobs</h2>
          {summary.top_skills_in_jobs.length > 0 ? (
            <ul className="list-disc pl-5">
              {summary.top_skills_in_jobs.map((item, index) => (
                <li key={index}>{item.skill} ({item.count})</li>
              ))}
            </ul>
          ) : (
            <p>No skill data available.</p>
          )}
        </div>
      </div>

      {interviewTrends && interviewTrends.total_interviews_analyzed > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Interview Trends</h2>
          <p className="text-sm text-gray-500 mb-4">Analyzed {interviewTrends.total_interviews_analyzed} interviews.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h3 className="font-semibold">Top Common Questions</h3>
              <ul className="list-disc pl-5">
                {interviewTrends.top_common_questions.map(([question, count], index) => (
                  <li key={index}>{question} ({count})</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold">Top Skill Areas Discussed</h3>
              <ul className="list-disc pl-5">
                {interviewTrends.top_skill_areas_discussed.map(([skill, count], index) => (
                  <li key={index}>{skill} ({count})</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold">Common Tech Stack in Interviews</h3>
              <ul className="list-disc pl-5">
                {interviewTrends.common_tech_stack_in_interviews.map(([tech, count], index) => (
                  <li key={index}>{tech} ({count})</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
