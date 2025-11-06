import { useMutation, useQueryClient } from '@tanstack/react-query';

// Placeholder for API client
const updateJob = async (updatedJob: any) => {
  // Replace with actual API call
  return updatedJob;
};

export const useUpdateJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateJob,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      // Optionally, update a single job in the cache
      queryClient.setQueryData(['job', data.id], data);
    },
  });
};
