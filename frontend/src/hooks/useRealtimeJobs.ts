'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';

import type { JobResponse } from '@/lib/api/client';
import { webSocketService } from '@/lib/api/websocket';
import { logger } from '@/lib/logger';

/**
 * Hook for real-time job recommendations via WebSocket
 * 
 * Features:
 * - Listen for new job recommendations
 * - Show toast notifications
 * - Update jobs list in real-time
 * - Track new job count
 * - Smooth animations for new items
 */

interface JobRecommendationEvent {
  job: JobResponse;
  match_score?: number;
  reason?: string;
}

export function useRealtimeJobs() {
  const [newJobsCount, setNewJobsCount] = useState(0);
  const [newJobs, setNewJobs] = useState<JobResponse[]>([]);
  const queryClient = useQueryClient();

  const clearNewJobs = useCallback(() => {
    setNewJobsCount(0);
    setNewJobs([]);
  }, []);

  useEffect(() => {
    // Subscribe to job match events
    const handleJobMatch = (data: any) => {
      logger.info('[Realtime Jobs] New job recommendation received:', data);

      const job = data.job as JobResponse;
      const matchScore = data.match_score || job.match_score;

      // Add to new jobs list
      setNewJobs(prev => [job, ...prev]);
      setNewJobsCount(prev => prev + 1);

      // Show toast notification
      toast.success('New Job Match!', {
        description: `${job.title} at ${job.company}${matchScore ? ` (${Math.round(matchScore)}% match)` : ''}`,
        action: {
          label: 'View',
          onClick: () => {
            // Navigate to job detail or open modal
            window.location.href = `/jobs/${job.id}`;
          },
        },
        duration: 5000,
      });

      // Invalidate jobs query to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    };

    webSocketService.on('job:match', handleJobMatch);

    return () => {
      webSocketService.off('job:match', handleJobMatch);
    };
  }, [queryClient]);

  return {
    newJobsCount,
    newJobs,
    clearNewJobs,
  };
}
