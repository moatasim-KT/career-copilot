/**
 * Status Breakdown Widget - Application status distribution
 */

'use client';

import {
  Clock,
  FileText,
  Calendar,
  Trophy,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';

interface StatusBreakdownWidgetProps {
  analytics: any;
}

export function StatusBreakdownWidget({ analytics }: StatusBreakdownWidgetProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'interested':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'applied':
        return <FileText className="h-5 w-5 text-blue-500" />;
      case 'interview':
        return <Calendar className="h-5 w-5 text-purple-500" />;
      case 'offer':
        return <Trophy className="h-5 w-5 text-green-500" />;
      case 'accepted':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'declined':
        return <XCircle className="h-5 w-5 text-neutral-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-neutral-400" />;
    }
  };

  if (
    !analytics?.application_status_breakdown ||
    Object.keys(analytics.application_status_breakdown).length === 0
  ) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-neutral-800 p-4 sm:p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
      <h2 className="text-xl md:text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
        Application Status Breakdown
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(analytics.application_status_breakdown).map(([status, count]) => (
          <div key={status} className="text-center">
            <div className="flex justify-center mb-2">{getStatusIcon(status)}</div>
            <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {String(count)}
            </p>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 capitalize">{status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
