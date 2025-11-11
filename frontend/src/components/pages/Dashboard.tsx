'use client';

import { TrendingUp, AlertCircle } from 'lucide-react';
import { useState, useEffect } from 'react';

import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';
import {
  ApplicationStatusChart,
  ApplicationTimelineChart,
  SalaryDistributionChart,
  SkillsDemandChart,
  SuccessRateChart,
} from '../charts';
import { DraggableDashboard } from '../dashboard';
import {
  MetricsWidget,
  DailyGoalWidget,
  RecentActivityWidget,
  StatusBreakdownWidget,
} from '../dashboard/widgets';
import { DashboardWidget as DashboardWidgetType } from '@/types/dashboard';

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

  // Render widget based on type
  const renderWidget = (widget: DashboardWidgetType) => {
    switch (widget.type) {
      case 'metrics':
        return <MetricsWidget analytics={analytics} />;

      case 'application-status-chart':
        return <ApplicationStatusChart className="h-full" />;

      case 'application-timeline-chart':
        return <ApplicationTimelineChart className="h-full" />;

      case 'salary-distribution-chart':
        return (
          <SalaryDistributionChart
            userTargetSalary={analytics?.target_salary}
            className="h-full"
          />
        );

      case 'skills-demand-chart':
        return (
          <SkillsDemandChart userSkills={analytics?.user_skills || []} className="h-full" />
        );

      case 'success-rate-chart':
        return <SuccessRateChart showBenchmark={true} className="h-full" />;

      case 'daily-goal':
        return <DailyGoalWidget analytics={analytics} />;

      case 'recent-activity':
        return <RecentActivityWidget recentApplications={recentApplications} />;

      case 'status-breakdown':
        return <StatusBreakdownWidget analytics={analytics} />;

      default:
        return null;
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
              <h1 className="text-2xl md:text-4xl font-bold text-neutral-900 dark:text-white mb-3">
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

      {/* Draggable Dashboard Widgets */}
      <DraggableDashboard>{renderWidget}</DraggableDashboard>
    </div>
  );
}