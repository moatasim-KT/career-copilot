'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getRecommendations } from '@/lib/recommendations';
import { createApplication } from '@/lib/applications'; // Assuming you'll create this later
import Cookies from 'js-cookie';

interface RecommendationData {
  job_id: number;
  company: string;
  title: string;
  location?: string;
  tech_stack?: string[];
  match_score: number;
  link?: string;
}

export default function RecommendationsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [skip, setSkip] = useState(0);
  const [limit, setLimit] = useState(10);

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
      fetchRecommendations();
    }
  }, [token, skip, limit]);

  const fetchRecommendations = async () => {
    setLoading(true);
    const response = await getRecommendations(token!, skip, limit);
    if (response.error) {
      setError(response.error);
      if (response.error.includes('Authentication required')) {
        Cookies.remove('auth_token');
        router.push('/login');
      }
    } else if (response.data) {
      setRecommendations(response.data);
    }
    setLoading(false);
  };

  const handleApply = async (jobId: number, title: string, score: number) => {
    if (!token) return;

    setLoading(true);
    setError(null);

    const applicationData = {
      job_id: jobId,
      status: 'applied',
      notes: `Applied via recommendations (Match: ${score.toFixed(0)}%)`,
    };

    const response = await createApplication(token, applicationData);
    if (response.error) {
      setError(response.error);
    } else {
      alert(`Successfully applied to ${title}!`);
      fetchRecommendations(); // Refresh recommendations after applying
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading recommendations...</div>;
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Job Recommendations</h1>

      <div className="mb-4 flex space-x-4">
        <div>
          <label htmlFor="limit" className="block text-gray-700 text-sm font-bold mb-2">Limit</label>
          <input type="number" id="limit" className="shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={limit} onChange={(e) => setLimit(parseInt(e.target.value))} min="1" max="50" />
        </div>
        <div>
          <label htmlFor="skip" className="block text-gray-700 text-sm font-bold mb-2">Skip</label>
          <input type="number" id="skip" className="shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={skip} onChange={(e) => setSkip(parseInt(e.target.value))} min="0" />
        </div>
      </div>

      {recommendations.length === 0 ? (
        <p>No recommendations found. Make sure your profile is updated and you have added some jobs.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recommendations.map((rec) => (
            <div key={rec.job_id} className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-2">{rec.title} at {rec.company}</h2>
              <p className="text-gray-600 mb-2">{rec.location}</p>
              <div className="mb-4">
                <span className="inline-block bg-blue-200 text-blue-800 text-xs px-2 rounded-full">Match Score: {rec.match_score.toFixed(0)}%</span>
              </div>
              {rec.tech_stack && rec.tech_stack.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-semibold">Tech Stack:</p>
                  <div className="flex flex-wrap gap-2">
                    {rec.tech_stack.map((skill) => (
                      <span key={skill} className="bg-gray-200 text-gray-800 text-xs px-2 py-1 rounded">{skill}</span>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex justify-between items-center mt-4">
                <button
                  onClick={() => handleApply(rec.job_id, rec.title, rec.match_score)}
                  className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-sm"
                >
                  Apply
                </button>
                {rec.link && (
                  <a
                    href={rec.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:underline text-sm"
                  >
                    View Job
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
