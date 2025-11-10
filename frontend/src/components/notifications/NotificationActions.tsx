/**
 * NotificationActions Component
 * Inline actions for notifications (view, dismiss, snooze)
 */

'use client';

import {
  ExternalLink,
  X,
  Clock,
  Eye,
  FileText,
  Briefcase,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

import type { Notification, NotificationAction } from '@/types/notification';
import { cn } from '@/lib/utils';
import Button2 from '@/components/ui/Button2';

interface NotificationActionsProps {
  notification: Notification;
  onAction?: (action: NotificationAction, notificationId: string) => void;
  onDismiss?: (notificationId: string) => void;
  onSnooze?: (notificationId: string, duration: number) => void;
  compact?: boolean;
  className?: string;
}

export default function NotificationActions({
  notification,
  onAction,
  onDismiss,
  onSnooze,
  compact = false,
  className,
}: NotificationActionsProps) {
  const [isSnoozing, setIsSnoozing] = useState(false);

  const handleDismiss = () => {
    onDismiss?.(notification.id);
    onAction?.('dismiss', notification.id);
  };

  const handleSnooze = (hours: number) => {
    const duration = hours * 60 * 60 * 1000; // Convert to milliseconds
    onSnooze?.(notification.id, duration);
    onAction?.('snooze', notification.id);
    setIsSnoozing(false);
  };

  const handleView = () => {
    onAction?.('view', notification.id);
  };

  // Determine action based on notification category
  const getPrimaryAction = () => {
    if (notification.actionUrl && notification.actionLabel) {
      return {
        label: notification.actionLabel,
        url: notification.actionUrl,
        icon: ExternalLink,
      };
    }

    switch (notification.category) {
      case 'job_alert':
        return {
          label: 'View Job',
          url: notification.actionUrl || '/jobs',
          icon: Briefcase,
        };
      case 'application':
        return {
          label: 'View Application',
          url: notification.actionUrl || '/applications',
          icon: FileText,
        };
      case 'recommendation':
        return {
          label: 'View Recommendations',
          url: notification.actionUrl || '/recommendations',
          icon: Eye,
        };
      default:
        return null;
    }
  };

  const primaryAction = getPrimaryAction();

  if (compact) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        {primaryAction && (
          <Link
            href={primaryAction.url}
            onClick={handleView}
            className="text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors inline-flex items-center gap-1"
          >
            {primaryAction.label}
            <primaryAction.icon className="w-3 h-3" />
          </Link>
        )}
        
        <button
          onClick={handleDismiss}
          className="p-1 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
          title="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      {/* Primary Action */}
      {primaryAction && (
        <Link href={primaryAction.url} onClick={handleView}>
          <Button2 size="sm" variant="primary">
            <primaryAction.icon className="w-4 h-4 mr-2" />
            {primaryAction.label}
          </Button2>
        </Link>
      )}

      {/* Snooze Action */}
      {!isSnoozing ? (
        <Button2
          size="sm"
          variant="outline"
          onClick={() => setIsSnoozing(true)}
        >
          <Clock className="w-4 h-4 mr-2" />
          Remind me later
        </Button2>
      ) : (
        <div className="flex items-center gap-1">
          <Button2
            size="sm"
            variant="outline"
            onClick={() => handleSnooze(1)}
          >
            1h
          </Button2>
          <Button2
            size="sm"
            variant="outline"
            onClick={() => handleSnooze(4)}
          >
            4h
          </Button2>
          <Button2
            size="sm"
            variant="outline"
            onClick={() => handleSnooze(24)}
          >
            1d
          </Button2>
          <Button2
            size="sm"
            variant="ghost"
            onClick={() => setIsSnoozing(false)}
          >
            <X className="w-4 h-4" />
          </Button2>
        </div>
      )}

      {/* Dismiss Action */}
      <Button2
        size="sm"
        variant="ghost"
        onClick={handleDismiss}
      >
        <X className="w-4 h-4 mr-2" />
        Dismiss
      </Button2>
    </div>
  );
}

/**
 * Compact notification actions for use in lists
 */
export function CompactNotificationActions({
  notification,
  onAction,
  onDismiss,
  className,
}: Omit<NotificationActionsProps, 'compact' | 'onSnooze'>) {
  return (
    <NotificationActions
      notification={notification}
      onAction={onAction}
      onDismiss={onDismiss}
      compact
      className={className}
    />
  );
}

/**
 * Full notification actions for use in detail views
 */
export function FullNotificationActions({
  notification,
  onAction,
  onDismiss,
  onSnooze,
  className,
}: NotificationActionsProps) {
  return (
    <NotificationActions
      notification={notification}
      onAction={onAction}
      onDismiss={onDismiss}
      onSnooze={onSnooze}
      compact={false}
      className={className}
    />
  );
}
