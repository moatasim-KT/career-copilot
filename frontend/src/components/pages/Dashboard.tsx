'use client';

import {
  Briefcase,
  FileText,
  Calendar,
  Trophy,
  TrendingUp,
  Target,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react';
import { useState, useEffect } from 'react';

import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [recentApplications, setRecentApplications] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refreshDashboard = async () => {
    setIsLoading(true);
    try {
      const [analyticsResp, recentResp] = await Promise.all([
        apiClient.getAnalyticsSummary(),
        apiClient.getApplications(0, 5),
      ]);

      if (analyticsResp && !analyticsResp.error && analyticsResp.data) {
        setAnalytics(analyticsResp.data);
      }
      if (recentResp && !recentResp.error && recentResp.data) {
        setRecentApplications(recentResp.data);
      }
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to refresh dashboard');
      logger.error('Dashboard: refresh failed', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    (async () => {
      setIsLoading(true);
      try {
        const [analyticsResp, recentResp] = await Promise.all([
          apiClient.getAnalyticsSummary(),
          apiClient.getApplications(0, 5),
        ]);

        if (!mounted) return;

        if (analyticsResp && !analyticsResp.error && analyticsResp.data) {
          setAnalytics(analyticsResp.data);
        }
        if (recentResp && !recentResp.error && recentResp.data) {
          setRecentApplications(recentResp.data);
        }
        setLastUpdated(new Date());
      } catch (err) {
        setError('Failed to load dashboard data');
        logger.error('Dashboard: initial load failed', err);
      } finally {
        if (mounted) setIsLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const getStatusIcon = (status: string | undefined) => {
    switch (status) {
      case 'interested':
        return <Clock className="h-4 w-4 text-yellow-500" />;
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
        return <XCircle className="h-4 w-4 text-neutral-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-neutral-400" />;
    }
  };

  const getStatusColor = (status: string | undefined) => {
    switch (status) {
      case 'interested':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'applied':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      case 'interview':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300';
      case 'offer':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'accepted':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'rejected':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      case 'declined':
        return 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-300';
      default:
        return 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-300';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
                <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero Section with Gradient */}
      <div className="gradient-mesh rounded-2xl p-4 sm:p-6 md:p-12 relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="flex-1">
              <h1 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-white mb-3">
                Welcome Back
              </h1>
              <p className="text-lg text-neutral-700 dark:text-neutral-200 max-w-2xl">
                Track your job applications, monitor your progress, and stay on top of your career goals.
              </p>
            </div>

            <div className="flex items-center space-x-3">
              {lastUpdated && (
                <span className="text-sm text-neutral-700 dark:text-neutral-200 font-medium">
                  Updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={refreshDashboard}
                disabled={isLoading}
                className="flex items-center space-x-2 px-6 py-3 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                <TrendingUp className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                <span>{isLoading ? 'Loading...' : 'Refresh'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400 dark:text-red-500" />
            <div className="ml-3">
              <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center">
            <Briefcase className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            <div className="ml-4">
              <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">Total Jobs</p>
              <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {analytics?.total_jobs || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-green-600 dark:text-green-400" />
            <div className="ml-4">
              <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">Applications</p>
              <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {analytics?.total_applications || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-purple-600 dark:text-purple-400" />
            <div className="ml-4">
              <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">Interviews</p>
              <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {analytics?.interviews_scheduled || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center">
            <Trophy className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
            <div className="ml-4">
              <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">Offers</p>
              <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {analytics?.offers_received || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Goal */}
      {analytics && (
        <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 flex items-center">
              <Target className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
              Daily Application Goal
            </h2>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-neutral-900 dark:text-neutral-100">
              <span>Progress</span>
              <span>
                {analytics.daily_applications_today} / {analytics.daily_application_goal}
              </span>
            </div>
            <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
              <div
                className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${Math.min(analytics.daily_goal_progress ?? 0, 100)}%`,
                }}
              ></div>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              {(analytics.daily_goal_progress ?? 0) >= 100
                ? '🎉 Goal achieved today!'
                : `${(analytics.daily_application_goal ?? 0) - (analytics.daily_applications_today ?? 0)} more applications to reach your goal`}
            </p>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
        <div className="p-4 sm:p-6 border-b border-neutral-200 dark:border-neutral-700">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">Recent Activity</h2>
        </div>
        <div className="p-4 sm:p-6">
          {recentApplications.length > 0 ? (
            <div className="space-y-4">
              {recentApplications.map((application) => (
                <div key={application.id} className="flex items-center justify-between p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {getStatusIcon(application.status)}
                    </div>
                    <div>
                      <p className="font-medium text-neutral-900 dark:text-neutral-100">
                        {application.job_title || 'Unknown Position'}
                      </p>
                      <p className="text-sm text-neutral-600 dark:text-neutral-400">
                        {application.job_company || 'Unknown Company'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(application.status)}`}>
                      {application.status?.charAt(0).toUpperCase()}{application.status?.slice(1)}
                    </span>
                    {application.applied_at && (
                      <span className="text-sm text-neutral-500 dark:text-neutral-400">
                        {new Date(application.applied_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
              <p className="text-neutral-600 dark:text-neutral-400">No applications yet</p>
              <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
                Start by adding jobs and applying to them
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Status Breakdown */}
      {analytics?.application_status_breakdown && Object.keys(analytics.application_status_breakdown).length > 0 && (
        <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">Application Status Breakdown</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(analytics.application_status_breakdown).map(([status, count]) => (
              <div key={status} className="text-center">
                <div className="flex justify-center mb-2">
                  {getStatusIcon(status)}
                </div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{String(count)}</p>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 capitalize">{status}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}