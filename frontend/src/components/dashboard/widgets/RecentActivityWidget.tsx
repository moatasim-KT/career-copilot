/**
 * Recent Activity Widget - Recent application activity
 */

'use client';

import {
  FileText,
  Clock,
  Calendar,
  Trophy,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';

interface RecentActivityWidgetProps {
  recentApplications: any[];
}

export function RecentActivityWidget({ recentApplications }: RecentActivityWidgetProps) {
  const getStatusIcon = (status: string | undefined) => {
    switch (status) {
      case 'interested':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'applied':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'interview':
        return <Calendar className="h-4 w-4 text-purple-500" />;
      case 'offer':
        return <Trophy className="h-4 w-4 text-green-500" />;
      case 'accepted':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'declined':
        return <XCircle className="h-4 w-4 text-neutral-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-neutral-400" />;
    }
  };

  const getStatusColor = (status: string | undefined) => {
    switch (status) {
      case 'interested':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'applied':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      case 'interview':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300';
      case 'offer':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'accepted':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'rejected':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      case 'declined':
        return 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-300';
      default:
        return 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-300';
    }
  };

  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
      <div className="p-4 sm:p-6 border-b border-neutral-200 dark:border-neutral-700">
        <h2 className="text-xl md:text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          Recent Activity
        </h2>
      </div>
      <div className="p-4 sm:p-6">
        {recentApplications.length > 0 ? (
          <div className="space-y-4">
            {recentApplications.map((application) => (
              <div
                key={application.id}
                className="flex items-center justify-between p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">{getStatusIcon(application.status)}</div>
                  <div>
                    <p className="font-medium text-neutral-900 dark:text-neutral-100">
                      {application.job_title || 'Unknown Position'}
                    </p>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      {application.job_company || 'Unknown Company'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(application.status)}`}
                  >
                    {application.status?.charAt(0).toUpperCase()}
                    {application.status?.slice(1)}
                  </span>
                  {application.applied_at && (
                    <span className="text-sm text-neutral-500 dark:text-neutral-400">
                      {new Date(application.applied_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400">No applications yet</p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
              Start by adding jobs and applying to them
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
