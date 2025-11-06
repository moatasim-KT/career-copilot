import { create } from 'zustand';

interface Job {
  id: string;
  title: string;
  company: string;
  status: string;
  // Add other job properties as needed
}

interface JobsState {
  jobs: Job[];
  filters: Record<string, any>;
  sortBy: string;
  pagination: { currentPage: number; totalPages: number };
  isLoading: boolean;
  error: string | null;
  setJobs: (jobs: Job[]) => void;
  addJob: (job: Job) => void;
  updateJob: (job: Job) => void;
  deleteJob: (id: string) => void;
  setFilters: (filters: Record<string, any>) => void;
  setSortBy: (sortBy: string) => void;
  setPagination: (pagination: { currentPage: number; totalPages: number }) => void;
}

export const useJobsStore = create<JobsState>((set) => ({
  jobs: [],
  filters: {},
  sortBy: 'datePosted',
  pagination: { currentPage: 1, totalPages: 1 },
  isLoading: false,
  error: null,
  setJobs: (jobs) => set({ jobs }),
  addJob: (job) => set((state) => ({ jobs: [...state.jobs, job] })),
  updateJob: (updatedJob) =>
    set((state) => ({
      jobs: state.jobs.map((job) => (job.id === updatedJob.id ? updatedJob : job)),
    })),
  deleteJob: (id) => set((state) => ({ jobs: state.jobs.filter((job) => job.id !== id) })),
  setFilters: (filters) => set({ filters }),
  setSortBy: (sortBy) => set({ sortBy }),
  setPagination: (pagination) => set({ pagination }),
}));