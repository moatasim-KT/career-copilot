import { Archive, Star, StarOff, Download, Eye, EyeOff, Trash2 } from 'lucide-react';

import { JobsService, type JobResponse } from '@/lib/api/client';
import { exportToCSV } from '@/lib/export';
import { logger } from '@/lib/logger';

import type { BulkAction } from '@/components/ui/BulkActionBar';

export interface JobBulkActionsOptions {
  jobs: JobResponse[];
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
  onRefresh?: () => void;
}

export function createJobBulkActions({
  jobs,
  onSuccess,
  onError,
  onRefresh,
}: JobBulkActionsOptions): BulkAction[] {
  return [
    {
      id: 'archive',
      label: 'Archive',
      icon: Archive,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(jobId =>
              JobsService.updateJobApiV1JobsJobIdPut({
                jobId,
                requestBody: { archived: true } as any,
              })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Successfully archived ${successCount} job${successCount > 1 ? 's' : ''}`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to archive ${failureCount} job${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk archive completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk archive failed', error);
          onError?.('Failed to archive jobs');
          throw error;
        }
      },
    },
    {
      id: 'add-to-wishlist',
      label: 'Add to Wishlist',
      icon: Star,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(jobId =>
              JobsService.updateJobApiV1JobsJobIdPut({
                jobId,
                requestBody: { is_saved: true } as any,
              })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Added ${successCount} job${successCount > 1 ? 's' : ''} to wishlist`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to add ${failureCount} job${failureCount > 1 ? 's' : ''} to wishlist`);
          }

          logger.log('Bulk add to wishlist completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk add to wishlist failed', error);
          onError?.('Failed to add jobs to wishlist');
          throw error;
        }
      },
    },
    {
      id: 'remove-from-wishlist',
      label: 'Remove from Wishlist',
      icon: StarOff,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(jobId =>
              JobsService.updateJobApiV1JobsJobIdPut({
                jobId,
                requestBody: { is_saved: false } as any,
              })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Removed ${successCount} job${successCount > 1 ? 's' : ''} from wishlist`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to remove ${failureCount} job${failureCount > 1 ? 's' : ''} from wishlist`);
          }

          logger.log('Bulk remove from wishlist completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk remove from wishlist failed', error);
          onError?.('Failed to remove jobs from wishlist');
          throw error;
        }
      },
    },
    {
      id: 'mark-viewed',
      label: 'Mark as Viewed',
      icon: Eye,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(jobId =>
              JobsService.updateJobApiV1JobsJobIdPut({
                jobId,
                requestBody: { is_viewed: true } as any,
              })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Marked ${successCount} job${successCount > 1 ? 's' : ''} as viewed`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to mark ${failureCount} job${failureCount > 1 ? 's' : ''} as viewed`);
          }

          logger.log('Bulk mark as viewed completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk mark as viewed failed', error);
          onError?.('Failed to mark jobs as viewed');
          throw error;
        }
      },
    },
    {
      id: 'mark-unviewed',
      label: 'Mark as Unviewed',
      icon: EyeOff,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(jobId =>
              JobsService.updateJobApiV1JobsJobIdPut({
                jobId,
                requestBody: { is_viewed: false } as any,
              })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Marked ${successCount} job${successCount > 1 ? 's' : ''} as unviewed`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to mark ${failureCount} job${failureCount > 1 ? 's' : ''} as unviewed`);
          }

          logger.log('Bulk mark as unviewed completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk mark as unviewed failed', error);
          onError?.('Failed to mark jobs as unviewed');
          throw error;
        }
      },
    },
    {
      id: 'export-csv',
      label: 'Export to CSV',
      icon: Download,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const selectedJobs = jobs.filter(job => job.id && numericIds.includes(job.id));

          if (selectedJobs.length === 0) {
            onError?.('No jobs to export');
            return;
          }

          const columns: (keyof JobResponse)[] = [
            'company',
            'title',
            'location',
            'job_type',
            'salary_range',
            'remote',
            'source',
            'url',
          ];

          exportToCSV(selectedJobs, columns, `jobs_export_${new Date().toISOString().split('T')[0]}`);

          onSuccess?.(`Exported ${selectedJobs.length} job${selectedJobs.length > 1 ? 's' : ''} to CSV`);
          logger.log('Bulk export to CSV completed', { count: selectedJobs.length });
        } catch (error) {
          logger.error('Bulk export to CSV failed', error);
          onError?.('Failed to export jobs to CSV');
          throw error;
        }
      },
    },
    {
      id: 'delete',
      label: 'Delete',
      icon: Trash2,
      variant: 'destructive',
      requiresConfirmation: true,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(jobId =>
              JobsService.deleteJobApiV1JobsJobIdDelete({ jobId })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Successfully deleted ${successCount} job${successCount > 1 ? 's' : ''}`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to delete ${failureCount} job${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk delete completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk delete failed', error);
          onError?.('Failed to delete jobs');
          throw error;
        }
      },
    },
  ];
}
