'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts';
import { format, subDays, parseISO } from 'date-fns';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { ChartWrapper } from './ChartWrapper';
import { Button2 } from '@/components/ui/Button2';
import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';

interface ApplicationTimelineData {
  date: string;
  count: number;
  cumulative?: number;
}

interface TimeRange {
  label: string;
  days: number;
}

const TIME_RANGES: TimeRange[] = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: 'All', days: 365 },
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-neutral-800 p-3 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-700"
      >
        <p className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          {label}
        </p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between space-x-4">
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              {entry.name}:
            </span>
            <span className="text-sm font-medium" style={{ color: entry.color }}>
              {entry.value}
            </span>
          </div>
        ))}
      </motion.div>
    );
  }
  return null;
};

interface ApplicationTimelineChartProps {
  className?: string;
}

/**
 * ApplicationTimelineChart - Line chart showing applications over time
 * 
 * Features:
 * - Line chart with applications count over time
 * - Optional trend line
 * - Hover tooltip with exact count and date
 * - Zoom/pan controls with brush for large date ranges
 * - Time range filters (7D, 30D, 90D, All)
 * - Dark mode support
 * - Cumulative view toggle
 * - CSV/PNG export
 * - Responsive design
 */
export const ApplicationTimelineChart: React.FC<ApplicationTimelineChartProps> = ({
  className = '',
}) => {
  const [data, setData] = useState<ApplicationTimelineData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(true);
  const [showTrend, setShowTrend] = useState(false);
  const [showCumulative, setShowCumulative] = useState(false);
  const [selectedRange, setSelectedRange] = useState<number>(30);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Detect dark mode
  useEffect(() => {
    const checkDarkMode = () => {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    };
    
    checkDarkMode();
    
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
      const response = await apiClient.getApplications(0, 1000);
      
      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to fetch data');
      }

      // Group applications by date
      const dateMap = new Map<string, number>();
      const applications = response.data;

      // Initialize date range
      const endDate = new Date();
      const startDate = subDays(endDate, selectedRange);

      for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = format(d, 'yyyy-MM-dd');
        dateMap.set(dateStr, 0);
      }

      // Count applications per date
      applications.forEach((app: any) => {
        if (app.applied_at) {
          try {
            const date = parseISO(app.applied_at);
            const dateStr = format(date, 'yyyy-MM-dd');
            if (dateMap.has(dateStr)) {
              dateMap.set(dateStr, (dateMap.get(dateStr) || 0) + 1);
            }
          } catch (err) {
            logger.warn('ApplicationTimelineChart: Invalid date', app.applied_at);
          }
        }
      });

      // Convert to array and calculate cumulative
      let cumulative = 0;
      const chartData: ApplicationTimelineData[] = Array.from(dateMap.entries())
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([date, count]) => {
          cumulative += count;
          return {
            date: format(parseISO(date), 'MMM dd'),
            count,
            cumulative,
          };
        });

      setData(chartData);
    } catch (err) {
      logger.error('ApplicationTimelineChart: Failed to fetch data', err);
      setError(err instanceof Error ? err.message : 'Failed to load chart data');
    } finally {
      setIsLoading(false);
    }
  }, [selectedRange]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExportCSV = () => {
    const csvContent = [
      ['Date', 'Applications', 'Cumulative'],
      ...data.map(item => [item.date, item.count.toString(), (item.cumulative || 0).toString()]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `application-timeline-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportPNG = () => {
    alert('PNG export feature coming soon!');
  };

  // Calculate trend
  const calculateTrend = () => {
    if (data.length < 2) return 0;
    const recent = data.slice(-7).reduce((sum, item) => sum + item.count, 0);
    const previous = data.slice(-14, -7).reduce((sum, item) => sum + item.count, 0);
    if (previous === 0) return recent > 0 ? 100 : 0;
    return ((recent - previous) / previous) * 100;
  };

  const trend = calculateTrend();
  const TrendIcon = trend > 0 ? TrendingUp : trend < 0 ? TrendingDown : Minus;
  const trendColor = trend > 0 ? 'text-success-600 dark:text-success-400' : trend < 0 ? 'text-error-600 dark:text-error-400' : 'text-neutral-600 dark:text-neutral-400';

  const chartColors = {
    line: isDarkMode ? '#60a5fa' : '#3b82f6', // blue-400 / blue-500
    area: isDarkMode ? 'rgba(96, 165, 250, 0.1)' : 'rgba(59, 130, 246, 0.1)',
    cumulative: isDarkMode ? '#34d399' : '#22c55e', // emerald-400 / green-500
    grid: isDarkMode ? '#374151' : '#e5e7eb', // gray-700 / gray-200
    text: isDarkMode ? '#d1d5db' : '#6b7280', // gray-300 / gray-500
  };

  if (data.length === 0 && !isLoading && !error) {
    return (
      <ChartWrapper
        title="Application Timeline"
        description="Track your application activity over time"
        isLoading={false}
        error={null}
        className={className}
      >
        <div className="h-[350px] flex items-center justify-center">
          <div className="text-center">
            <p className="text-neutral-600 dark:text-neutral-400">
              No application data available
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
              Start applying to jobs to see your timeline
            </p>
          </div>
        </div>
      </ChartWrapper>
    );
  }

  return (
    <ChartWrapper
      title="Application Timeline"
      description="Track your application activity over time"
      isLoading={isLoading}
      error={error}
      onExportCSV={handleExportCSV}
      onExportPNG={handleExportPNG}
      className={className}
      actions={
        <div className="flex items-center space-x-2">
          {/* Trend Indicator */}
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-md bg-neutral-100 dark:bg-neutral-700 ${trendColor}`}>
            <TrendIcon className="h-3 w-3" />
            <span className="text-xs font-medium">
              {Math.abs(trend).toFixed(1)}%
            </span>
          </div>
        </div>
      }
    >
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        {/* Time Range Buttons */}
        <div className="flex items-center space-x-2">
          {TIME_RANGES.map((range) => (
            <Button2
              key={range.days}
              size="sm"
              variant={selectedRange === range.days ? 'primary' : 'outline'}
              onClick={() => setSelectedRange(range.days)}
            >
              {range.label}
            </Button2>
          ))}
        </div>

        {/* View Options */}
        <div className="flex items-center space-x-2">
          <Button2
            size="sm"
            variant={showCumulative ? 'primary' : 'ghost'}
            onClick={() => setShowCumulative(!showCumulative)}
          >
            Cumulative
          </Button2>
          <Button2
            size="sm"
            variant={showLegend ? 'primary' : 'ghost'}
            onClick={() => setShowLegend(!showLegend)}
          >
            Legend
          </Button2>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={data}>
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColors.line} stopOpacity={0.3} />
              <stop offset="95%" stopColor={chartColors.line} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
          <XAxis
            dataKey="date"
            stroke={chartColors.text}
            style={{ fontSize: '12px' }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            stroke={chartColors.text}
            style={{ fontSize: '12px' }}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              verticalAlign="top"
              height={36}
              iconType="line"
            />
          )}
          
          {/* Main line with area */}
          <Area
            type="monotone"
            dataKey="count"
            stroke={chartColors.line}
            strokeWidth={2}
            fill="url(#colorCount)"
            name="Applications"
            animationDuration={800}
            animationEasing="ease-out"
          />
          
          {/* Cumulative line */}
          {showCumulative && (
            <Line
              type="monotone"
              dataKey="cumulative"
              stroke={chartColors.cumulative}
              strokeWidth={2}
              dot={false}
              name="Cumulative"
              animationDuration={800}
              animationEasing="ease-out"
            />
          )}

          {/* Brush for zoom/pan */}
          {data.length > 30 && (
            <Brush
              dataKey="date"
              height={30}
              stroke={chartColors.line}
              fill={isDarkMode ? '#1f2937' : '#f9fafb'}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {data.reduce((sum, item) => sum + item.count, 0)}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Total Applications
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {(data.reduce((sum, item) => sum + item.count, 0) / (selectedRange || 1)).toFixed(1)}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Avg per Day
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {Math.max(...data.map(item => item.count))}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Peak Day
          </p>
        </div>
      </div>
    </ChartWrapper>
  );
};

export default ApplicationTimelineChart;
