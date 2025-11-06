import { useQuery } from '@tanstack/react-query';

// Placeholder for API client
const fetchJobs = async () => {
  // Replace with actual API call
  return [];
};

export const useJobs = () => {
  return useQuery({ queryKey: ['jobs'], queryFn: fetchJobs });
};
