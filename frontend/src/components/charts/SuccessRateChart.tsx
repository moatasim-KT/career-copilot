'use client';

import { TrendingUp, Award, AlertCircle } from 'lucide-react';
import React, { useState, useEffect, useCallback } from 'react';
import { FunnelChart, Funnel, Tooltip, LabelList, ResponsiveContainer, Cell } from 'recharts';

import { Button } from '@/components/ui/Button2';
import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';
import { m } from '@/lib/motion';

import { ChartWrapper } from './ChartWrapper';

interface SuccessRateData {
  name: string;
  value: number;
  fill: string;
  conversionRate?: number;
  benchmark?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <m.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-neutral-800 p-3 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-700"
      >
        <p className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          {data.name}
        </p>
        <div className="space-y-1">
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              Count:
            </span>
            <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {data.value}
            </span>
          </div>
          {data.conversionRate !== undefined && (
            <div className="flex items-center justify-between space-x-4">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Conversion:
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {data.conversionRate}%
              </span>
            </div>
          )}
          {data.benchmark !== undefined && (
            <div className="mt-2 pt-2 border-t border-neutral-200 dark:border-neutral-700">
              <div className="flex items-center justify-between space-x-4">
                <span className="text-xs text-neutral-600 dark:text-neutral-400">
                  Industry Avg:
                </span>
                <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
                  {data.benchmark}%
                </span>
              </div>
            </div>
          )}
        </div>
      </m.div>
    );
  }
  return null;
};

interface SuccessRateChartProps {
  showBenchmark?: boolean;
  className?: string;
}

/**
 * SuccessRateChart - Funnel chart showing application success rate
 * 
 * Features:
 * - Funnel chart: Applied → Interviewed → Offer → Accepted
 * - Show conversion rates at each stage
 * - Benchmark against industry averages (optional)
 * - Interactive hover states
 * - Dark mode support
 * - Responsive design
 * - CSV/PNG export
 * - Stage-by-stage breakdown
 */
export const SuccessRateChart: React.FC<SuccessRateChartProps> = ({
  showBenchmark = false,
  className = '',
}) => {
  const [data, setData] = useState<SuccessRateData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBenchmarkData, setShowBenchmarkData] = useState(showBenchmark);
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
    // Industry benchmark data (example values)
    const benchmarks = {
      Applied: 100,
      Interviewed: 25, // 25% of applications lead to interviews
      Offer: 10, // 10% of applications lead to offers
      Accepted: 8, // 8% of applications are accepted
    };
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.getApplications(0, 1000);
      
      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to fetch data');
      }

      const applications = response.data;

      // Count applications at each stage
      const statusCounts = {
        Applied: 0,
        Interviewed: 0,
        Offer: 0,
        Accepted: 0,
      };

      applications.forEach((app: any) => {
        const status = app.status?.toLowerCase();
        
        // All applications count as "Applied"
        statusCounts.Applied++;
        
        // Count interviews
        if (status === 'interview' || status === 'interviewing' || status === 'offer' || status === 'accepted') {
          statusCounts.Interviewed++;
        }
        
        // Count offers
        if (status === 'offer' || status === 'accepted') {
          statusCounts.Offer++;
        }
        
        // Count accepted
        if (status === 'accepted') {
          statusCounts.Accepted++;
        }
      });

      // Calculate conversion rates
      const total = statusCounts.Applied || 1;
      
      const chartColors = {
        applied: isDarkMode ? '#60a5fa' : '#3b82f6', // blue-400 / blue-500
        interviewed: isDarkMode ? '#a78bfa' : '#8b5cf6', // purple-400 / purple-500
        offer: isDarkMode ? '#4ade80' : '#22c55e', // green-400 / green-500
        accepted: isDarkMode ? '#34d399' : '#10b981', // emerald-400 / emerald-500
      };

      const funnelData: SuccessRateData[] = [
        {
          name: 'Applied',
          value: statusCounts.Applied,
          fill: chartColors.applied,
          conversionRate: 100,
          benchmark: benchmarks.Applied,
        },
        {
          name: 'Interviewed',
          value: statusCounts.Interviewed,
          fill: chartColors.interviewed,
          conversionRate: Number(((statusCounts.Interviewed / total) * 100).toFixed(1)),
          benchmark: benchmarks.Interviewed,
        },
        {
          name: 'Offer',
          value: statusCounts.Offer,
          fill: chartColors.offer,
          conversionRate: Number(((statusCounts.Offer / total) * 100).toFixed(1)),
          benchmark: benchmarks.Offer,
        },
        {
          name: 'Accepted',
          value: statusCounts.Accepted,
          fill: chartColors.accepted,
          conversionRate: Number(((statusCounts.Accepted / total) * 100).toFixed(1)),
          benchmark: benchmarks.Accepted,
        },
      ].filter(item => item.value > 0);

      setData(funnelData);
    } catch (err) {
      logger.error('SuccessRateChart: Failed to fetch data', err);
      setError(err instanceof Error ? err.message : 'Failed to load chart data');
    } finally {
      setIsLoading(false);
    }
  }, [isDarkMode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExportCSV = () => {
    const csvContent = [
      ['Stage', 'Count', 'Conversion Rate', 'Industry Benchmark'],
      ...data.map(item => [
        item.name,
        item.value.toString(),
        `${item.conversionRate}%`,
        `${item.benchmark}%`,
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `success-rate-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportPNG = () => {
    alert('PNG export feature coming soon!');
  };

  // Calculate overall success rate (accepted / applied)
  const overallSuccessRate = data.length > 0 && data[0].value > 0
    ? ((data[data.length - 1]?.value || 0) / data[0].value) * 100
    : 0;

  // Compare with benchmark
  const lastStage = data[data.length - 1];
  const benchmarkComparison = data.length > 0 && lastStage?.benchmark !== undefined
    ? overallSuccessRate - lastStage.benchmark
    : 0;

  if (data.length === 0 && !isLoading && !error) {
    return (
      <ChartWrapper
        title="Application Success Rate"
        description="Track your conversion rate through the application process"
        isLoading={false}
        error={null}
        className={className}
      >
        <div className="h-[350px] flex items-center justify-center">
          <div className="text-center">
            <Award className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400">
              No application data available
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
              Start applying to jobs to track your success rate
            </p>
          </div>
        </div>
      </ChartWrapper>
    );
  }

  return (
    <ChartWrapper
      title="Application Success Rate"
      description="Track your conversion rate through the application process"
      isLoading={isLoading}
      error={error}
      onExportCSV={handleExportCSV}
      onExportPNG={handleExportPNG}
      className={className}
      actions={
        <div className="flex items-center space-x-2">
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-md ${
            benchmarkComparison >= 0
              ? 'bg-success-100 dark:bg-success-900/30'
              : 'bg-warning-100 dark:bg-warning-900/30'
          }`}>
            {benchmarkComparison >= 0 ? (
              <TrendingUp className="h-3 w-3 text-success-600 dark:text-success-400" />
            ) : (
              <AlertCircle className="h-3 w-3 text-warning-600 dark:text-warning-400" />
            )}
            <span className={`text-xs font-medium ${
              benchmarkComparison >= 0
                ? 'text-success-700 dark:text-success-300'
                : 'text-warning-700 dark:text-warning-300'
            }`}>
              {benchmarkComparison >= 0 ? '+' : ''}{benchmarkComparison.toFixed(1)}% vs avg
            </span>
          </div>
        </div>
      }
    >
      {/* Controls */}
      <div className="flex items-center justify-end mb-4">
        <Button
          size="sm"
          variant={showBenchmarkData ? 'primary' : 'ghost'}
          onClick={() => setShowBenchmarkData(!showBenchmarkData)}
        >
          Show Benchmark
        </Button>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <FunnelChart>
          <Tooltip content={<CustomTooltip />} />
          <Funnel
            dataKey="value"
            data={data}
            isAnimationActive
            animationDuration={800}
            animationEasing="ease-out"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
            <LabelList
              position="right"
              fill={isDarkMode ? '#d1d5db' : '#374151'}
              stroke="none"
              dataKey="name"
              style={{ fontSize: '14px', fontWeight: 500 }}
            />
            <LabelList
              position="inside"
              fill="#ffffff"
              stroke="none"
              dataKey="value"
              style={{ fontSize: '16px', fontWeight: 'bold' }}
            />
          </Funnel>
        </FunnelChart>
      </ResponsiveContainer>

      {/* Conversion Rates Table */}
      <div className="mt-6 space-y-3">
        <h4 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
          Stage Conversion Rates
        </h4>
        <div className="space-y-2">
          {data.map((stage) => (
            <div
              key={stage.name}
              className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-800/50 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: stage.fill }}
                ></div>
                <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  {stage.name}
                </span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                    {stage.conversionRate ?? 0}%
                  </p>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400">
                    {stage.value} applications
                  </p>
                </div>
                {showBenchmarkData && stage.benchmark !== undefined && stage.conversionRate !== undefined && (
                  <div className="text-right">
                    <p className="text-xs text-neutral-600 dark:text-neutral-400">
                      Avg: {stage.benchmark}%
                    </p>
                    <p className={`text-xs font-medium ${
                      stage.conversionRate >= stage.benchmark
                        ? 'text-success-600 dark:text-success-400'
                        : 'text-warning-600 dark:text-warning-400'
                    }`}>
                      {stage.conversionRate >= stage.benchmark ? '+' : ''}
                      {(stage.conversionRate - stage.benchmark).toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {data[0]?.value || 0}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Total Applications
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-success-600 dark:text-success-400">
            {overallSuccessRate.toFixed(1)}%
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Success Rate
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {data[data.length - 1]?.value || 0}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Accepted Offers
          </p>
        </div>
      </div>
    </ChartWrapper>
  );
};

export default SuccessRateChart;
