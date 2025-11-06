import { useMutation, useQueryClient } from '@tanstack/react-query';

// Placeholder for API client
const updateApplication = async (updatedApplication: any) => {
  // Replace with actual API call
  return updatedApplication;
};

export const useUpdateApplication = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateApplication,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      // Optionally, update a single application in the cache
      queryClient.setQueryData(['application', data.id], data);
    },
  });
};
