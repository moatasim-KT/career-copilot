import { Archive, Download, Trash2, RefreshCw } from 'lucide-react';

import { apiClient, type Application } from '@/lib/api';
import { exportToCSV } from '@/lib/export';
import { logger } from '@/lib/logger';

import type { BulkAction } from '@/components/ui/BulkActionBar';

export interface ApplicationBulkActionsOptions {
  applications: Application[];
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
  onRefresh?: () => void;
}

export function createApplicationBulkActions({
  applications,
  onSuccess,
  onError,
  onRefresh,
}: ApplicationBulkActionsOptions): BulkAction[] {
  return [
    {
      id: 'change-status-interested',
      label: 'Mark as Interested',
      icon: RefreshCw,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(appId =>
              apiClient.updateApplication(appId, { status: 'interested' })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Updated ${successCount} application${successCount > 1 ? 's' : ''} to Interested`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to update ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk status change to interested completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk status change failed', error);
          onError?.('Failed to update application status');
          throw error;
        }
      },
    },
    {
      id: 'change-status-applied',
      label: 'Mark as Applied',
      icon: RefreshCw,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(appId =>
              apiClient.updateApplication(appId, { status: 'applied' })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Updated ${successCount} application${successCount > 1 ? 's' : ''} to Applied`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to update ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk status change to applied completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk status change failed', error);
          onError?.('Failed to update application status');
          throw error;
        }
      },
    },
    {
      id: 'change-status-interview',
      label: 'Mark as Interview',
      icon: RefreshCw,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(appId =>
              apiClient.updateApplication(appId, { status: 'interview' })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Updated ${successCount} application${successCount > 1 ? 's' : ''} to Interview`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to update ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk status change to interview completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk status change failed', error);
          onError?.('Failed to update application status');
          throw error;
        }
      },
    },
    {
      id: 'change-status-offer',
      label: 'Mark as Offer',
      icon: RefreshCw,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(appId =>
              apiClient.updateApplication(appId, { status: 'offer' })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Updated ${successCount} application${successCount > 1 ? 's' : ''} to Offer`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to update ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk status change to offer completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk status change failed', error);
          onError?.('Failed to update application status');
          throw error;
        }
      },
    },
    {
      id: 'change-status-rejected',
      label: 'Mark as Rejected',
      icon: RefreshCw,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(appId =>
              apiClient.updateApplication(appId, { status: 'rejected' })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Updated ${successCount} application${successCount > 1 ? 's' : ''} to Rejected`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to update ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk status change to rejected completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk status change failed', error);
          onError?.('Failed to update application status');
          throw error;
        }
      },
    },
    {
      id: 'change-status-accepted',
      label: 'Mark as Accepted',
      icon: RefreshCw,
      variant: 'outline',
      requiresConfirmation: false,
      action: async (selectedIds: string[] | number[]) => {
        try {
          const numericIds = selectedIds.map(id => typeof id === 'string' ? parseInt(id) : id);
          
          const results = await Promise.allSettled(
            numericIds.map(appId =>
              apiClient.updateApplication(appId, { status: 'accepted' })
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Updated ${successCount} application${successCount > 1 ? 's' : ''} to Accepted`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to update ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk status change to accepted completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk status change failed', error);
          onError?.('Failed to update application status');
          throw error;
        }
      },
    },
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
            numericIds.map(appId =>
              apiClient.updateApplication(appId, { archived: true } as any)
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Archived ${successCount} application${successCount > 1 ? 's' : ''}`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to archive ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk archive completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk archive failed', error);
          onError?.('Failed to archive applications');
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
          
          const selectedApplications = applications.filter(app => numericIds.includes(app.id));

          if (selectedApplications.length === 0) {
            onError?.('No applications to export');
            return;
          }

          // Flatten application data for CSV export
          const exportData = selectedApplications.map(app => ({
            id: app.id,
            company: app.job?.company || '',
            job_title: app.job?.title || '',
            status: app.status,
            applied_date: app.applied_date || '',
            interview_date: app.interview_date || '',
            response_date: app.response_date || '',
            notes: app.notes || '',
          }));

          const columns = [
            'id',
            'company',
            'job_title',
            'status',
            'applied_date',
            'interview_date',
            'response_date',
            'notes',
          ] as (keyof typeof exportData[0])[];

          exportToCSV(exportData, columns, `applications_export_${new Date().toISOString().split('T')[0]}`);

          onSuccess?.(`Exported ${selectedApplications.length} application${selectedApplications.length > 1 ? 's' : ''} to CSV`);
          logger.log('Bulk export to CSV completed', { count: selectedApplications.length });
        } catch (error) {
          logger.error('Bulk export to CSV failed', error);
          onError?.('Failed to export applications to CSV');
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
            numericIds.map(appId =>
              apiClient.deleteApplication(appId)
            )
          );

          const successCount = results.filter(r => r.status === 'fulfilled').length;
          const failureCount = results.filter(r => r.status === 'rejected').length;

          if (successCount > 0) {
            onSuccess?.(`Successfully deleted ${successCount} application${successCount > 1 ? 's' : ''}`);
            onRefresh?.();
          }

          if (failureCount > 0) {
            onError?.(`Failed to delete ${failureCount} application${failureCount > 1 ? 's' : ''}`);
          }

          logger.log('Bulk delete completed', { successCount, failureCount });
        } catch (error) {
          logger.error('Bulk delete failed', error);
          onError?.('Failed to delete applications');
          throw error;
        }
      },
    },
  ];
}
