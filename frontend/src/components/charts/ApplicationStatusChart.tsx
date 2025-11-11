'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, Sector } from 'recharts';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ChartWrapper } from './ChartWrapper';
import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';

interface ApplicationStatusData {
  name: string;
  value: number;
  color: string;
  percentage?: number;
}

// Status colors matching the design system
const STATUS_COLORS: Record<string, string> = {
  Applied: '#3b82f6', // blue-500
  Interviewing: '#8b5cf6', // purple-500
  Offer: '#22c55e', // green-500
  Rejected: '#ef4444', // red-500
  Accepted: '#10b981', // emerald-500
  Withdrawn: '#6b7280', // gray-500
};

// Dark mode colors
const STATUS_COLORS_DARK: Record<string, string> = {
  Applied: '#60a5fa', // blue-400
  Interviewing: '#a78bfa', // purple-400
  Offer: '#4ade80', // green-400
  Rejected: '#f87171', // red-400
  Accepted: '#34d399', // emerald-400
  Withdrawn: '#9ca3af', // gray-400
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-neutral-800 p-3 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-700"
      >
        <p className="font-semibold text-neutral-900 dark:text-neutral-100">
          {data.name}
        </p>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Count: <span className="font-medium">{data.value}</span>
        </p>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Percentage: <span className="font-medium">{data.percentage}%</span>
        </p>
      </motion.div>
    );
  }
  return null;
};

interface ActiveShapeProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  startAngle: number;
  endAngle: number;
  fill: string;
  payload: ApplicationStatusData;
  percent: number;
  value: number;
}

const renderActiveShape = (props: ActiveShapeProps) => {
  const RADIAN = Math.PI / 180;
  const {
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    payload,
    percent,
    value,
  } = props;
  const sin = Math.sin(-RADIAN * midAngle);
  const cos = Math.cos(-RADIAN * midAngle);
  const sx = cx + (outerRadius + 10) * cos;
  const sy = cy + (outerRadius + 10) * sin;
  const mx = cx + (outerRadius + 30) * cos;
  const my = cy + (outerRadius + 30) * sin;
  const ex = mx + (cos >= 0 ? 1 : -1) * 22;
  const ey = my;
  const textAnchor = cos >= 0 ? 'start' : 'end';

  return (
    <g>
      <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill} className="font-semibold">
        {payload.name}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
      <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
      <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
      <text
        x={ex + (cos >= 0 ? 1 : -1) * 12}
        y={ey}
        textAnchor={textAnchor}
        fill="#333"
        className="text-sm font-medium dark:fill-neutral-300"
      >
        {`${value} (${(percent * 100).toFixed(1)}%)`}
      </text>
    </g>
  );
};

interface ApplicationStatusChartProps {
  onStatusClick?: (status: string) => void;
  className?: string;
}

/**
 * ApplicationStatusChart - Interactive pie/donut chart showing application status distribution
 * 
 * Features:
 * - Interactive tooltips with counts and percentages
 * - Click slice to filter applications by status
 * - Smooth animations on load and data changes
 * - Dark mode support
 * - Active slice highlighting
 * - CSV/PNG export
 * - Responsive design
 */
export const ApplicationStatusChart: React.FC<ApplicationStatusChartProps> = ({
  onStatusClick,
  className = '',
}) => {
  const router = useRouter();
  const [data, setData] = useState<ApplicationStatusData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState<number | undefined>(undefined);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Detect dark mode
  useEffect(() => {
    const checkDarkMode = () => {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    };
    
    checkDarkMode();
    
    // Watch for theme changes
    const observer = new MutationObserver(checkDarkMode);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });
    
    return () => observer.disconnect();
  }, []);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.getAnalyticsSummary();
      
      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to fetch data');
      }

      const statusBreakdown = response.data.application_status_breakdown || {};
      const total = Object.values(statusBreakdown).reduce((sum: number, count) => sum + (count as number), 0);

      const chartData: ApplicationStatusData[] = Object.entries(statusBreakdown)
        .map(([status, count]) => ({
          name: status.charAt(0).toUpperCase() + status.slice(1),
          value: count as number,
          color: isDarkMode 
            ? STATUS_COLORS_DARK[status.charAt(0).toUpperCase() + status.slice(1)] || '#9ca3af'
            : STATUS_COLORS[status.charAt(0).toUpperCase() + status.slice(1)] || '#6b7280',
          percentage: total > 0 ? Number(((count as number / total) * 100).toFixed(1)) : 0,
        }))
        .filter(item => item.value > 0)
        .sort((a, b) => b.value - a.value);

      setData(chartData);
    } catch (err) {
      logger.error('ApplicationStatusChart: Failed to fetch data', err);
      setError(err instanceof Error ? err.message : 'Failed to load chart data');
    } finally {
      setIsLoading(false);
    }
  }, [isDarkMode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handlePieClick = (data: ApplicationStatusData, index: number) => {
    logger.info('ApplicationStatusChart: Slice clicked', { status: data.name });
    
    if (onStatusClick) {
      onStatusClick(data.name.toLowerCase());
    } else {
      // Navigate to applications page with status filter
      router.push(`/applications?status=${data.name.toLowerCase()}`);
    }
  };

  const handleExportCSV = () => {
    const csvContent = [
      ['Status', 'Count', 'Percentage'],
      ...data.map(item => [item.name, item.value.toString(), `${item.percentage}%`]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `application-status-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportPNG = () => {
    // This would require html2canvas or similar library
    // For now, we'll show a message
    alert('PNG export feature coming soon!');
  };

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  const onPieLeave = () => {
    setActiveIndex(undefined);
  };

  if (data.length === 0 && !isLoading && !error) {
    return (
      <ChartWrapper
        title="Application Status Distribution"
        description="Breakdown of your applications by status"
        isLoading={false}
        error={null}
        className={className}
      >
        <div className="h-[300px] flex items-center justify-center">
          <div className="text-center">
            <p className="text-neutral-600 dark:text-neutral-400">
              No application data available
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
              Start applying to jobs to see your status distribution
            </p>
          </div>
        </div>
      </ChartWrapper>
    );
  }

  return (
    <ChartWrapper
      title="Application Status Distribution"
      description="Breakdown of your applications by status"
      isLoading={isLoading}
      error={error}
      onExportCSV={handleExportCSV}
      onExportPNG={handleExportPNG}
      className={className}
    >
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            activeIndex={activeIndex}
            activeShape={renderActiveShape}
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            onClick={handlePieClick}
            onMouseEnter={onPieEnter}
            onMouseLeave={onPieLeave}
            animationBegin={0}
            animationDuration={800}
            animationEasing="ease-out"
            style={{ cursor: 'pointer' }}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color}
                className="transition-opacity hover:opacity-80"
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
            formatter={(value, entry: any) => (
              <span className="text-sm text-neutral-700 dark:text-neutral-300">
                {value} ({entry.payload.value})
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend with click hint */}
      <div className="mt-4 text-center">
        <p className="text-xs text-neutral-500 dark:text-neutral-400">
          Click on a slice to filter applications by status
        </p>
      </div>
    </ChartWrapper>
  );
};

export default ApplicationStatusChart;
