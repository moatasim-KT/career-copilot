
import { Home, Briefcase, FileText, Settings } from 'lucide-react';

export const commandCategories = [
  {
    name: 'Navigation',
    commands: [
      {
        id: 'home',
        label: 'Go to Dashboard',
        action: () => {
          window.location.href = '/';
        },
        icon: Home,
        keywords: ['home', 'dashboard', 'main'],
      },
      {
        id: 'jobs',
        label: 'Go to Jobs',
        action: () => {
          window.location.href = '/jobs';
        },
        icon: Briefcase,
        keywords: ['jobs', 'opportunities', 'search'],
      },
      {
        id: 'applications',
        label: 'Go to Applications',
        action: () => {
          window.location.href = '/applications';
        },
        icon: FileText,
        keywords: ['applications', 'applied', 'tracker'],
      },
    ],
  },
  {
    name: 'Settings',
    commands: [
      {
        id: 'settings',
        label: 'Open Settings',
        action: () => {
          window.location.href = '/settings';
        },
        icon: Settings,
        keywords: ['settings', 'preferences', 'account'],
      },
    ],
  },
];
