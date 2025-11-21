'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useCallback } from 'react';
import { toast } from 'sonner';

import { logger } from '@/lib/logger';
import { webSocketService } from '@/lib/api/websocket';
import type { Application } from '@/types/application';

/**
 * Hook for real-time application status updates via WebSocket
 * 
 * Features:
 * - Listen for application status changes
 * - Show toast notifications
 * - Update application data in real-time
 * - Update dashboard stats
 * - Badge animations for status changes
 */

interface ApplicationStatusChangeEvent {
  application_id: number;
  old_status: string;
  new_status: string;
  application?: Application;
  job_title?: string;
  company?: string;
}

const STATUS_LABELS: Record<string, string> = {
  interested: 'Interested',
  applied: 'Applied',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
  accepted: 'Accepted',
  declined: 'Declined',
};

export function useRealtimeApplications() {
  const queryClient = useQueryClient();

  const handleStatusChange = useCallback((data: ApplicationStatusChangeEvent) => {
    logger.info('[Realtime Applications] Status change received:', data);

    const newStatusLabel = STATUS_LABELS[data.new_status] || data.new_status;
    const jobInfo = data.job_title && data.company
      ? `${data.job_title} at ${data.company}`
      : `Application #${data.application_id}`;

    // Show toast notification with appropriate styling
    const isPositive = ['offer', 'accepted', 'interview'].includes(data.new_status);
    const isNegative = ['rejected', 'declined'].includes(data.new_status);

    if (isPositive) {
      toast.success('Application Status Updated', {
        description: `${jobInfo} → ${newStatusLabel}`,
        duration: 5000,
      });
    } else if (isNegative) {
      toast.error('Application Status Updated', {
        description: `${jobInfo} → ${newStatusLabel}`,
        duration: 5000,
      });
    } else {
      toast.info('Application Status Updated', {
        description: `${jobInfo} → ${newStatusLabel}`,
        duration: 4000,
      });
    }

    // Update application in cache if we have the full data
    if (data.application) {
      const updatedApplication = data.application;
      queryClient.setQueryData<Application[]>(
        ['applications'],
        (old) => {
          if (!old) return old;
          return old.map(app =>
            app.id === data.application_id ? updatedApplication : app,
          );
        },
      );
    }

    // Invalidate queries to trigger refetch
    queryClient.invalidateQueries({ queryKey: ['applications'] });
    queryClient.invalidateQueries({ queryKey: ['applications', data.application_id] });
    queryClient.invalidateQueries({ queryKey: ['analytics'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  }, [queryClient]);

  useEffect(() => {
    // Subscribe to application status change events
    const onStatusChange = (data: any) => {
      handleStatusChange(data as ApplicationStatusChangeEvent);
    };

    webSocketService.on('application:status', onStatusChange);

    return () => {
      webSocketService.off('application:status', onStatusChange);
    };
  }, [handleStatusChange]);

  return {
    // Could expose additional functionality here if needed
  };
}
