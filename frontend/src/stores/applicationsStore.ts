import { create } from 'zustand';

interface Application {
  id: string;
  jobId: string;
  status: string;
  // Add other application properties as needed
}

interface ApplicationsState {
  applications: Application[];
  isLoading: boolean;
  error: string | null;
  setApplications: (applications: Application[]) => void;
  addApplication: (application: Application) => void;
  updateApplication: (application: Application) => void;
  deleteApplication: (id: string) => void;
}

export const useApplicationsStore = create<ApplicationsState>((set) => ({
  applications: [],
  isLoading: false,
  error: null,
  setApplications: (applications) => set({ applications }),
  addApplication: (application) => set((state) => ({ applications: [...state.applications, application] })),
  updateApplication: (updatedApplication) =>
    set((state) => ({
      applications: state.applications.map((application) =>
        application.id === updatedApplication.id ? updatedApplication : application,
      ),
    })),
  deleteApplication: (id) =>
    set((state) => ({ applications: state.applications.filter((application) => application.id !== id) })),
}));