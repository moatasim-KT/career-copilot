'use client';

import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import {
    Briefcase,
    FileText,
    Calendar,
    Trophy,
    Plus,
    Upload,
    RefreshCw,
    Clock,
    CheckCircle,
    XCircle,
    Wifi,
    WifiOff,
    TrendingUp,
    AlertCircle,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';

import ActivityTimeline from '@/components/ui/ActivityTimeline';
import MetricCard from '@/components/ui/MetricCard';
import QuickActionsPanel from '@/components/ui/QuickActionsPanel';
import Widget from '@/components/ui/Widget';
import WidgetGrid from '@/components/ui/WidgetGrid';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiClient, type AnalyticsSummary, type Application } from '@/lib/api';
import { logger } from '@/lib/logger';

export default function EnhancedDashboard() {
    const router = useRouter();
    const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const handleDashboardUpdate = useCallback((data: any) => {
        if (data.analytics) {
            setAnalytics(data.analytics);
        }
        setLastUpdated(new Date());
    }, []);

    const { connectionStatus } = useWebSocket('ws://localhost:8080/api/ws', handleDashboardUpdate);

    const loadAnalytics = async () => {
        try {
            const response = await apiClient.getAnalyticsSummary();
            if (response.error) {
                setError(response.error);
            } else if (response.data) {
                setAnalytics(response.data);
            }
        } catch (err) {
            setError('Failed to load analytics');
        }
    };

    const loadDashboardData = useCallback(async () => {
        setIsLoading(true);
        try {
            await loadAnalytics();
            setLastUpdated(new Date());
        } catch {
            setError('Failed to load dashboard data');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadDashboardData();
    }, [loadDashboardData]);

    const [currentPreset, setCurrentPreset] = useState('default');
    const [layout, setLayout] = useState<any[]>([]);

    const presets = {
        default: [
            { i: 'metrics', x: 0, y: 0, w: 2, h: 2, minW: 2, minH: 2 },
            { i: 'activity', x: 2, y: 0, w: 1, h: 2, minW: 1, minH: 2 },
            { i: 'quick-actions', x: 0, y: 2, w: 1, h: 1, minW: 1, minH: 1 },
            { i: 'progress', x: 1, y: 2, w: 1, h: 1, minW: 1, minH: 1 },
        ],
        compact: [
            { i: 'metrics', x: 0, y: 0, w: 3, h: 1, minW: 2, minH: 1 },
            { i: 'activity', x: 0, y: 1, w: 2, h: 1, minW: 1, minH: 1 },
            { i: 'quick-actions', x: 2, y: 1, w: 1, h: 1, minW: 1, minH: 1 },
            { i: 'progress', x: 0, y: 2, w: 3, h: 1, minW: 1, minH: 1 },
        ],
    };

    useEffect(() => {
        setLayout(presets[currentPreset as keyof typeof presets]);
    }, [currentPreset]);

    const onLayoutChange = (newLayout: any) => {
        setLayout(newLayout);
    };

    const ResponsiveReactGridLayout = WidthProvider(Responsive);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-neutral-900">Dashboard</h1>
                    <p className="text-neutral-600 mt-1">Track your job search progress</p>
                </div>

                <div className="flex items-center space-x-3">
                    {/* Connection Status */}
                    <div className="flex items-center space-x-2">
                        {connectionStatus === 'open' ? (
                            <div className="flex items-center space-x-1 text-green-600">
                                <Wifi className="h-4 w-4" />
                                <span className="text-sm font-medium">Live</span>
                            </div>
                        ) : connectionStatus === 'connecting' ? (
                            <div className="flex items-center space-x-1 text-yellow-600">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                                <span className="text-sm font-medium">Connecting...</span>
                            </div>
                        ) : (
                            <div className="flex items-center space-x-1 text-red-600">
                                <WifiOff className="h-4 w-4" />
                                <span className="text-sm font-medium">Offline</span>
                            </div>
                        )}
                    </div>

                    {lastUpdated && (
                        <span className="text-sm text-neutral-500">
                            Updated: {lastUpdated.toLocaleTimeString()}
                        </span>
                    )}

                    <select
                        value={currentPreset}
                        onChange={(e) => setCurrentPreset(e.target.value)}
                        className="px-3 py-2 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                        <option value="default">Default Layout</option>
                        <option value="compact">Compact Layout</option>
                    </select>

                    <button
                        onClick={loadDashboardData}
                        disabled={isLoading}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                        <span>Refresh</span>
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex">
                        <AlertCircle className="h-5 w-5 text-red-400" />
                        <p className="ml-3 text-sm text-red-800">{error}</p>
                    </div>
                </div>
            )}

            {/* Main Content Grid */}
            <ResponsiveReactGridLayout
                className="layout"
                layouts={{ lg: layout }}
                breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
                cols={{ lg: 3, md: 3, sm: 2, xs: 1, xxs: 1 }}
                rowHeight={150}
                onLayoutChange={onLayoutChange}
                isDraggable={true}
                isResizable={true}
            >
                <div key="metrics">
                    <Widget title="Primary Metrics">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <MetricCard
                                title="Total Jobs"
                                value={analytics?.total_jobs || 0}
                                icon={Briefcase}
                                iconColor="text-blue-600"
                                trend={analytics?.total_jobs_trend?.trend}
                                trendValue={analytics?.total_jobs_trend?.value}
                                trendLabel="vs last month"
                                onClick={() => router.push('/jobs')}
                                loading={isLoading}
                            />

                            <MetricCard
                                title="Applications"
                                value={analytics?.total_applications || 0}
                                icon={FileText}
                                iconColor="text-green-600"
                                trend={analytics?.total_applications_trend?.trend}
                                trendValue={analytics?.total_applications_trend?.value}
                                trendLabel="vs last month"
                                onClick={() => router.push('/applications')}
                                loading={isLoading}
                            />

                            <MetricCard
                                title="Interviews"
                                value={analytics?.interviews_scheduled || 0}
                                icon={Calendar}
                                iconColor="text-purple-600"
                                trend={analytics?.interviews_scheduled_trend?.trend}
                                trendValue={analytics?.interviews_scheduled_trend?.value}
                                trendLabel="this week"
                                onClick={() => router.push('/applications?status=interview')}
                                loading={isLoading}
                            />

                            <MetricCard
                                title="Offers"
                                value={analytics?.offers_received || 0}
                                icon={Trophy}
                                iconColor="text-yellow-600"
                                trend={analytics?.offers_received_trend?.trend}
                                trendValue={analytics?.offers_received_trend?.value}
                                trendLabel="this month"
                                onClick={() => router.push('/applications?status=offer')}
                                loading={isLoading}
                            />
                        </div>
                    </Widget>
                </div>
                <div key="activity">
                    <Widget title="Recent Activity">
                        <ActivityTimeline />
                    </Widget>
                </div>
                <div key="quick-actions">
                    <Widget title="Quick Actions">
                        <QuickActionsPanel />
                    </Widget>
                </div>
                <div key="progress">
                    {analytics && analytics.total_applications > 0 && (
                        <Widget title="Application Status">
                            <div className="space-y-3">
                                {[
                                    { label: 'Applied', count: analytics.total_applications, color: 'bg-blue-500' },
                                    { label: 'Interviews', count: analytics.interviews_scheduled, color: 'bg-purple-500' },
                                    { label: 'Offers', count: analytics.offers_received, color: 'bg-green-500' },
                                ].map((item) => (
                                    <div key={item.label}>
                                        <div className="flex items-center justify-between text-sm mb-1">
                                            <span className="text-neutral-600">{item.label}</span>
                                            <span className="font-semibold text-neutral-900">{item.count}</span>
                                        </div>
                                        <div className="w-full bg-neutral-200 rounded-full h-2">
                                            <div
                                                className={`${item.color} h-2 rounded-full transition-all duration-300`}
                                                style={{
                                                    width: `${Math.min((item.count / (analytics.total_applications || 1)) * 100, 100)}%`,
                                                }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Widget>
                    )}
                </div>
            </ResponsiveReactGridLayout>
        </div>
    );
}
