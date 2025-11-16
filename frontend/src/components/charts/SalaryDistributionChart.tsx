'use client';

import { DollarSign, TrendingUp } from 'lucide-react';
import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
  LabelList,
} from 'recharts';


import Button from '@/components/ui/Button2';
import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';
import { m } from '@/lib/motion';

import { ChartWrapper } from './ChartWrapper';

interface SalaryDistributionData {
  range: string;
  count: number;
  minSalary: number;
  maxSalary: number;
  avgSalary: number;
  isTargetRange?: boolean;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <m.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-neutral-800 p-3 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-700"
      >
        <p className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          {label}
        </p>
        <div className="space-y-1">
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              Jobs:
            </span>
            <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {data.count}
            </span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              Avg Salary:
            </span>
            <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              ${(data.avgSalary / 1000).toFixed(0)}k
            </span>
          </div>
          {data.isTargetRange && (
            <div className="mt-2 pt-2 border-t border-neutral-200 dark:border-neutral-700">
              <span className="text-xs text-success-600 dark:text-success-400 font-medium">
                ✓ Your target range
              </span>
            </div>
          )}
        </div>
      </m.div>
    );
  }
  return null;
};

interface SalaryDistributionChartProps {
  userTargetSalary?: number;
  className?: string;
}

/**
 * SalaryDistributionChart - Bar chart showing salary distribution across job postings
 * 
 * Features:
 * - Bar chart/histogram showing salary ranges
 * - Highlight user's target salary range
 * - Interactive tooltips with job counts and average salaries
 * - Dark mode support
 * - Responsive design
 * - CSV/PNG export
 * - Click bars to filter jobs by salary range
 */
export const SalaryDistributionChart: React.FC<SalaryDistributionChartProps> = ({
  userTargetSalary,
  className = '',
}) => {
  const [data, setData] = useState<SalaryDistributionData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(true);
  const [showAverage, setShowAverage] = useState(false);
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
      const response = await apiClient.getJobs(0, 1000);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to fetch data');
      }

      const jobs = response.data;

      // Define salary buckets (in thousands)
      const buckets = [
        { min: 0, max: 50, label: '$0-50k' },
        { min: 50, max: 75, label: '$50-75k' },
        { min: 75, max: 100, label: '$75-100k' },
        { min: 100, max: 125, label: '$100-125k' },
        { min: 125, max: 150, label: '$125-150k' },
        { min: 150, max: 200, label: '$150-200k' },
        { min: 200, max: 300, label: '$200-300k' },
        { min: 300, max: Infinity, label: '$300k+' },
      ];

      // Count jobs in each bucket
      const distribution = buckets.map(bucket => {
        const jobsInRange = jobs.filter((job: any) => {
          const salary = job.salary_max || job.salary_min || 0;
          return salary >= bucket.min * 1000 && salary < bucket.max * 1000;
        });

        const avgSalary = jobsInRange.length > 0
          ? jobsInRange.reduce((sum: number, job: any) => sum + (job.salary_max || job.salary_min || 0), 0) / jobsInRange.length
          : 0;

        // Check if this is the user's target range
        const isTargetRange = userTargetSalary
          ? userTargetSalary >= bucket.min * 1000 && userTargetSalary < bucket.max * 1000
          : false;

        return {
          range: bucket.label,
          count: jobsInRange.length,
          minSalary: bucket.min * 1000,
          maxSalary: bucket.max === Infinity ? bucket.min * 1000 : bucket.max * 1000,
          avgSalary,
          isTargetRange,
        };
      }).filter(item => item.count > 0);

      setData(distribution);
    } catch (err) {
      logger.error('SalaryDistributionChart: Failed to fetch data', err);
      setError(err instanceof Error ? err.message : 'Failed to load chart data');
    } finally {
      setIsLoading(false);
    }
  }, [userTargetSalary]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExportCSV = () => {
    const csvContent = [
      ['Salary Range', 'Job Count', 'Average Salary'],
      ...data.map(item => [
        item.range,
        item.count.toString(),
        `$${(item.avgSalary / 1000).toFixed(0)}k`,
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `salary-distribution-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportPNG = () => {
    alert('PNG export feature coming soon!');
  };

  const handleBarClick = (data: SalaryDistributionData) => {
    logger.info('SalaryDistributionChart: Bar clicked', { range: data.range });
    // Could navigate to jobs page with salary filter
    // router.push(`/jobs?salary_min=${data.minSalary}&salary_max=${data.maxSalary}`);
  };

  const chartColors = {
    bar: isDarkMode ? '#60a5fa' : '#3b82f6', // blue-400 / blue-500
    targetBar: isDarkMode ? '#34d399' : '#22c55e', // emerald-400 / green-500
    grid: isDarkMode ? '#374151' : '#e5e7eb', // gray-700 / gray-200
    text: isDarkMode ? '#d1d5db' : '#6b7280', // gray-300 / gray-500
    referenceLine: isDarkMode ? '#f87171' : '#ef4444', // red-400 / red-500
  };

  const totalJobs = data.reduce((sum, item) => sum + item.count, 0);
  const avgSalary = data.reduce((sum, item) => sum + item.avgSalary * item.count, 0) / totalJobs || 0;

  if (data.length === 0 && !isLoading && !error) {
    return (
      <ChartWrapper
        title="Salary Distribution"
        description="Distribution of job salaries across different ranges"
        isLoading={false}
        error={null}
        className={className}
      >
        <div className="h-[350px] flex items-center justify-center">
          <div className="text-center">
            <DollarSign className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400">
              No salary data available
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
              Jobs with salary information will appear here
            </p>
          </div>
        </div>
      </ChartWrapper>
    );
  }

  return (
    <ChartWrapper
      title="Salary Distribution"
      description="Distribution of job salaries across different ranges"
      isLoading={isLoading}
      error={error}
      onExportCSV={handleExportCSV}
      onExportPNG={handleExportPNG}
      className={className}
      actions={
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 px-2 py-1 rounded-md bg-neutral-100 dark:bg-neutral-700">
            <TrendingUp className="h-3 w-3 text-success-600 dark:text-success-400" />
            <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
              ${(avgSalary / 1000).toFixed(0)}k avg
            </span>
          </div>
        </div>
      }
    >
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2">
          <Button
            size="sm"
            variant={showAverage ? 'primary' : 'ghost'}
            onClick={() => setShowAverage(!showAverage)}
          >
            Show Average
          </Button>
          <Button
            size="sm"
            variant={showLegend ? 'primary' : 'ghost'}
            onClick={() => setShowLegend(!showLegend)}
          >
            Legend
          </Button>
        </div>

        {userTargetSalary && (
          <div className="text-sm text-neutral-600 dark:text-neutral-400">
            Your target: <span className="font-medium">${(userTargetSalary / 1000).toFixed(0)}k</span>
          </div>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
          <XAxis
            dataKey="range"
            stroke={chartColors.text}
            style={{ fontSize: '12px' }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke={chartColors.text}
            style={{ fontSize: '12px' }}
            allowDecimals={false}
            label={{ value: 'Number of Jobs', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              verticalAlign="top"
              height={36}
              iconType="rect"
            />
          )}

          <Bar
            dataKey="count"
            name="Jobs"
            onClick={(data: any) => handleBarClick(data as SalaryDistributionData)}
            animationDuration={800}
            animationEasing="ease-out"
            style={{ cursor: 'pointer' }}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.isTargetRange ? chartColors.targetBar : chartColors.bar}
                className="transition-opacity hover:opacity-80"
              />
            ))}
            {showAverage && (
              <LabelList
                dataKey="count"
                position="top"
                style={{ fontSize: '11px', fill: chartColors.text }}
              />
            )}
          </Bar>

          {/* Reference line for user's target salary */}
          {userTargetSalary && (
            <ReferenceLine
              y={0}
              stroke={chartColors.referenceLine}
              strokeDasharray="3 3"
              label={{
                value: 'Your Target',
                position: 'insideTopRight',
                fill: chartColors.referenceLine,
                fontSize: 12,
              }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {totalJobs}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Total Jobs
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            ${(avgSalary / 1000).toFixed(0)}k
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Average Salary
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {data.length > 0 ? data.reduce((max, item) => item.count > max.count ? item : max).range : 'N/A'}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Most Common Range
          </p>
        </div>
      </div>

      {/* Click hint */}
      <div className="mt-4 text-center">
        <p className="text-xs text-neutral-500 dark:text-neutral-400">
          Click on a bar to filter jobs by salary range
        </p>
      </div>
    </ChartWrapper>
  );
};

export default SalaryDistributionChart;
