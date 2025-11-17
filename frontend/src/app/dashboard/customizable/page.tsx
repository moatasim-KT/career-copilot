/**
 * Customizable Dashboard Page
 * 
 * Drag-and-drop dashboard with 8 customizable widgets
 * Uses react-grid-layout for layout management
 */

'use client';

import { LayoutDashboard, Save, RotateCcw } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Responsive, WidgetDict, Layout as RGLLayout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

// Import widget components
import ActivityTimelineWidget from '@/components/dashboard/widgets/ActivityTimelineWidget';
import ApplicationStatsWidget from '@/components/dashboard/widgets/ApplicationStatsWidget';
import GoalsTrackerWidget from '@/components/dashboard/widgets/GoalsTrackerWidget';
import RecentJobsWidget from '@/components/dashboard/widgets/RecentJobsWidget';
import RecommendationsWidget from '@/components/dashboard/widgets/RecommendationsWidget';
import SkillsProgressWidget from '@/components/dashboard/widgets/SkillsProgressWidget';
import StatusOverviewWidget from '@/components/dashboard/widgets/StatusOverviewWidget';
import UpcomingCalendarWidget from '@/components/dashboard/widgets/UpcomingCalendarWidget';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DashboardService } from '@/lib/api/client';
import type { CustomDashboardLayout, CustomizableWidgetType } from '@/types/dashboard';
import { WIDGET_METADATA } from '@/types/dashboard';

import { useToast } from '@/components/ui/use-toast';

const ResponsiveGridLayout = Responsive;

const WIDGET_COMPONENTS: Record<string, React.ComponentType> = {
    'status-overview': StatusOverviewWidget,
    'recent-jobs': RecentJobsWidget,
    'application-stats': ApplicationStatsWidget,
    'upcoming-calendar': UpcomingCalendarWidget,
    'recommendations': RecommendationsWidget,
    'activity-timeline': ActivityTimelineWidget,
    'skills-progress': SkillsProgressWidget,
    'goals-tracker': GoalsTrackerWidget,
};

export default function CustomizableDashboardPage() {
    const [layout, setLayout] = useState<CustomDashboardLayout | null>(null);
    const [_currentBreakpoint, setCurrentBreakpoint] = useState('lg');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const { toast } = useToast();

    const loadLayout = useCallback(async () => {
        try {
            setLoading(true);
            const response = await DashboardService.getLayout();

            if (response.data) {
                setLayout(response.data);
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to load dashboard layout',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    }, [toast]);

    useEffect(() => {
        loadLayout();
    }, [loadLayout]);

    const handleLayoutChange = (newLayout: RGLLayout[], _layouts: WidgetDict) => {
        if (!layout) return;

        // Update the layout with new positions
        const updatedWidgets = layout.layout_config.widgets.map(widget => {
            const layoutItem = newLayout.find(item => item.i === widget.i);
            if (layoutItem) {
                return {
                    ...widget,
                    x: layoutItem.x,
                    y: layoutItem.y,
                    w: layoutItem.w,
                    h: layoutItem.h,
                };
            }
            return widget;
        }); setLayout({
            ...layout,
            layout_config: {
                ...layout.layout_config,
                widgets: updatedWidgets,
            },
        });
    };

    const handleSaveLayout = async () => {
        if (!layout) return;

        try {
            setSaving(true);
            const response = await DashboardService.updateLayout(layout.layout_config);

            if (response.status === 200) {
                toast({
                    title: 'Layout Saved',
                    description: 'Your dashboard layout has been saved',
                });
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to save dashboard layout',
                variant: 'destructive',
            });
        } finally {
            setSaving(false);
        }
    };

    const handleResetLayout = async () => {
        try {
            const response = await DashboardService.resetLayout();

            if (response.data) {
                setLayout(response.data);
                toast({
                    title: 'Layout Reset',
                    description: 'Dashboard layout has been reset to default',
                });
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to reset dashboard layout',
                variant: 'destructive',
            });
        }
    };

    if (loading) {
        return (
            <div className="container mx-auto py-8 px-4">
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
            </div>
        );
    }

    if (!layout) {
        return (
            <div className="container mx-auto py-8 px-4">
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <LayoutDashboard className="h-12 w-12 text-muted-foreground mb-4" />
                        <p className="text-muted-foreground mb-4">No dashboard layout found</p>
                        <Button onClick={handleResetLayout}>Create Default Layout</Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Convert widgets to react-grid-layout format
    const layouts = {
        lg: layout.layout_config.widgets.map(w => ({
            i: w.i,
            x: w.x,
            y: w.y,
            w: w.w,
            h: w.h,
            minW: w.minW,
            minH: w.minH,
        })),
    };

    return (
        <div className="container mx-auto py-8 px-4">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Customizable Dashboard</h1>
                    <p className="text-muted-foreground">
                        Drag and resize widgets to customize your dashboard
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={handleResetLayout}
                    >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        Reset
                    </Button>
                    <Button
                        onClick={handleSaveLayout}
                        disabled={saving}
                    >
                        <Save className="mr-2 h-4 w-4" />
                        {saving ? 'Saving...' : 'Save Layout'}
                    </Button>
                </div>
            </div>

            <ResponsiveGridLayout
                className="layout"
                layouts={layouts}
                breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480 }}
                cols={{ lg: layout.layout_config.columns || 12, md: 8, sm: 4, xs: 2 }}
                rowHeight={layout.layout_config.rowHeight || 100}
                onLayoutChange={handleLayoutChange}
                onBreakpointChange={setCurrentBreakpoint}
                isDraggable={true}
                isResizable={true}
                compactType="vertical"
                preventCollision={false}
            >
                {layout.layout_config.widgets
                    .filter(widget => widget.visible !== false)
                    .map(widget => {
                        const widgetType = widget.i as CustomizableWidgetType;
                        const WidgetComponent = WIDGET_COMPONENTS[widgetType];
                        const metadata = WIDGET_METADATA[widgetType];

                        return (
                            <div
                                key={widget.i}
                                className="dashboard-widget"
                            >
                                <Card className="h-full">
                                    <CardHeader className="cursor-move pb-3">
                                        <CardTitle className="text-lg">{metadata?.title || widgetType}</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        {WidgetComponent ? (
                                            <WidgetComponent />
                                        ) : (
                                            <div className="flex items-center justify-center h-full text-muted-foreground">
                                                Widget not found
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </div>
                        );
                    })}
            </ResponsiveGridLayout>      <style>
                {`
          .react-grid-layout {
            position: relative;
            transition: height 200ms ease;
          }
          
          .react-grid-item {
            transition: all 200ms ease;
            transition-property: left, top;
          }
          
          .react-grid-item.cssTransforms {
            transition-property: transform;
          }
          
          .react-grid-item.resizing {
            z-index: 100;
            will-change: width, height;
          }
          
          .react-grid-item.react-draggable-dragging {
            transition: none;
            z-index: 100;
            will-change: transform;
          }
          
          .react-grid-item.react-grid-placeholder {
            background: hsl(var(--primary) / 0.2);
            opacity: 0.2;
            transition-duration: 100ms;
            z-index: 2;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            -o-user-select: none;
            user-select: none;
            border-radius: 0.5rem;
          }
          
          .react-grid-item > .react-resizable-handle {
            position: absolute;
            width: 20px;
            height: 20px;
          }
          
          .react-grid-item > .react-resizable-handle::after {
            content: "";
            position: absolute;
            right: 3px;
            bottom: 3px;
            width: 5px;
            height: 5px;
            border-right: 2px solid hsl(var(--muted-foreground));
            border-bottom: 2px solid hsl(var(--muted-foreground));
          }
          
          .react-resizable-hide > .react-resizable-handle {
            display: none;
          }
          
          .dashboard-widget {
            height: 100%;
          }
        `}
            </style>
        </div>
    );
}