'use client';

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
  Cell,
  LabelList,
} from 'recharts';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { TrendingUp, Award, CheckCircle } from 'lucide-react';
import { ChartWrapper } from './ChartWrapper';
import { Button2 } from '@/components/ui/Button2';
import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';

interface SkillsDemandData {
  skill: string;
  demand: number;
  userHasSkill: boolean;
  matchRate?: number;
  trending?: boolean;
}

type SortOption = 'demand' | 'name' | 'match';

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <motion.div
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
              Demand:
            </span>
            <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {data.demand} jobs
            </span>
          </div>
          {data.matchRate !== undefined && (
            <div className="flex items-center justify-between space-x-4">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Match Rate:
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {data.matchRate}%
              </span>
            </div>
          )}
          {data.userHasSkill && (
            <div className="mt-2 pt-2 border-t border-neutral-200 dark:border-neutral-700 flex items-center space-x-1">
              <CheckCircle className="h-3 w-3 text-success-600 dark:text-success-400" />
              <span className="text-xs text-success-600 dark:text-success-400 font-medium">
                You have this skill
              </span>
            </div>
          )}
          {data.trending && (
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-3 w-3 text-warning-600 dark:text-warning-400" />
              <span className="text-xs text-warning-600 dark:text-warning-400 font-medium">
                Trending
              </span>
            </div>
          )}
        </div>
      </motion.div>
    );
  }
  return null;
};

interface SkillsDemandChartProps {
  userSkills?: string[];
  onSkillClick?: (skill: string) => void;
  className?: string;
}

/**
 * SkillsDemandChart - Bar chart showing top skills in job postings
 * 
 * Features:
 * - Bar chart showing skill demand across job postings
 * - Compare with user's skills (overlay/highlight)
 * - Clickable bars to filter jobs by skill
 * - Sort by: frequency, match rate, trending
 * - Dark mode support
 * - Responsive design
 * - CSV/PNG export
 * - Show match rate for user's skills
 */
export const SkillsDemandChart: React.FC<SkillsDemandChartProps> = ({
  userSkills = [],
  onSkillClick,
  className = '',
}) => {
  const router = useRouter();
  const [data, setData] = useState<SkillsDemandData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('demand');
  const [showOnlyUserSkills, setShowOnlyUserSkills] = useState(false);
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

      // Extract and count skills from job postings
      const skillCounts = new Map<string, number>();
      
      jobs.forEach((job: any) => {
        const skills = job.required_skills || [];
        skills.forEach((skill: string) => {
          const normalizedSkill = skill.trim();
          if (normalizedSkill) {
            skillCounts.set(normalizedSkill, (skillCounts.get(normalizedSkill) || 0) + 1);
          }
        });
      });

      // Convert to array and calculate match rates
      const totalJobs = jobs.length;
      const chartData: SkillsDemandData[] = Array.from(skillCounts.entries())
        .map(([skill, count]) => {
          const userHasSkill = userSkills.some(
            userSkill => userSkill.toLowerCase() === skill.toLowerCase()
          );
          const matchRate = (count / totalJobs) * 100;
          
          // Simple trending detection: skills with >20% match rate
          const trending = matchRate > 20;

          return {
            skill,
            demand: count,
            userHasSkill,
            matchRate: Number(matchRate.toFixed(1)),
            trending,
          };
        })
        .filter(item => item.demand > 0);

      setData(chartData);
    } catch (err) {
      logger.error('SkillsDemandChart: Failed to fetch data', err);
      setError(err instanceof Error ? err.message : 'Failed to load chart data');
    } finally {
      setIsLoading(false);
    }
  }, [userSkills]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getSortedData = () => {
    let sorted = [...data];

    if (showOnlyUserSkills) {
      sorted = sorted.filter(item => item.userHasSkill);
    }

    switch (sortBy) {
      case 'demand':
        sorted.sort((a, b) => b.demand - a.demand);
        break;
      case 'name':
        sorted.sort((a, b) => a.skill.localeCompare(b.skill));
        break;
      case 'match':
        sorted.sort((a, b) => (b.matchRate || 0) - (a.matchRate || 0));
        break;
    }

    // Limit to top 15 for readability
    return sorted.slice(0, 15);
  };

  const sortedData = getSortedData();

  const handleBarClick = (data: SkillsDemandData) => {
    logger.info('SkillsDemandChart: Bar clicked', { skill: data.skill });
    
    if (onSkillClick) {
      onSkillClick(data.skill);
    } else {
      // Navigate to jobs page with skill filter
      router.push(`/jobs?skill=${encodeURIComponent(data.skill)}`);
    }
  };

  const handleExportCSV = () => {
    const csvContent = [
      ['Skill', 'Demand', 'Match Rate', 'You Have'],
      ...sortedData.map(item => [
        item.skill,
        item.demand.toString(),
        `${item.matchRate}%`,
        item.userHasSkill ? 'Yes' : 'No',
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `skills-demand-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportPNG = () => {
    alert('PNG export feature coming soon!');
  };

  const chartColors = {
    userSkill: isDarkMode ? '#34d399' : '#22c55e', // emerald-400 / green-500
    otherSkill: isDarkMode ? '#60a5fa' : '#3b82f6', // blue-400 / blue-500
    grid: isDarkMode ? '#374151' : '#e5e7eb', // gray-700 / gray-200
    text: isDarkMode ? '#d1d5db' : '#6b7280', // gray-300 / gray-500
  };

  const userSkillsCount = data.filter(item => item.userHasSkill).length;
  const topSkill = sortedData.length > 0 ? sortedData[0] : null;

  if (data.length === 0 && !isLoading && !error) {
    return (
      <ChartWrapper
        title="Skills Demand"
        description="Most in-demand skills across job postings"
        isLoading={false}
        error={null}
        className={className}
      >
        <div className="h-[350px] flex items-center justify-center">
          <div className="text-center">
            <Award className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400">
              No skills data available
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
              Jobs with required skills will appear here
            </p>
          </div>
        </div>
      </ChartWrapper>
    );
  }

  return (
    <ChartWrapper
      title="Skills Demand"
      description="Most in-demand skills across job postings"
      isLoading={isLoading}
      error={error}
      onExportCSV={handleExportCSV}
      onExportPNG={handleExportPNG}
      className={className}
      actions={
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 px-2 py-1 rounded-md bg-success-100 dark:bg-success-900/30">
            <CheckCircle className="h-3 w-3 text-success-600 dark:text-success-400" />
            <span className="text-xs font-medium text-success-700 dark:text-success-300">
              {userSkillsCount} matched
            </span>
          </div>
        </div>
      }
    >
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        {/* Sort Options */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-neutral-600 dark:text-neutral-400">Sort by:</span>
          <Button2
            size="sm"
            variant={sortBy === 'demand' ? 'primary' : 'outline'}
            onClick={() => setSortBy('demand')}
          >
            Demand
          </Button2>
          <Button2
            size="sm"
            variant={sortBy === 'match' ? 'primary' : 'outline'}
            onClick={() => setSortBy('match')}
          >
            Match Rate
          </Button2>
          <Button2
            size="sm"
            variant={sortBy === 'name' ? 'primary' : 'outline'}
            onClick={() => setSortBy('name')}
          >
            Name
          </Button2>
        </div>

        {/* Filter Options */}
        {userSkills.length > 0 && (
          <Button2
            size="sm"
            variant={showOnlyUserSkills ? 'primary' : 'ghost'}
            onClick={() => setShowOnlyUserSkills(!showOnlyUserSkills)}
          >
            Your Skills Only
          </Button2>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={sortedData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
          <XAxis
            type="number"
            stroke={chartColors.text}
            style={{ fontSize: '12px' }}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="skill"
            stroke={chartColors.text}
            style={{ fontSize: '12px' }}
            width={90}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            height={36}
            iconType="rect"
            formatter={(value) => (
              <span className="text-sm text-neutral-700 dark:text-neutral-300">
                {value}
              </span>
            )}
          />
          
          <Bar
            dataKey="demand"
            name="Job Postings"
            onClick={handleBarClick}
            animationDuration={800}
            animationEasing="ease-out"
            style={{ cursor: 'pointer' }}
          >
            {sortedData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.userHasSkill ? chartColors.userSkill : chartColors.otherSkill}
                className="transition-opacity hover:opacity-80"
              />
            ))}
            <LabelList
              dataKey="demand"
              position="right"
              style={{ fontSize: '11px', fill: chartColors.text }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {data.length}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Unique Skills
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-success-600 dark:text-success-400">
            {userSkillsCount}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Your Skills
          </p>
        </div>
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {topSkill?.skill || 'N/A'}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Most Demanded
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartColors.userSkill }}></div>
          <span className="text-neutral-600 dark:text-neutral-400">Your Skills</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartColors.otherSkill }}></div>
          <span className="text-neutral-600 dark:text-neutral-400">Other Skills</span>
        </div>
      </div>

      {/* Click hint */}
      <div className="mt-4 text-center">
        <p className="text-xs text-neutral-500 dark:text-neutral-400">
          Click on a bar to filter jobs by skill
        </p>
      </div>
    </ChartWrapper>
  );
};

export default SkillsDemandChart;
