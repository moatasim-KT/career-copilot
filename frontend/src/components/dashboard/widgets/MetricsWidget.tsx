/**
 * Metrics Widget - Key dashboard metrics
 */

'use client';

import { Briefcase, FileText, Calendar, Trophy } from 'lucide-react';

interface MetricsWidgetProps {
  analytics: any;
}

export function MetricsWidget({ analytics }: MetricsWidgetProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-4">
      <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center">
          <Briefcase className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          <div className="ml-4">
            <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
              Total Jobs
            </p>
            <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {analytics?.total_jobs || 0}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center">
          <FileText className="h-8 w-8 text-green-600 dark:text-green-400" />
          <div className="ml-4">
            <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
              Applications
            </p>
            <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {analytics?.total_applications || 0}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center">
          <Calendar className="h-8 w-8 text-purple-600 dark:text-purple-400" />
          <div className="ml-4">
            <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
              Interviews
            </p>
            <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {analytics?.interviews_scheduled || 0}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center">
          <Trophy className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
          <div className="ml-4">
            <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
              Offers
            </p>
            <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {analytics?.offers_received || 0}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
