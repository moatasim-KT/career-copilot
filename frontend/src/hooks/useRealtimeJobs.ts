'use client';

import { useEffect, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { getWebSocketClient } from '@/lib/websocket';
import { logger } from '@/lib/logger';
import type { JobResponse } from '@/lib/api/client';

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
    const wsClient = getWebSocketClient();

    // Subscribe to job recommendation events
    const unsubscribe = wsClient.subscribe<JobRecommendationEvent>(
      'job:recommendation',
      (data) => {
        logger.info('[Realtime Jobs] New job recommendation received:', data);

        const job = data.job;
        const matchScore = data.match_score || job.match_score;
        const reason = data.reason || 'New job matches your profile';

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
      },
    );

    return () => {
      unsubscribe();
    };
  }, [queryClient]);

  return {
    newJobsCount,
    newJobs,
    clearNewJobs,
  };
}
