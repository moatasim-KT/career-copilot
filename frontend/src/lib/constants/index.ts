// Application-wide constants

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000';

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',
  JOBS: '/jobs',
  APPLICATIONS: '/applications',
  ANALYTICS: '/analytics',
  RECOMMENDATIONS: '/recommendations',
  INTERVIEW_PRACTICE: '/interview-practice',
  CONTENT_GENERATION: '/content-generation',
  ADVANCED_FEATURES: '/advanced-features',
} as const;

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
  },
  USER: {
    PROFILE: '/user/profile',
    SETTINGS: '/user/settings',
  },
  JOBS: {
    LIST: '/jobs',
    SEARCH: '/jobs/search',
    APPLY: '/jobs/apply',
  },
  ANALYTICS: {
    DASHBOARD: '/analytics/dashboard',
    REPORTS: '/analytics/reports',
  },
} as const;