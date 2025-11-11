/**
 * Search Applications Hook
 * 
 * Provides search functionality for applications with React Query.
 */

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';
import { queryKeys, getCacheConfig } from '@/lib/queryClient';

export function useSearchApplications(query: string, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.applications.search(query),
    queryFn: async () => {
      if (!query || query.trim().length === 0) {
        return [];
      }
      const response = await apiClient.searchApplications(query.trim(), 10);
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      // Client-side filtering for applications since backend doesn't have full search
      const applications = response.data || [];
      const lowerQuery = query.toLowerCase();
      
      return applications.filter(app => {
        // Search in job title, company, status, and notes
        const jobTitle = app.job?.title?.toLowerCase() || '';
        const jobCompany = app.job?.company?.toLowerCase() || '';
        const status = app.status?.toLowerCase() || '';
        const notes = app.notes?.toLowerCase() || '';
        
        return (
          jobTitle.includes(lowerQuery) ||
          jobCompany.includes(lowerQuery) ||
          status.includes(lowerQuery) ||
          notes.includes(lowerQuery)
        );
      });
    },
    enabled: enabled && query.trim().length > 0,
    ...getCacheConfig('SEARCH'),
  });
}
