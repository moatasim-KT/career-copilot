'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getSkillGapAnalysis } from '@/lib/skill-gap';
import Cookies from 'js-cookie';

interface SkillGapAnalysisData {
  user_skills: string[];
  missing_skills: { [key: string]: number };
  top_market_skills: { [key: string]: number };
  skill_coverage_percentage: number;
  learning_recommendations: string[];
  total_jobs_analyzed: number;
}

export default function SkillGapPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<SkillGapAnalysisData | null>(null);
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
      fetchSkillGapAnalysis();
    }
  }, [token]);

  const fetchSkillGapAnalysis = async () => {
    setLoading(true);
    const response = await getSkillGapAnalysis(token!); // token is guaranteed to be non-null here
    if (response.error) {
      setError(response.error);
      if (response.error.includes('Authentication required')) {
        Cookies.remove('auth_token');
        router.push('/login');
      }
    } else if (response.data) {
      setAnalysis(response.data);
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading skill gap analysis...</div>;
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">Error: {error}</div>;
  }

  if (!analysis) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-6">Skill Gap Analysis</h1>
        <p>No data available for skill gap analysis. Make sure your profile is updated and you have added some jobs with tech stacks.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Skill Gap Analysis</h1>

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Skill Coverage</h2>
        <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
          <div
            className="bg-blue-600 h-4 rounded-full"
            style={{ width: `${analysis.skill_coverage_percentage}%` }}
          ></div>
        </div>
        <p className="text-lg font-medium">{analysis.skill_coverage_percentage.toFixed(1)}% of skills in your tracked jobs are covered by your profile.</p>
        <p className="text-sm text-gray-500">Analyzed {analysis.total_jobs_analyzed} jobs.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Your Skills</h2>
          {analysis.user_skills.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {analysis.user_skills.map((skill) => (
                <span key={skill} className="bg-green-200 text-green-800 text-sm px-3 py-1 rounded-full">{skill}</span>
              ))}
            </div>
          ) : (
            <p>No skills found in your profile. Please update your profile.</p>
          )}
        </div>

        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Missing Skills</h2>
          {Object.keys(analysis.missing_skills).length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {Object.entries(analysis.missing_skills).map(([skill, count]) => (
                <span key={skill} className="bg-red-200 text-red-800 text-sm px-3 py-1 rounded-full">{skill} ({count})</span>
              ))}
            </div>
          ) : (
            <p>🎉 No missing skills found!</p>
          )}
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Top Market Skills</h2>
        {Object.keys(analysis.top_market_skills).length > 0 ? (
          <ul className="list-disc pl-5">
            {Object.entries(analysis.top_market_skills).map(([skill, count]) => (
              <li key={skill} className="text-gray-700">{skill} (appears in {count} jobs)</li>
            ))}
          </ul>
        ) : (
          <p>No market skill data available yet.</p>
        )}
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Learning Recommendations</h2>
        {analysis.learning_recommendations.length > 0 ? (
          <ul className="list-disc pl-5">
            {analysis.learning_recommendations.map((rec, index) => (
              <li key={index} className="text-gray-700">{rec}</li>
            ))}
          </ul>
        ) : (
          <p>You have all the required skills for your tracked jobs!</p>
        )}
      </div>
    </div>
  );
}
