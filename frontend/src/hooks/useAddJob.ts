import { useMutation, useQueryClient } from '@tanstack/react-query';

// Placeholder for API client
const addJob = async (newJob: any) => {
  // Replace with actual API call
  return { id: String(Date.now()), ...newJob };
};

export const useAddJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: addJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
