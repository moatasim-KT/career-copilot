import { create } from 'zustand';

interface UIState {
  isModalOpen: boolean;
  modalContent: React.ReactNode | null;
  isDrawerOpen: boolean;
  openModal: (content: React.ReactNode) => void;
  closeModal: () => void;
  toggleDrawer: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isModalOpen: false,
  modalContent: null,
  isDrawerOpen: false,
  openModal: (content) => set({ isModalOpen: true, modalContent: content }),
  closeModal: () => set({ isModalOpen: false, modalContent: null }),
  toggleDrawer: () => set((state) => ({ isDrawerOpen: !state.isDrawerOpen })),
}));
