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
  | 'success-rate-chart';

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
