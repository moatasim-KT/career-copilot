'use client';

import { useState, useEffect } from 'react';

import Button2 from '@/components/ui/Button2';
import Card2, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card2';
import Container from '@/components/ui/Container';
import { apiClient, Job } from '@/lib/api';

interface SkillGapAnalysis {
  user_skills: string[];
  missing_skills: string[];
  top_market_skills: string[];
  skill_coverage_percentage: number;
  recommendations: string[];
}

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Job[]>([]);
  const [skillGapAnalysis, setSkillGapAnalysis] = useState<SkillGapAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'recommendations' | 'skill-gap'>('recommendations');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load recommendations
      const recommendationsResponse = await apiClient.getRecommendations(0, 10);
      if (recommendationsResponse.error) {
        throw new Error(recommendationsResponse.error);
      }
      setRecommendations(recommendationsResponse.data || []);

      // Load skill gap analysis
      const skillGapResponse = await apiClient.getSkillGapAnalysis();
      if (skillGapResponse.error) {
        throw new Error(skillGapResponse.error);
      }
      setSkillGapAnalysis(skillGapResponse.data || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyToJob = async (jobId: number) => {
    try {
      const response = await apiClient.createApplication({
        job_id: jobId,
        status: 'interested',
        notes: 'Applied from recommendations',
      });

      if (response.error) {
        throw new Error(response.error);
      }

      // Refresh recommendations to remove applied job
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply to job');
    }
  };

  const formatMatchScore = (score?: number) => {
    if (!score) return 'N/A';
    return `${Math.round(score)}%`;
  };

  const getMatchScoreColor = (score?: number) => {
    if (!score) return 'text-neutral-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <Container>
        <div className="space-y-6">
          <h1 className="text-3xl font-bold text-neutral-900">Job Recommendations & Skill Analysis</h1>
          <Card2>
            <CardContent>
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-neutral-600">Loading recommendations...</span>
              </div>
            </CardContent>
          </Card2>
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <div className="space-y-6">
          <h1 className="text-3xl font-bold text-neutral-900">Job Recommendations & Skill Analysis</h1>
          <Card2>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-red-600 mb-4">{error}</p>
                <Button2 onClick={loadData}>Try Again</Button2>
              </div>
            </CardContent>
          </Card2>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-neutral-900">Job Recommendations & Skill Analysis</h1>

        {/* Tab Navigation */}
        <div className="border-b border-neutral-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'recommendations'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                }`}
            >
              Job Recommendations ({recommendations.length})
            </button>
            <button
              onClick={() => setActiveTab('skill-gap')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'skill-gap'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              Skill Gap Analysis
            </button>
          </nav>
        </div>

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {recommendations.length === 0 ? (
              <Card2>
                <CardContent>
                  <div className="text-center py-8">
                    <p className="text-neutral-600 mb-4">No job recommendations available.</p>
                    <p className="text-sm text-neutral-500">
                      Add some jobs and update your profile to get personalized recommendations.
                    </p>
                  </div>
                </CardContent>
              </Card2>
            ) : (
              recommendations.map((job) => (
                <Card2 key={job.id} hover className="transition-all duration-200">
                  <CardContent>
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold text-neutral-900 mb-1">
                          {job.title}
                        </h3>
                        <p className="text-lg text-neutral-700 mb-2">{job.company}</p>
                        {job.location && (
                          <p className="text-sm text-neutral-600 mb-2">📍 {job.location}</p>
                        )}
                        {job.salary_range && (
                          <p className="text-sm text-neutral-600 mb-2">💰 {job.salary_range}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${getMatchScoreColor(job.match_score)}`}>
                          {formatMatchScore(job.match_score)}
                        </div>
                        <p className="text-xs text-neutral-500">Match Score</p>
                      </div>
                    </div>

                    {job.tech_stack && job.tech_stack.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-neutral-700 mb-2">Tech Stack:</p>
                        <div className="flex flex-wrap gap-2">
                          {job.tech_stack.map((tech, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                            >
                              {tech}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {job.description && (
                      <div className="mb-4">
                        <p className="text-sm text-neutral-600 line-clamp-3">
                          {job.description}
                        </p>
                      </div>
                    )}

                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-4 text-sm text-neutral-500">
                        <span className="capitalize">{job.job_type}</span>
                        {job.remote && <span>🏠 Remote</span>}
                        <span>Source: {job.source}</span>
                      </div>
                      <div className="flex space-x-2">
                        {job.url && (
                          <Button2
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(job.url, '_blank')}
                          >
                            View Job
                          </Button2>
                        )}
                        <Button2
                          size="sm"
                          onClick={() => handleApplyToJob(job.id)}
                        >
                          Apply
                        </Button2>
                      </div>
                    </div>
                  </CardContent>
                </Card2>
              ))
            )}
          </div>
        )}

        {/* Skill Gap Analysis Tab */}
        {activeTab === 'skill-gap' && (
          <div className="space-y-6">
            {!skillGapAnalysis ? (
              <Card2>
                <CardContent>
                  <div className="text-center py-8">
                    <p className="text-neutral-600 mb-4">No skill gap analysis available.</p>
                    <p className="text-sm text-neutral-500">
                      Add some jobs to your list to get skill gap insights.
                    </p>
                  </div>
                </CardContent>
              </Card2>
            ) : (
              <>
                {/* Skill Coverage Overview */}
                <Card2>
                  <CardHeader>
                    <CardTitle>Skill Coverage Overview</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-3xl font-bold text-blue-600">
                          {Math.round(skillGapAnalysis.skill_coverage_percentage)}%
                        </p>
                        <p className="text-sm text-neutral-600">Skills Coverage</p>
                      </div>
                      <div className="w-32 h-32">
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="3"
                          />
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#3b82f6"
                            strokeWidth="3"
                            strokeDasharray={`${skillGapAnalysis.skill_coverage_percentage}, 100`}
                          />
                        </svg>
                      </div>
                    </div>
                    <p className="text-sm text-neutral-600">
                      You have {skillGapAnalysis.user_skills.length} skills out of {skillGapAnalysis.top_market_skills.length} top market skills.
                    </p>
                  </CardContent>
                </Card2>

                {/* Your Skills */}
                <Card2>
                  <CardHeader>
                    <CardTitle>Your Current Skills ({skillGapAnalysis.user_skills.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {skillGapAnalysis.user_skills.length === 0 ? (
                      <p className="text-neutral-600">No skills added to your profile yet.</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {skillGapAnalysis.user_skills.map((skill, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full"
                          >
                            ✓ {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card2>

                {/* Missing Skills */}
                <Card2>
                  <CardHeader>
                    <CardTitle>Skills to Learn ({skillGapAnalysis.missing_skills.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {skillGapAnalysis.missing_skills.length === 0 ? (
                      <p className="text-neutral-600">Great! You have all the skills from your target jobs.</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {skillGapAnalysis.missing_skills.map((skill, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded-full"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card2>

                {/* Top Market Skills */}
                <Card2>
                  <CardHeader>
                    <CardTitle>Top Market Skills</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {skillGapAnalysis.top_market_skills.map((skill, index) => (
                        <span
                          key={index}
                          className={`px-3 py-1 text-sm rounded-full ${skillGapAnalysis.user_skills.includes(skill)
                              ? 'bg-green-100 text-green-800'
                              : 'bg-neutral-100 text-neutral-800'
                            }`}
                        >
                          {skillGapAnalysis.user_skills.includes(skill) ? '✓ ' : ''}{skill}
                        </span>
                      ))}
                    </div>
                  </CardContent>
                </Card2>

                {/* Learning Recommendations */}
                {skillGapAnalysis.recommendations.length > 0 && (
                  <Card2>
                    <CardHeader>
                      <CardTitle>Learning Recommendations</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {skillGapAnalysis.recommendations.map((recommendation, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span className="text-neutral-700">{recommendation}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card2>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </Container>
  );
}