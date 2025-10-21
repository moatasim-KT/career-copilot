import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Progress } from './ui/Progress';
import { 
  DocumentTextIcon, 
  ArrowTrendingUpIcon, 
  ExclamationCircleIcon, 
  CheckCircleIcon, 
  StarIcon,
  FlagIcon,
  ChartBarIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface DocumentSuggestion {
  document_id: number;
  document_type: string;
  filename: string;
  relevance_score: number;
  suggestion_reason: string;
  performance_metrics: {
    total_applications: number;
    response_rate: number;
    interview_rate: number;
    success_rate: number;
    last_30_days_usage: number;
  };
  usage_count: number;
  last_used?: string;
}

interface DocumentOptimizationRecommendation {
  type: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  estimated_impact: string;
}

interface JobDocumentMatch {
  job_id: number;
  job_title: string;
  company: string;
  overall_match_score: number;
  matching_documents: Array<{
    document_id: number;
    document_type: string;
    filename: string;
    relevance_score: number;
  }>;
  missing_document_types: string[];
}

interface DocumentSuggestionsProps {
  jobId?: number;
  documentId?: number;
  mode: 'job-suggestions' | 'document-optimization' | 'job-matches' | 'portfolio-analysis';
}

const DocumentSuggestions: React.FC<DocumentSuggestionsProps> = ({ 
  jobId, 
  documentId, 
  mode 
}) => {
  const [suggestions, setSuggestions] = useState<DocumentSuggestion[]>([]);
  const [recommendations, setRecommendations] = useState<DocumentOptimizationRecommendation[]>([]);
  const [jobMatches, setJobMatches] = useState<JobDocumentMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mode === 'job-suggestions' && jobId) {
      fetchDocumentSuggestions();
    } else if (mode === 'document-optimization' && documentId) {
      fetchOptimizationRecommendations();
    } else if (mode === 'job-matches') {
      fetchJobDocumentMatches();
    }
  }, [mode, jobId, documentId]);

  const fetchDocumentSuggestions = async () => {
    if (!jobId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/document-suggestions/job/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch document suggestions');
      }
      
      const data = await response.json();
      setSuggestions(data.suggestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchOptimizationRecommendations = async () => {
    if (!documentId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/v1/document-suggestions/document/${documentId}/optimization`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch optimization recommendations');
      }
      
      const data = await response.json();
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobDocumentMatches = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/document-suggestions/job-matches', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch job-document matches');
      }
      
      const data = await response.json();
      setJobMatches(data.matches);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDocumentTypeIcon = (type: string) => {
    switch (type) {
      case 'resume': return <DocumentTextIcon className="h-4 w-4" />;
      case 'cover_letter': return <DocumentTextIcon className="h-4 w-4" />;
      case 'portfolio': return <StarIcon className="h-4 w-4" />;
      default: return <DocumentTextIcon className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Loading suggestions...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center text-red-600">
            <ExclamationCircleIcon className="h-5 w-5 mr-2" />
            <span>{error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (mode === 'job-suggestions') {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FlagIcon className="h-5 w-5 mr-2" />
              Document Suggestions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {suggestions.length === 0 ? (
              <p className="text-gray-500">No document suggestions available.</p>
            ) : (
              <div className="space-y-4">
                {suggestions.map((suggestion) => (
                  <div key={suggestion.document_id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          {getDocumentTypeIcon(suggestion.document_type)}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium">{suggestion.filename}</h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {suggestion.suggestion_reason}
                          </p>
                          <div className="flex items-center space-x-4 mt-2">
                            <Badge className={getRelevanceColor(suggestion.relevance_score)}>
                              {Math.round(suggestion.relevance_score * 100)}% match
                            </Badge>
                            <span className="text-sm text-gray-500">
                              Used {suggestion.usage_count} times
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">Performance</div>
                        <div className="text-sm">
                          <div>Response: {Math.round(suggestion.performance_metrics.response_rate * 100)}%</div>
                          <div>Interview: {Math.round(suggestion.performance_metrics.interview_rate * 100)}%</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (mode === 'document-optimization') {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <LightBulbIcon className="h-5 w-5 mr-2" />
              Optimization Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recommendations.length === 0 ? (
              <p className="text-gray-500">No optimization recommendations available.</p>
            ) : (
              <div className="space-y-4">
                {recommendations.map((rec, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium">{rec.title}</h4>
                          <Badge className={getPriorityColor(rec.priority)}>
                            {rec.priority}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {rec.description}
                        </p>
                        <p className="text-sm text-blue-600 mt-2">
                          <ArrowTrendingUpIcon className="h-4 w-4 inline mr-1" />
                          {rec.estimated_impact}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (mode === 'job-matches') {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <ChartBarIcon className="h-5 w-5 mr-2" />
              Job-Document Matches
            </CardTitle>
          </CardHeader>
          <CardContent>
            {jobMatches.length === 0 ? (
              <p className="text-gray-500">No job-document matches available.</p>
            ) : (
              <div className="space-y-4">
                {jobMatches.map((match) => (
                  <div key={match.job_id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium">{match.job_title}</h4>
                        <p className="text-sm text-gray-600">{match.company}</p>
                        <div className="mt-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm">Overall Match:</span>
                            <Progress 
                              value={match.overall_match_score * 100} 
                              className="w-24 h-2"
                            />
                            <span className="text-sm font-medium">
                              {Math.round(match.overall_match_score * 100)}%
                            </span>
                          </div>
                        </div>
                        <div className="mt-2">
                          <div className="text-sm text-gray-600">
                            Matching documents: {match.matching_documents.length}
                          </div>
                          {match.missing_document_types.length > 0 && (
                            <div className="text-sm text-orange-600">
                              Missing: {match.missing_document_types.join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                      <Button variant="secondary" size="sm">
                        View Job
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};

export default DocumentSuggestions;