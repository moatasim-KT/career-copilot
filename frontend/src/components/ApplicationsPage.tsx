'use client';

import { useState, useEffect } from 'react';
import { apiClient, type Application } from '@/lib/api';
import { 
  FileText, 
  Calendar, 
  Building, 
  MapPin,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Trophy,
  Eye
} from 'lucide-react';

const STATUS_OPTIONS = [
  'interested', 'applied', 'interview', 'offer', 'rejected', 'accepted', 'declined'
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [expandedApp, setExpandedApp] = useState<number | null>(null);

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.getApplications();
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setApplications(response.data);
      }
    } catch (err) {
      setError('Failed to load applications');
    } finally {
      setIsLoading(false);
    }
  };

  const updateApplicationStatus = async (appId: number, newStatus: string) => {
    try {
      const response = await apiClient.updateApplication(appId, { status: newStatus as any });
      if (response.error) {
        setError(response.error);
      } else {
        loadApplications();
      }
    } catch (err) {
      setError('Failed to update application');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'interested':
        return <Eye className="h-4 w-4 text-yellow-500" />;
      case 'applied':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'interview':
        return <Calendar className="h-4 w-4 text-purple-500" />;
      case 'offer':
        return <Trophy className="h-4 w-4 text-green-500" />;
      case 'accepted':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'declined':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'interested':
        return 'bg-yellow-100 text-yellow-800';
      case 'applied':
        return 'bg-blue-100 text-blue-800';
      case 'interview':
        return 'bg-purple-100 text-purple-800';
      case 'offer':
        return 'bg-green-100 text-green-800';
      case 'accepted':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'declined':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredApplications = applications.filter(app =>
    statusFilter === 'All' || app.status === statusFilter
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Applications</h1>
        <div className="flex items-center space-x-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="All">All Status</option>
            {STATUS_OPTIONS.map(status => (
              <option key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="text-sm text-gray-600">
        Showing {filteredApplications.length} application(s)
        {statusFilter !== 'All' && ` with status: ${statusFilter}`}
      </div>

      {filteredApplications.length > 0 ? (
        <div className="space-y-4">
          {filteredApplications.map((application) => (
            <div key={application.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {application.job?.title || 'Unknown Position'}
                      </h3>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(application.status)}
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(application.status)}`}>
                          {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                      <div className="flex items-center space-x-1">
                        <Building className="h-4 w-4" />
                        <span>{application.job?.company || 'Unknown Company'}</span>
                      </div>
                      {application.job?.location && (
                        <div className="flex items-center space-x-1">
                          <MapPin className="h-4 w-4" />
                          <span>{application.job.location}</span>
                        </div>
                      )}
                      {application.applied_date && (
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>Applied {new Date(application.applied_date).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>

                    {application.notes && (
                      <p className="text-sm text-gray-600 mb-3">
                        <strong>Notes:</strong> {application.notes}
                      </p>
                    )}

                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      {application.interview_date && (
                        <span>Interview: {new Date(application.interview_date).toLocaleDateString()}</span>
                      )}
                      {application.response_date && (
                        <span>Response: {new Date(application.response_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>

                  <div className="ml-4">
                    <select
                      value={application.status}
                      onChange={(e) => updateApplicationStatus(application.id, e.target.value)}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      {STATUS_OPTIONS.map(status => (
                        <option key={status} value={status}>
                          {status.charAt(0).toUpperCase() + status.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Interview Feedback Section */}
                {application.interview_feedback && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Interview Feedback</h4>
                    
                    {application.interview_feedback.questions && application.interview_feedback.questions.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-medium text-gray-700">Questions Asked:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {application.interview_feedback.questions.map((question, idx) => (
                            <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                              {question}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {application.interview_feedback.skill_areas && application.interview_feedback.skill_areas.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-medium text-gray-700">Skill Areas Discussed:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {application.interview_feedback.skill_areas.map((skill, idx) => (
                            <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {application.interview_feedback.notes && (
                      <div>
                        <p className="text-xs font-medium text-gray-700">Notes:</p>
                        <p className="text-sm text-gray-600 mt-1">{application.interview_feedback.notes}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Job Tech Stack */}
                {application.job?.tech_stack && application.job.tech_stack.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-xs font-medium text-gray-700 mb-2">Required Tech Stack:</p>
                    <div className="flex flex-wrap gap-1">
                      {application.job.tech_stack.slice(0, 10).map((tech) => (
                        <span key={tech} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                          {tech}
                        </span>
                      ))}
                      {application.job.tech_stack.length > 10 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          +{application.job.tech_stack.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">
            {statusFilter === 'All' ? 'No applications yet' : `No applications with status: ${statusFilter}`}
          </p>
          <p className="text-sm text-gray-500">
            {statusFilter === 'All' 
              ? 'Start by adding jobs and applying to them' 
              : 'Try selecting a different status filter'
            }
          </p>
        </div>
      )}
    </div>
  );
}