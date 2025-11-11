/**
 * Application types and interfaces
 * Re-export from API types for consistency
 */

import { Application as APIApplication } from '@/lib/api/api';

export type ApplicationStatus =
  | 'interested'
  | 'applied'
  | 'interview'
  | 'offer'
  | 'accepted'
  | 'rejected'
  | 'declined';

// Use the API Application type
export type Application = APIApplication;

export interface KanbanColumn {
  id: ApplicationStatus;
  title: string;
  applications: Application[];
  color: string;
}

export const KANBAN_COLUMNS: Omit<KanbanColumn, 'applications'>[] = [
  {
    id: 'applied',
    title: 'Applied',
    color: 'blue',
  },
  {
    id: 'interview',
    title: 'Interviewing',
    color: 'purple',
  },
  {
    id: 'offer',
    title: 'Offer',
    color: 'green',
  },
  {
    id: 'rejected',
    title: 'Rejected',
    color: 'red',
  },
];
