/**
 * Daily Goal Widget - Daily application goal progress
 */

'use client';

import { Target } from 'lucide-react';

interface DailyGoalWidgetProps {
  analytics: any;
}

export function DailyGoalWidget({ analytics }: DailyGoalWidgetProps) {
  if (!analytics) return null;

  return (
    <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl md:text-2xl font-semibold text-neutral-900 dark:text-neutral-100 flex items-center">
          <Target className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
          Daily Application Goal
        </h2>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-neutral-900 dark:text-neutral-100">
          <span>Progress</span>
          <span>
            {analytics.daily_applications_today} / {analytics.daily_application_goal}
          </span>
        </div>
        <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
          <div
            className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{
              width: `${Math.min(analytics.daily_goal_progress ?? 0, 100)}%`,
            }}
          ></div>
        </div>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          {(analytics.daily_goal_progress ?? 0) >= 100
            ? '🎉 Goal achieved today!'
            : `${(analytics.daily_application_goal ?? 0) - (analytics.daily_applications_today ?? 0)} more applications to reach your goal`}
        </p>
      </div>
    </div>
  );
}
