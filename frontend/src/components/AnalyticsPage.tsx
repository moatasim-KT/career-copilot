'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAnalyticsUpdates } from '@/hooks/useWebSocket';
import { apiClient } from '@/lib/api';
import Card from './ui/Card';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
  ComposedChart
} from 'recharts';
import { 
  TrendingUp, 
  Users, 
  Briefcase, 
  Calendar, 
  Award,
  Target,
  Activity,
  BarChart3
} from 'lucide-react';
import { AnalyticsSummary } from '@/lib/api';

interface StatusBreakdownData {
  status: string;
  count: number;
  color: string;
}

interface SkillData {
  skill: string;
  count: number;
}

interface CompanyData {
  company: string;
  count: number;
}

const STATUS_COLORS = {
  interested: '#3B82F6',
  applied: '#F59E0B',
  interview: '#10B981',
  offer: '#8B5CF6',
  rejected: '#EF4444',
  accepted: '#059669',
  declined: '#6B7280'
};

const STATUS_LABELS = {
  interested: 'Interested',
  applied: 'Applied',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
  accepted: 'Accepted',
  declined: 'Declined'
};

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [comprehensiveData, setComprehensiveData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState(90);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Handle real-time analytics updates
  const handleAnalyticsUpdate = useCallback((data: any) => {
    console.log('Analytics page received update:', data);
    if (data.analytics) {
      setAnalytics(data.analytics);
      setLastUpdated(new Date());
    }
    if (data.comprehensive) {
      setComprehensiveData(data.comprehensive);
    }
    setLoading(false);
  }, []);

  // Set up WebSocket listener for analytics updates
  useAnalyticsUpdates(handleAnalyticsUpdate);

  const loadAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [analyticsResponse, comprehensiveResponse] = await Promise.all([
        apiClient.getAnalyticsSummary(),
        apiClient.getComprehensiveAnalytics(timeframe)
      ]);

      if (analyticsResponse.error) {
        setError(analyticsResponse.error);
      } else if (analyticsResponse.data) {
        setAnalytics(analyticsResponse.data);
      }

      if (comprehensiveResponse.data) {
        setComprehensiveData(comprehensiveResponse.data);
      }

      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalyticsData();
  }, [timeframe]);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <Card key={i} className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <Card className="p-6">
          <div className="text-center">
            <div className="text-red-500 mb-2">⚠️</div>
            <p className="text-gray-600">Error loading analytics: {error}</p>
            <button 
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        </Card>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <Card className="p-6">
          <p className="text-gray-600">No analytics data available</p>
        </Card>
      </div>
    );
  }

  // Prepare data for charts
  const statusBreakdownData: StatusBreakdownData[] = Object.entries(analytics.application_status_breakdown || {})
    .map(([status, count]) => ({
      status: STATUS_LABELS[status as keyof typeof STATUS_LABELS] || status,
      count: count as number,
      color: STATUS_COLORS[status as keyof typeof STATUS_COLORS] || '#6B7280'
    }));

  const skillsData: SkillData[] = (analytics.top_skills_in_jobs || []).map(item => ({
    skill: item.skill,
    count: item.count
  }));

  const companiesData: CompanyData[] = (analytics.top_companies_applied || []).map(item => ({
    company: item.company,
    count: item.count
  }));

  const applicationTrendData = [
    { period: 'Today', applications: analytics.daily_applications_today },
    { period: 'This Week', applications: analytics.weekly_applications },
    { period: 'This Month', applications: analytics.monthly_applications }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <div className="flex items-center space-x-3">
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={loadAnalyticsData}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <TrendingUp className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Loading...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Jobs</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.total_jobs}</p>
            </div>
            <Briefcase className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Applications</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.total_applications}</p>
            </div>
            <Users className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Interviews</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.interviews_scheduled}</p>
            </div>
            <Calendar className="w-8 h-8 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Offers</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.offers_received}</p>
            </div>
            <Award className="w-8 h-8 text-yellow-500" />
          </div>
        </Card>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending Applications</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.pending_applications}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-orange-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Acceptance Rate</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.acceptance_rate}%</p>
            </div>
            <Target className="w-8 h-8 text-indigo-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Daily Goal Progress</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.daily_goal_progress}%</p>
            </div>
            <BarChart3 className="w-8 h-8 text-pink-500" />
          </div>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-pink-500 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${Math.min(analytics.daily_goal_progress, 100)}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {analytics.daily_applications_today} / {analytics.daily_application_goal} applications today
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Rejections</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.rejections_received}</p>
            </div>
            <Activity className="w-8 h-8 text-red-500" />
          </div>
        </Card>
      </div>

      {/* Time Range Selector */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Analytics Timeframe</h3>
          <div className="flex gap-2">
            {[30, 60, 90, 180].map((days) => (
              <button
                key={days}
                onClick={() => setTimeframe(days)}
                className={`px-3 py-1 rounded text-sm ${
                  timeframe === days
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Application Status Breakdown */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Status Breakdown</h3>
          {statusBreakdownData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusBreakdownData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ status, count, percent }) => `${status}: ${count} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {statusBreakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              No application data available
            </div>
          )}
        </Card>

        {/* Application Trends */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={applicationTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="applications" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Application Timeline and Performance Trends */}
      {comprehensiveData && (
        <div className="grid grid-cols-1 gap-6">
          {/* Application Timeline */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Timeline</h3>
            {comprehensiveData.application_trends && comprehensiveData.application_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={comprehensiveData.application_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(date) => new Date(date).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(date) => new Date(date).toLocaleDateString()}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="applications" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No timeline data available
              </div>
            )}
          </Card>

          {/* Weekly Performance Trends */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Performance Trends</h3>
            {comprehensiveData.weekly_performance && comprehensiveData.weekly_performance.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={comprehensiveData.weekly_performance.reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="week_start" 
                    tickFormatter={(date) => new Date(date).toLocaleDateString()}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip 
                    labelFormatter={(date) => `Week of ${new Date(date).toLocaleDateString()}`}
                    formatter={(value, name) => [
                      typeof name === 'string' && name.includes('rate') ? `${(value as number).toFixed(1)}%` : value,
                      name
                    ]}
                  />
                  <Legend />
                  <Bar yAxisId="left" dataKey="applications" fill="#3B82F6" name="Applications" />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="interview_rate" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    name="Interview Rate (%)"
                  />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="offer_rate" 
                    stroke="#F59E0B" 
                    strokeWidth={2}
                    name="Offer Rate (%)"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No performance trend data available
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Skills and Companies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Skills */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Skills in Jobs</h3>
          {skillsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={skillsData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="skill" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="count" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              No skills data available
            </div>
          )}
        </Card>

        {/* Top Companies */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Companies Applied</h3>
          {companiesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={companiesData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="company" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="count" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              No company data available
            </div>
          )}
        </Card>
      </div>

      {/* Summary Stats */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="font-medium text-blue-900">Weekly Activity</p>
            <p className="text-blue-700">{analytics.weekly_applications} applications this week</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="font-medium text-green-900">Monthly Progress</p>
            <p className="text-green-700">{analytics.monthly_applications} applications this month</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <p className="font-medium text-purple-900">Success Rate</p>
            <p className="text-purple-700">
              {analytics.offers_received > 0 
                ? `${((analytics.offers_received / analytics.total_applications) * 100).toFixed(1)}% offer rate`
                : 'No offers yet'
              }
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}