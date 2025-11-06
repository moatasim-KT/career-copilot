import { useMutation, useQueryClient } from '@tanstack/react-query';

// Placeholder for API client
const deleteJob = async (id: string) => {
  // Replace with actual API call
  return id;
};

export const useDeleteJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
