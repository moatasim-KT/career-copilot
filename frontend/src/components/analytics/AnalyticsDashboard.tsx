/**
 * Analytics Dashboard
 * 
 * Enterprise-grade analytics dashboard with real-time metrics,
 * time period selection, and interactive charts.
 * 
 * @module components/analytics/AnalyticsDashboard
 */

'use client';

import { useEffect, useState } from 'react';

import {
    LineChartComponent,
    BarChartComponent,
    PieChartComponent,
    AreaChartComponent,
    ChartDataPoint,
} from '@/components/charts/DataVisualization';
import apiClient from '@/lib/api/client';
import { logger } from '@/lib/logger';

export interface AnalyticsData {
    applications: {
        total: number;
        thisWeek: number;
        thisMonth: number;
        trend: ChartDataPoint[];
    };
    interviews: {
        total: number;
        scheduled: number;
        completed: number;
        successRate: number;
    };
    offers: {
        total: number;
        pending: number;
        accepted: number;
        rejected: number;
    };
    statusDistribution: ChartDataPoint[];
    companyDistribution: ChartDataPoint[];
    weeklyActivity: ChartDataPoint[];
}

type TimePeriod = '7d' | '30d' | '90d' | '1y' | 'all';

/**
 * Metric Card Component
 */
function MetricCard({
    title,
    value,
    change,
    changeType,
    icon,
}: {
    title: string;
    value: string | number;
    change?: string;
    changeType?: 'positive' | 'negative' | 'neutral';
    icon?: React.ReactNode;
}) {
    const changeColors = {
        positive: 'text-green-600 bg-green-100',
        negative: 'text-red-600 bg-red-100',
        neutral: 'text-neutral-600 bg-neutral-100',
    };

    return (
        <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-600">{title}</p>
                    <p className="mt-2 text-3xl font-bold text-neutral-900">{value}</p>
                    {change && changeType && (
                        <div className="mt-2 flex items-center gap-1">
                            <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${changeColors[changeType]}`}
                            >
                                {changeType === 'positive' && '↑'}
                                {changeType === 'negative' && '↓'}
                                {change}
                            </span>
                            <span className="text-xs text-neutral-500">vs last period</span>
                        </div>
                    )}
                </div>
                {icon && (
                    <div className="rounded-lg bg-blue-100 p-3 text-blue-600">
                        {icon}
                    </div>
                )}
            </div>
        </div>
    );
}

/**
 * Analytics Dashboard Component
 * 
 * @example
 * ```tsx
 * <AnalyticsDashboard userId="user-123" />
 * ```
 */
export default function AnalyticsDashboard({
    userId,
    className = '',
}: {
    userId: string;
    className?: string;
}) {
    const [timePeriod, setTimePeriod] = useState<TimePeriod>('30d');
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    /**
     * Fetch analytics data
     */
    useEffect(() => {
        async function fetchData() {
            setIsLoading(true);
            try {
                const response = await apiClient.analytics.dashboard(userId);
                setData(response.data);
            } catch (error) {
                logger.error('Failed to fetch analytics:', error);
            } finally {
                setIsLoading(false);
            }
        }

        fetchData();
    }, [timePeriod, userId]);

    if (isLoading) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!data) {
        return <div>No data available</div>;
    }

    return (
        <div className={`space-y-6 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-neutral-900">Analytics Dashboard</h1>
                    <p className="mt-1 text-sm text-neutral-500">
                        Track your job search progress and metrics
                    </p>
                </div>

                {/* Time Period Selector */}
                <div className="flex gap-2">
                    {(['7d', '30d', '90d', '1y', 'all'] as TimePeriod[]).map((period) => (
                        <button
                            key={period}
                            onClick={() => setTimePeriod(period)}
                            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${timePeriod === period
                                ? 'bg-blue-600 text-white'
                                : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
                                }`}
                        >
                            {period === 'all' ? 'All Time' : period.toUpperCase()}
                        </button>
                    ))}
                </div>
            </div>

            {/* Key Metrics */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                    title="Total Applications"
                    value={data.applications.total}
                    change="+12%"
                    changeType="positive"
                    icon={
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    }
                />
                <MetricCard
                    title="Interviews"
                    value={data.interviews.total}
                    change="+8%"
                    changeType="positive"
                    icon={
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    }
                />
                <MetricCard
                    title="Offers"
                    value={data.offers.total}
                    change="+25%"
                    changeType="positive"
                    icon={
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    }
                />
                <MetricCard
                    title="Success Rate"
                    value={`${data.interviews.successRate}%`}
                    change="-3%"
                    changeType="negative"
                    icon={
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                    }
                />
            </div>

            {/* Charts */}
            <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-neutral-900">
                        Application Trend
                    </h3>
                    <LineChartComponent
                        data={data.applications.trend}
                        dataKeys={['value']}
                        height={250}
                    />
                </div>

                {/* Weekly Activity */}
                <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-neutral-900">
                        Weekly Activity
                    </h3>
                    <BarChartComponent
                        data={data.weeklyActivity}
                        dataKeys={['applications', 'interviews']}
                        height={250}
                    />
                </div>

                {/* Status Distribution */}
                <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-neutral-900">
                        Status Distribution
                    </h3>
                    <PieChartComponent data={data.statusDistribution} height={250} />
                </div>

                {/* Industry Distribution */}
                <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-neutral-900">
                        Industry Distribution
                    </h3>
                    <AreaChartComponent
                        data={data.companyDistribution}
                        dataKeys={['value']}
                        height={250}
                    />
                </div>
            </div>

            {/* Detailed Stats */}
            <div className="grid gap-6 lg:grid-cols-3">
                {/* Applications Breakdown */}
                <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-neutral-900">
                        Applications
                    </h3>
                    <dl className="space-y-3">
                        <div className="flex justify-between">
                            <dt className="text-sm text-neutral-600">This Week</dt>
                            <dd className="text-sm font-medium text-neutral-900">
                                {data.applications.thisWeek}
                            </dd>
                        </div>
                        <div className="flex justify-between">
                            <dt className="text-sm text-neutral-600">This Month</dt>
                            <dd className="text-sm font-medium text-neutral-900">
                                {data.applications.thisMonth}
                            </dd>
                        </div>
                        <div className="flex justify-between border-t pt-3">
                            <dt className="text-sm font-semibold text-neutral-900">Total</dt>
                            <dd className="text-sm font-bold text-neutral-900">
                                {data.applications.total}
                            </dd>
                        </div>
                    </dl>
                </div>

                {/* Interviews Breakdown */}
                <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-neutral-900">
                        Interviews
                    </h3>
                    <dl className="space-y-3">
                        <div className="flex justify-between">
                            <dt className="text-sm text-neutral-600">Scheduled</dt>
                            <dd className="text-sm font-medium text-neutral-900">
                                {data.interviews.scheduled}
                            </dd>
                        </div>
                        <div className="flex justify-between">
                            <dt className="text-sm text-neutral-600">Completed</dt>
                            <dd className="text-sm font-medium text-neutral-900">
                                {data.interviews.completed}
                            </dd>
                        </div>
                        <div className="flex justify-between border-t pt-3">
                            <dt className="text-sm font-semibold text-neutral-900">Success Rate</dt>
                            <dd className="text-sm font-bold text-neutral-900">
                                {data.interviews.successRate}%
                            </dd>
                        </div>
                    </dl>
                </div>

                {/* Offers Breakdown */}
                <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-neutral-900">
                        Offers
                    </h3>
                    <dl className="space-y-3">
                        <div className="flex justify-between">
                            <dt className="text-sm text-neutral-600">Pending</dt>
                            <dd className="text-sm font-medium text-neutral-900">
                                {data.offers.pending}
                            </dd>
                        </div>
                        <div className="flex justify-between">
                            <dt className="text-sm text-neutral-600">Accepted</dt>
                            <dd className="text-sm font-medium text-green-600">
                                {data.offers.accepted}
                            </dd>
                        </div>
                        <div className="flex justify-between">
                            <dt className="text-sm text-neutral-600">Rejected</dt>
                            <dd className="text-sm font-medium text-red-600">
                                {data.offers.rejected}
                            </dd>
                        </div>
                    </dl>
                </div>
            </div>
        </div>
    );
}
