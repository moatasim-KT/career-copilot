/**
 * LazyCharts
 * 
 * Lazy-loaded wrappers for individual chart components using Recharts.
 * Each chart type is code-split separately for optimal loading.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

import { ChartSkeleton, PieChartSkeleton, LineChartSkeleton } from '@/components/loading/ChartSkeleton';

// Lazy load individual chart types
export const LazyPieChart = dynamic(
  () => import('recharts').then((mod) => ({ default: mod.PieChart })),
  {
    loading: () => <PieChartSkeleton />,
    ssr: false,
  }
);

export const LazyBarChart = dynamic(
  () => import('recharts').then((mod) => ({ default: mod.BarChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

export const LazyLineChart = dynamic(
  () => import('recharts').then((mod) => ({ default: mod.LineChart })),
  {
    loading: () => <LineChartSkeleton />,
    ssr: false,
  }
);

export const LazyComposedChart = dynamic(
  () => import('recharts').then((mod) => ({ default: mod.ComposedChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

export const LazyAreaChart = dynamic(
  () => import('recharts').then((mod) => ({ default: mod.AreaChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

export const LazyRadarChart = dynamic(
  () => import('recharts').then((mod) => ({ default: mod.RadarChart })),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);

// Export chart components that are commonly used together
export const LazyChartComponents = {
  ResponsiveContainer: dynamic(() => import('recharts').then((mod) => ({ default: mod.ResponsiveContainer })), { ssr: false }),
  CartesianGrid: dynamic(() => import('recharts').then((mod) => ({ default: mod.CartesianGrid })), { ssr: false }),
  XAxis: dynamic(() => import('recharts').then((mod) => ({ default: mod.XAxis })), { ssr: false }),
  YAxis: dynamic(() => import('recharts').then((mod) => ({ default: mod.YAxis })), { ssr: false }),
  Tooltip: dynamic(() => import('recharts').then((mod) => ({ default: mod.Tooltip })), { ssr: false }),
  Legend: dynamic(() => import('recharts').then((mod) => ({ default: mod.Legend })), { ssr: false }),
  Bar: dynamic(() => import('recharts').then((mod) => ({ default: mod.Bar })), { ssr: false }),
  Line: dynamic(() => import('recharts').then((mod) => ({ default: mod.Line })), { ssr: false }),
  Area: dynamic(() => import('recharts').then((mod) => ({ default: mod.Area })), { ssr: false }),
  Pie: dynamic(() => import('recharts').then((mod) => ({ default: mod.Pie })), { ssr: false }),
  Cell: dynamic(() => import('recharts').then((mod) => ({ default: mod.Cell })), { ssr: false }),
};

/**
 * Wrapper component for any chart with Suspense
 */
interface ChartWrapperProps {
  children: React.ReactNode;
  type?: 'bar' | 'line' | 'pie' | 'composed' | 'area' | 'radar';
}

export function ChartWrapper({ children, type = 'bar' }: ChartWrapperProps) {
  const SkeletonComponent = type === 'pie' ? PieChartSkeleton : type === 'line' ? LineChartSkeleton : ChartSkeleton;
  
  return (
    <Suspense fallback={<SkeletonComponent />}>
      {children}
    </Suspense>
  );
}
