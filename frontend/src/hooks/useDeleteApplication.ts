import { useMutation, useQueryClient } from '@tanstack/react-query';

// Placeholder for API client
const deleteApplication = async (id: string) => {
  // Replace with actual API call
  return id;
};

export const useDeleteApplication = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteApplication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
};
