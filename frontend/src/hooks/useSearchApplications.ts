/**
 * Search Applications Hook
 * 
 * Provides search functionality for applications with React Query.
 */

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api/api';

export function useSearchApplications(query: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['applications', 'search', query],
    queryFn: async () => {
      if (!query || query.trim().length === 0) {
        return [];
      }
      const response = await apiClient.searchApplications(query.trim(), 10);
      
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
    staleTime: 30000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
  });
}
