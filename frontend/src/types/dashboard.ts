/**
 * Dashboard widget types and interfaces
 */

export type WidgetType =
  | 'metrics'
  | 'daily-goal'
  | 'recent-activity'
  | 'status-breakdown'
  | 'application-status-chart'
  | 'application-timeline-chart'
  | 'salary-distribution-chart'
  | 'skills-demand-chart'
  | 'success-rate-chart'
  | 'status-overview'
  | 'recent-jobs'
  | 'application-stats'
  | 'upcoming-calendar'
  | 'recommendations'
  | 'activity-timeline'
  | 'skills-progress'
  | 'goals-tracker';

export interface DashboardWidget {
  id: string;
  type: WidgetType;
  position: number;
  visible: boolean;
  title: string;
  gridSpan?: {
    cols: number; // Number of columns to span (1-2)
    rows?: number; // Optional row span
  };
}

export interface DashboardLayout {
  widgets: DashboardWidget[];
  lastUpdated: Date;
}

// ============================================================================
// Customizable Dashboard Layout Types (Phase 3.2)
// ============================================================================

export interface CustomDashboardWidget {
  i: string; // Unique widget ID
  x: number; // Grid x position
  y: number; // Grid y position
  w: number; // Width in grid units
  h: number; // Height in grid units
  minW?: number; // Minimum width
  minH?: number; // Minimum height
  maxW?: number; // Maximum width
  maxH?: number; // Maximum height
  static?: boolean; // Whether widget is draggable
  visible?: boolean; // Whether widget is visible
}

export interface DashboardBreakpoints {
  lg: number;
  md: number;
  sm: number;
  xs: number;
}

export interface DashboardCols {
  lg: number;
  md: number;
  sm: number;
  xs: number;
}

export interface CustomDashboardLayoutConfig {
  widgets: CustomDashboardWidget[];
  columns?: number;
  rowHeight?: number;
  breakpoints?: DashboardBreakpoints;
  cols?: DashboardCols;
}

export interface CustomDashboardLayout {
  id: number;
  user_id: number;
  layout_config: CustomDashboardLayoutConfig;
  created_at: string;
  updated_at: string;
}

export type CustomizableWidgetType =
  | 'status-overview'
  | 'recent-jobs'
  | 'application-stats'
  | 'upcoming-calendar'
  | 'recommendations'
  | 'activity-timeline'
  | 'skills-progress'
  | 'goals-tracker';

export interface WidgetMetadata {
  id: CustomizableWidgetType;
  title: string;
  description: string;
  defaultSize: { w: number; h: number };
  minSize: { w: number; h: number };
  icon?: string;
}

// Default widget configurations for customizable dashboard
export const WIDGET_METADATA: Record<CustomizableWidgetType, WidgetMetadata> = {
  'status-overview': {
    id: 'status-overview',
    title: 'Application Status Overview',
    description: 'Visual breakdown of application statuses',
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, h: 3 },
  },
  'recent-jobs': {
    id: 'recent-jobs',
    title: 'Recent Job Listings',
    description: 'Latest job opportunities',
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, h: 3 },
  },
  'application-stats': {
    id: 'application-stats',
    title: 'Application Statistics',
    description: 'Key metrics and trends',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, h: 2 },
  },
  'upcoming-calendar': {
    id: 'upcoming-calendar',
    title: 'Upcoming Interviews',
    description: 'Calendar events and interviews',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, h: 2 },
  },
  'recommendations': {
    id: 'recommendations',
    title: 'Job Recommendations',
    description: 'AI-powered job matches',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, h: 2 },
  },
  'activity-timeline': {
    id: 'activity-timeline',
    title: 'Recent Activity',
    description: 'Timeline of recent actions',
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, h: 3 },
  },
  'skills-progress': {
    id: 'skills-progress',
    title: 'Skills Progress',
    description: 'Track skill development',
    defaultSize: { w: 6, h: 3 },
    minSize: { w: 4, h: 2 },
  },
  'goals-tracker': {
    id: 'goals-tracker',
    title: 'Goals & Milestones',
    description: 'Track career goals',
    defaultSize: { w: 6, h: 3 },
    minSize: { w: 4, h: 2 },
  },
};

export const DEFAULT_DASHBOARD_WIDGETS: DashboardWidget[] = [
  {
    id: 'metrics',
    type: 'metrics',
    position: 0,
    visible: true,
    title: 'Key Metrics',
    gridSpan: { cols: 2 }, // Full width
  },
  {
    id: 'application-status-chart',
    type: 'application-status-chart',
    position: 1,
    visible: true,
    title: 'Application Status',
    gridSpan: { cols: 1 },
  },
  {
    id: 'application-timeline-chart',
    type: 'application-timeline-chart',
    position: 2,
    visible: true,
    title: 'Application Timeline',
    gridSpan: { cols: 1 },
  },
  {
    id: 'salary-distribution-chart',
    type: 'salary-distribution-chart',
    position: 3,
    visible: true,
    title: 'Salary Distribution',
    gridSpan: { cols: 1 },
  },
  {
    id: 'skills-demand-chart',
    type: 'skills-demand-chart',
    position: 4,
    visible: true,
    title: 'Skills Demand',
    gridSpan: { cols: 1 },
  },
  {
    id: 'success-rate-chart',
    type: 'success-rate-chart',
    position: 5,
    visible: true,
    title: 'Success Rate',
    gridSpan: { cols: 2 }, // Full width
  },
  {
    id: 'daily-goal',
    type: 'daily-goal',
    position: 6,
    visible: true,
    title: 'Daily Application Goal',
    gridSpan: { cols: 2 }, // Full width
  },
  {
    id: 'recent-activity',
    type: 'recent-activity',
    position: 7,
    visible: true,
    title: 'Recent Activity',
    gridSpan: { cols: 2 }, // Full width
  },
  {
    id: 'status-breakdown',
    type: 'status-breakdown',
    position: 8,
    visible: true,
    title: 'Status Breakdown',
    gridSpan: { cols: 2 }, // Full width
  },
];
