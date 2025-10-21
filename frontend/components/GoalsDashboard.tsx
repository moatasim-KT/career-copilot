import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Progress } from './ui/Progress';
import { Badge } from './ui/Badge';
import { 
  FlagIcon, 
  ArrowTrendingUpIcon, 
  TrophyIcon, 
  CalendarIcon, 
  PlusIcon,
  CheckCircleIcon,
  ClockIcon,
  FireIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../utils/api';

interface Goal {
  id: number;
  goal_type: string;
  title: string;
  description?: string;
  target_value: number;
  current_value: number;
  unit: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  is_completed: boolean;
  completed_at?: string;
  progress_percentage: number;
  days_remaining?: number;
  is_overdue: boolean;
  recent_progress: any[];
}

interface Milestone {
  id: number;
  milestone_type: string;
  title: string;
  description?: string;
  achievement_value?: number;
  achievement_date: string;
  metadata: any;
  is_celebrated: boolean;
}

interface MotivationalMessage {
  message_type: string;
  title: string;
  message: string;
  context: any;
  priority: string;
}

interface GoalSummaryStats {
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  overdue_goals: number;
  goals_completion_rate: number;
  current_streak: number;
  longest_streak: number;
  total_milestones: number;
  recent_milestones: number;
}

interface GoalDashboardData {
  summary_stats: GoalSummaryStats;
  active_goals: Goal[];
  recent_milestones: Milestone[];
  motivational_messages: MotivationalMessage[];
  weekly_progress_chart: any[];
  goal_completion_trend: any[];
}

const GoalsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<GoalDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateGoal, setShowCreateGoal] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/goals/dashboard`);
      const data = await response.json();
      setDashboardData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getGoalTypeIcon = (goalType: string) => {
    switch (goalType) {
      case 'daily_applications':
      case 'weekly_applications':
      case 'monthly_applications':
        return <FlagIcon className="h-4 w-4" />;
      case 'skill_development':
        return <ArrowTrendingUpIcon className="h-4 w-4" />;
      default:
        return <FlagIcon className="h-4 w-4" />;
    }
  };

  const getGoalTypeColor = (goalType: string) => {
    switch (goalType) {
      case 'daily_applications':
        return 'bg-blue-100 text-blue-800';
      case 'weekly_applications':
        return 'bg-green-100 text-green-800';
      case 'monthly_applications':
        return 'bg-purple-100 text-purple-800';
      case 'skill_development':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getMilestoneIcon = (milestoneType: string) => {
    switch (milestoneType) {
      case 'application_streak':
        return <FireIcon className="h-4 w-4 text-orange-500" />;
      case 'goal_achievement':
        return <TrophyIcon className="h-4 w-4 text-yellow-500" />;
      default:
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    }
  };

  const getMessagePriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'border-red-200 bg-red-50';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50';
      case 'low':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={fetchDashboardData}>Try Again</Button>
      </div>
    );
  }

  if (!dashboardData) {
    return <div>No data available</div>;
  }

  const { summary_stats, active_goals, recent_milestones, motivational_messages } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Goals Dashboard</h1>
          <p className="text-gray-600">Track your career progress and achievements</p>
        </div>
        <Button onClick={() => setShowCreateGoal(true)} className="flex items-center gap-2">
          <PlusIcon className="h-4 w-4" />
          New Goal
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Goals</p>
                <p className="text-2xl font-bold text-gray-900">{summary_stats.active_goals}</p>
              </div>
              <FlagIcon className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completion Rate</p>
                <p className="text-2xl font-bold text-gray-900">{summary_stats.goals_completion_rate}%</p>
              </div>
              <ArrowTrendingUpIcon className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Current Streak</p>
                <p className="text-2xl font-bold text-gray-900">{summary_stats.current_streak} days</p>
              </div>
              <FireIcon className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Milestones</p>
                <p className="text-2xl font-bold text-gray-900">{summary_stats.recent_milestones}</p>
                <p className="text-xs text-gray-500">this month</p>
              </div>
              <TrophyIcon className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Motivational Messages */}
      {motivational_messages.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">Messages for You</h2>
          {motivational_messages.map((message, index) => (
            <Card key={index} className={`border-l-4 ${getMessagePriorityColor(message.priority)}`}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{message.title}</h3>
                    <p className="text-gray-600 mt-1">{message.message}</p>
                  </div>
                  <Badge variant="outline" className="capitalize">
                    {message.message_type}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Goals */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FlagIcon className="h-5 w-5" />
              Active Goals
            </CardTitle>
          </CardHeader>
          <CardContent>
            {active_goals.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FlagIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No active goals yet</p>
                <Button 
                  variant="secondary" 
                  className="mt-4"
                  onClick={() => setShowCreateGoal(true)}
                >
                  Create Your First Goal
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {active_goals.map((goal) => (
                  <div key={goal.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {getGoalTypeIcon(goal.goal_type)}
                          <h3 className="font-medium text-gray-900">{goal.title}</h3>
                          <Badge className={getGoalTypeColor(goal.goal_type)}>
                            {goal.goal_type.replace('_', ' ')}
                          </Badge>
                        </div>
                        {goal.description && (
                          <p className="text-sm text-gray-600 mb-2">{goal.description}</p>
                        )}
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>{goal.current_value} / {goal.target_value} {goal.unit}</span>
                          {goal.days_remaining !== null && (
                            <span className="flex items-center gap-1">
                              <CalendarIcon className="h-3 w-3" />
                              {(goal.days_remaining ?? 0) > 0 
                                ? `${goal.days_remaining} days left`
                                : goal.is_overdue 
                                  ? 'Overdue'
                                  : 'Due today'
                              }
                            </span>
                          )}
                        </div>
                      </div>
                      {goal.is_overdue && (
                        <Badge variant="destructive">Overdue</Badge>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Progress</span>
                        <span>{goal.progress_percentage.toFixed(0)}%</span>
                      </div>
                      <Progress 
                        value={goal.progress_percentage} 
                        className={`h-2 ${goal.is_overdue ? 'bg-red-100' : ''}`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Milestones */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrophyIcon className="h-5 w-5" />
              Recent Achievements
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recent_milestones.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <TrophyIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No achievements yet</p>
                <p className="text-sm">Complete goals to earn milestones!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recent_milestones.slice(0, 5).map((milestone) => (
                  <div key={milestone.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    {getMilestoneIcon(milestone.milestone_type)}
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{milestone.title}</h4>
                      {milestone.description && (
                        <p className="text-sm text-gray-600">{milestone.description}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(milestone.achievement_date).toLocaleDateString()}
                      </p>
                    </div>
                    {!milestone.is_celebrated && (
                      <Badge variant="secondary">New!</Badge>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GoalsDashboard;