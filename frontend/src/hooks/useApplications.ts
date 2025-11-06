import { useQuery } from '@tanstack/react-query';

// Placeholder for API client
const fetchApplications = async () => {
  // Replace with actual API call
  return [];
};

export const useApplications = () => {
  return useQuery({ queryKey: ['applications'], queryFn: fetchApplications });
};
