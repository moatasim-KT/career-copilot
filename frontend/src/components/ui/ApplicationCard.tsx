/**
 * ApplicationCard Component
 * 
 * A card component for displaying application information in lists and grids.
 * Supports different variants and selection state.
 */

'use client';

import { Calendar, Clock, FileText, Building2, CalendarPlus } from 'lucide-react';
import React, { useState } from 'react';

import CreateEventDialog from '@/components/calendar/CreateEventDialog';

import { Badge } from './Badge';

/**
 * Application interface matching backend ApplicationResponse
 */
export interface Application {
  id: number;
  user_id: number;
  job_id: number;
  status: string;
  applied_date: string | null;
  response_date: string | null;
  interview_date: string | null;
  offer_date: string | null;
  notes: string | null;
  interview_feedback: Record<string, any> | null;
  follow_up_date: string | null;
  created_at: string;
  updated_at: string;
  // Optional job details that might be included
  job_title?: string;
  company_name?: string;
  job_location?: string;
}

/**
 * ApplicationCard Props
 */
export interface ApplicationCardProps {
  /** Application data to display */
  application: Application;
  /** Card variant */
  variant?: 'default' | 'compact' | 'detailed';
  /** Whether the card is selected */
  isSelected?: boolean;
  /** Callback when card is selected/deselected */
  onSelect?: () => void;
  /** Custom className */
  className?: string;
  /** Callback when calendar event is added */
  onEventAdded?: () => void;
}

/**
 * Get status badge color based on application status
 */
function getStatusColor(status: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  const statusLower = status.toLowerCase();

  if (statusLower === 'accepted' || statusLower === 'offer') {
    return 'success';
  }
  if (statusLower === 'rejected' || statusLower === 'declined') {
    return 'error';
  }
  if (statusLower === 'interview' || statusLower === 'interviewing') {
    return 'warning';
  }
  if (statusLower === 'applied') {
    return 'info';
  }
  return 'default';
}

/**
 * Format date string to readable format
 */
function formatDate(dateString: string | null): string {
  if (!dateString) return 'N/A';

  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return 'Invalid date';
  }
}

/**
 * Calculate days since application
 */
function getDaysSince(dateString: string | null): number {
  if (!dateString) return 0;

  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  } catch {
    return 0;
  }
}

/**
 * ApplicationCard Component
 * 
 * Displays application information in a card format with support for
 * different variants and selection state.
 * 
 * @example
 * ```tsx
 * <ApplicationCard
 *   application={application}
 *   variant="default"
 *   isSelected={isSelected}
 *   onSelect={handleSelect}
 * />
 * ```
 */
export function ApplicationCard({
  application,
  variant = 'default',
  isSelected = false,
  onSelect,
  className = '',
  onEventAdded,
}: ApplicationCardProps) {
  const [showEventDialog, setShowEventDialog] = useState(false);
  const daysSince = getDaysSince(application.applied_date || application.created_at);
  const jobDisplayTitle = application.job_title || `Job #${application.job_id}`;
  const companyDisplayName = application.company_name || 'Company';
  const selectionLabel = `Select application ${jobDisplayTitle}${companyDisplayName ? ` at ${companyDisplayName}` : ''}`;

  const handleEventCreated = () => {
    setShowEventDialog(false);
    if (onEventAdded) {
      onEventAdded();
    }
  };

  // Pre-filled event data based on application
  const defaultEventData = {
    title: application.interview_date
      ? `Interview: ${jobDisplayTitle} at ${companyDisplayName}`
      : `Follow-up: ${jobDisplayTitle}`,
    description: `${application.status} - ${companyDisplayName}\n\nJob: ${jobDisplayTitle}\nApplication ID: ${application.id}`,
    applicationId: application.id,
  };

  // Compact variant - minimal information
  if (variant === 'compact') {
    return (
      <div
        className={`
          bg-white dark:bg-neutral-800 rounded-lg shadow-sm p-4 
          flex items-center justify-between
          border border-neutral-200 dark:border-neutral-700
          hover:shadow-md transition-shadow
          ${isSelected ? 'ring-2 ring-blue-500 dark:ring-blue-400' : ''}
          ${className}
        `}
      >
        {onSelect && (
          <input
            type="checkbox"
            className="mr-3 rounded border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-blue-500"
            checked={isSelected}
            aria-label={selectionLabel}
            onChange={onSelect}
            onClick={(e) => e.stopPropagation()}
          />
        )}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            {jobDisplayTitle}
          </h3>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            {companyDisplayName}
          </p>
        </div>
        <div className="text-right">
          <Badge variant={getStatusColor(application.status)}>
            {application.status}
          </Badge>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            {formatDate(application.applied_date)}
          </p>
        </div>
      </div>
    );
  }

  // Detailed variant - full information
  if (variant === 'detailed') {
    return (
      <div
        className={`
          bg-white dark:bg-neutral-800 rounded-lg shadow-md p-6
          border border-neutral-200 dark:border-neutral-700
          hover:shadow-lg transition-shadow
          ${isSelected ? 'ring-2 ring-blue-500 dark:ring-blue-400' : ''}
          ${className}
        `}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            {onSelect && (
              <input
                type="checkbox"
                className="float-right ml-3 rounded border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-blue-500"
                checked={isSelected}
                aria-label={selectionLabel}
                onChange={onSelect}
                onClick={(e) => e.stopPropagation()}
              />
            )}
            <h3 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              {jobDisplayTitle}
            </h3>
            <p className="text-md text-neutral-700 dark:text-neutral-300 mt-1 flex items-center">
              <Building2 className="w-4 h-4 mr-2" />
              {companyDisplayName}
            </p>
          </div>
        </div>

        <div className="space-y-3 mb-4">
          <div className="flex items-center text-sm text-neutral-600 dark:text-neutral-400">
            <Calendar className="w-4 h-4 mr-2" />
            <span>Applied: {formatDate(application.applied_date)}</span>
            <span className="ml-4 text-neutral-500 dark:text-neutral-500">
              ({daysSince} days ago)
            </span>
          </div>

          {application.interview_date && (
            <div className="flex items-center text-sm text-neutral-600 dark:text-neutral-400">
              <Clock className="w-4 h-4 mr-2" />
              <span>Interview: {formatDate(application.interview_date)}</span>
            </div>
          )}

          {application.notes && (
            <div className="flex items-start text-sm text-neutral-600 dark:text-neutral-400">
              <FileText className="w-4 h-4 mr-2 mt-0.5" />
              <span className="line-clamp-2">{application.notes}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-neutral-200 dark:border-neutral-700">
          <Badge variant={getStatusColor(application.status)} className="text-sm">
            {application.status}
          </Badge>
          <div className="flex gap-2">
            <button
              onClick={() => setShowEventDialog(true)}
              className="px-3 py-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors text-sm font-medium flex items-center gap-2"
            >
              <CalendarPlus className="w-4 h-4" />
              Add to Calendar
            </button>
            <button
              className="px-4 py-2 bg-neutral-100 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors text-sm font-medium"
            >
              View Details
            </button>
          </div>
        </div>

        <CreateEventDialog
          open={showEventDialog}
          onOpenChange={setShowEventDialog}
          onEventCreated={handleEventCreated}
          defaultValues={defaultEventData}
        />
      </div>
    );
  }

  // Default variant - balanced information
  return (
    <div
      className={`
        bg-white dark:bg-neutral-800 rounded-lg shadow-sm p-6 relative
        border border-neutral-200 dark:border-neutral-700
        hover:shadow-md transition-shadow
        ${isSelected ? 'ring-2 ring-blue-500 dark:ring-blue-400' : ''}
        ${className}
      `}
    >
      {onSelect && (
        <input
          type="checkbox"
          className="absolute top-4 right-4 rounded border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-blue-500"
          checked={isSelected}
          aria-label={selectionLabel}
          onChange={onSelect}
          onClick={(e) => e.stopPropagation()}
        />
      )}

      <div className="pr-8">
        <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
          {jobDisplayTitle}
        </h3>
        <p className="text-md text-neutral-700 dark:text-neutral-300 mt-1 flex items-center">
          <Building2 className="w-4 h-4 mr-2" />
          {companyDisplayName}
        </p>
      </div>

      <div className="flex items-center text-sm text-neutral-600 dark:text-neutral-400 mt-4">
        <Calendar className="w-4 h-4 mr-2" />
        <span>Applied: {formatDate(application.applied_date)}</span>
        <span className="ml-2 text-neutral-500 dark:text-neutral-500">
          ({daysSince}d ago)
        </span>
      </div>

      {application.interview_date && (
        <div className="flex items-center text-sm text-neutral-600 dark:text-neutral-400 mt-2">
          <Clock className="w-4 h-4 mr-2" />
          <span>Interview: {formatDate(application.interview_date)}</span>
        </div>
      )}

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <Badge variant={getStatusColor(application.status)}>
          {application.status}
        </Badge>
        <div className="flex gap-2">
          <button
            onClick={() => setShowEventDialog(true)}
            className="px-3 py-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors text-sm flex items-center gap-2"
            title="Add interview or follow-up to calendar"
          >
            <CalendarPlus className="w-4 h-4" />
            Calendar
          </button>
          <button
            className="px-4 py-2 bg-neutral-100 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors text-sm"
          >
            View Details
          </button>
        </div>
      </div>

      <CreateEventDialog
        open={showEventDialog}
        onOpenChange={setShowEventDialog}
        onEventCreated={handleEventCreated}
        defaultValues={defaultEventData}
      />
    </div>
  );
}

export default ApplicationCard;
