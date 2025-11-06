import { useMutation, useQueryClient } from '@tanstack/react-query';

// Placeholder for API client
const addApplication = async (newApplication: any) => {
  // Replace with actual API call
  return { id: String(Date.now()), ...newApplication };
};

export const useAddApplication = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: addApplication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
};
