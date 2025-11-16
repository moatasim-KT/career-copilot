/**
 * User Profile Hook
 * 
 * Manages user profile data with optimized caching (30 min stale time, refetch on focus).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { apiClient, type UserProfile } from '@/lib/api/api';
import { logger } from '@/lib/logger';
import { queryKeys, getCacheConfig } from '@/lib/queryClient';

/**
 * Hook to fetch user profile
 */
export function useUserProfile(enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.userProfile.current(),
    queryFn: async () => {
      const response = await apiClient.getUserProfile();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    enabled,
    ...getCacheConfig('USER_PROFILE'),
  });
}

/**
 * Hook to update user profile
 */
export function useUpdateUserProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (profileData: Partial<UserProfile>) => {
      const response = await apiClient.updateUserProfile(profileData);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    onMutate: async (newProfile) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.userProfile.current() });
      
      // Snapshot previous value
      const previousProfile = queryClient.getQueryData(queryKeys.userProfile.current());
      
      // Optimistically update
      queryClient.setQueryData(queryKeys.userProfile.current(), (old: UserProfile | undefined) => {
        if (!old) return old;
        return { ...old, ...newProfile };
      });
      
      return { previousProfile };
    },
    onError: (err, newProfile, context) => {
      // Rollback on error
      if (context?.previousProfile) {
        queryClient.setQueryData(queryKeys.userProfile.current(), context.previousProfile);
      }
      logger.error('Failed to update user profile:', err);
    },
    onSuccess: (data) => {
      // Update cache with server response
      queryClient.setQueryData(queryKeys.userProfile.current(), data);
      logger.info('User profile updated successfully');
    },
  });
}
