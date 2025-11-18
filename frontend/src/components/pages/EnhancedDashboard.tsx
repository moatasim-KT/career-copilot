/**
 * Enhanced Dashboard Component
 * 
 * Main dashboard page with customizable widget layout and real-time updates.
 * 
 * **Features**:
 * - Drag-and-drop widget rearrangement via react-grid-layout
 * - Real-time WebSocket updates for analytics and application status
 * - Multiple layout presets (default, compact)
 * - Connection status indicator
 * - Auto-refresh on data updates
 * - Loading states and error handling
 * 
 * **Widgets**:
 * 1. Metrics Overview - Application statistics (total, success rate, response time)
 * 2. Activity Timeline - Recent application activity with icons
 * 3. Quick Actions Panel - Common actions (New Application, Search Jobs, etc.)
 * 4. Progress Tracker - Goals and milestones
 * 
 * **Layout System**:
 * Uses react-grid-layout with responsive breakpoints:
 * - Desktop (lg): 3 columns
 * - Tablet (md): 2 columns
 * - Mobile (sm): 1 column
 * 
 * Grid coordinates: `{ i: 'id', x: col, y: row, w: width, h: height }`
 * 
 * **WebSocket Integration**:
 * Connects to backend at `ws://localhost:8002/ws` for:
 * - Analytics updates (`analytics` property)
 * - Application status changes
 * - Real-time notifications
 * 
 * **State Management**:
 * - `analytics`: AnalyticsSummary from backend
 * - `layout`: Current widget layout configuration
 * - `connectionStatus`: WebSocket connection state (open/connecting/closed)
 * - `lastUpdated`: Timestamp of last data refresh
 * 
 * **Usage**:
 * ```tsx
 * import EnhancedDashboard from '@/components/pages/EnhancedDashboard';
 * 
 * export default function DashboardPage() {
 *   return <EnhancedDashboard />;
 * }
 * ```
 * 
 * **Design Tokens**:
 * Uses design system from [[frontend/src/app/globals.css|globals.css]]:
 * - Colors: neutral-*, green-*, yellow-*, red-* for status
 * - Typography: text-3xl, font-bold for headers
 * - Spacing: space-y-6, space-x-3
 * 
 * **Related Components**:
 * - [[frontend/src/components/ui/MetricCard.tsx|MetricCard]] - Displays individual metrics
 * - [[frontend/src/components/ui/ActivityTimeline.tsx|ActivityTimeline]] - Shows recent activity
 * - [[frontend/src/components/ui/QuickActionsPanel.tsx|QuickActionsPanel]] - Action buttons
 * - [[frontend/src/components/ui/Widget.tsx|Widget]] - Generic widget wrapper
 * 
 * **API Integration**:
 * - `apiClient.getAnalyticsSummary()` - Fetches dashboard analytics
 * - WebSocket updates trigger state refresh
 * 
 * @see [[docs/features/DASHBOARD_CUSTOMIZATION_GUIDE|Dashboard Customization Guide]]
 * @see [[docs/DEVELOPER_GUIDE|Developer Guide]] - Component patterns
 */
'use client';

import {
    Briefcase,
    FileText,
    Calendar,
    Trophy,
    RefreshCw,
    Wifi,
    WifiOff,
    AlertCircle,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState, useEffect, useCallback, useMemo } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import ActivityTimeline from '@/components/ui/ActivityTimeline';
import MetricCard from '@/components/ui/MetricCard';
import QuickActionsPanel from '@/components/ui/QuickActionsPanel';
import Widget from '@/components/ui/Widget';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiClient, type AnalyticsSummary } from '@/lib/api';
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

    // point the dashboard websocket to the local backend started on port 8002
    const { connectionStatus } = useWebSocket(
        'ws://localhost:8002/ws',
        handleDashboardUpdate,
        () => { }, // onApplicationStatusUpdate - not needed for dashboard
        () => { },  // onAnalyticsUpdate - not needed for dashboard
    );

    const loadAnalytics = useCallback(async () => {
        try {
            const response = await apiClient.getAnalyticsSummary();
            if (response.error) {
                setError(response.error);
            } else if (response.data) {
                setAnalytics(response.data);
            }
        } catch (err) {
            // keep user-facing message but record the error for debugging
            setError('Failed to load analytics');
            logger.error('EnhancedDashboard: failed to load analytics', err);
        }
    }, []);

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
    }, [loadAnalytics]);

    useEffect(() => {
        loadDashboardData();
    }, [loadDashboardData]);

    const [currentPreset, setCurrentPreset] = useState('default');
    const [layout, setLayout] = useState<any[]>([]);

    const presets = useMemo(() => ({
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
    }), []);

    useEffect(() => {
        setLayout(presets[currentPreset as keyof typeof presets]);
    }, [currentPreset, presets]);

    const onLayoutChange = (newLayout: any) => {
        try {
            const prev = JSON.stringify(layout || []);
            const next = JSON.stringify(newLayout || []);
            if (prev !== next) {
                setLayout(newLayout);
            }
        } catch {
            // fallback: set layout if comparison fails
            setLayout(newLayout);
        }
    };

    const ResponsiveReactGridLayout = WidthProvider(Responsive);

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">Dashboard</h1>
                    <p className="text-neutral-500 dark:text-neutral-400 mt-1">Track your job search progress and insights</p>
                </div>

                <div className="flex items-center gap-3 bg-white dark:bg-neutral-900 p-2 rounded-xl border border-neutral-200 dark:border-neutral-800 shadow-sm">
                    {/* Connection Status */}
                    <div className="flex items-center px-3 py-1.5 rounded-lg bg-neutral-50 dark:bg-neutral-800">
                        {connectionStatus === 'open' ? (
                            <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                                <div className="relative flex h-2.5 w-2.5">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                                </div>
                                <span className="text-xs font-medium">Live</span>
                            </div>
                        ) : connectionStatus === 'connecting' ? (
                            <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                                <span className="text-xs font-medium">Connecting</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                                <WifiOff className="h-3 w-3" />
                                <span className="text-xs font-medium">Offline</span>
                            </div>
                        )}
                    </div>

                    <div className="h-6 w-px bg-neutral-200 dark:bg-neutral-700 mx-1"></div>

                    <select
                        value={currentPreset}
                        onChange={(e) => setCurrentPreset(e.target.value)}
                        className="text-sm border-none bg-transparent focus:ring-0 text-neutral-600 dark:text-neutral-300 font-medium cursor-pointer hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
                    >
                        <option value="default">Default View</option>
                        <option value="compact">Compact View</option>
                    </select>

                    <button
                        onClick={loadDashboardData}
                        disabled={isLoading}
                        className="p-2 text-neutral-500 hover:text-primary-600 dark:text-neutral-400 dark:hover:text-primary-400 transition-colors rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800"
                        title="Refresh Data"
                    >
                        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-center gap-3">
                    <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                    <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
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
