import { create } from 'zustand';

interface AnalyticsState {
  pageViews: number;
  events: { name: string; timestamp: number; data?: any }[];
  addPageView: () => void;
  addEvent: (name: string, data?: any) => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  pageViews: 0,
  events: [],
  addPageView: () => set((state) => ({ pageViews: state.pageViews + 1 })),
  addEvent: (name, data) =>
    set((state) => ({
      events: [...state.events, { name, timestamp: Date.now(), data }],
    })),
}));
