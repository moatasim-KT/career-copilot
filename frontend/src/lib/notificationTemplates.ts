/**
 * Notification Templates
 * Pre-defined templates for different notification types
 */

import {
  Briefcase,
  FileText,
  Calendar,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Info,
  Users,
  TrendingUp,
} from 'lucide-react';

import type { NotificationTemplate, NotificationCategory, NotificationPriority } from '@/types/notification';
import type { LucideIcon } from 'lucide-react';

/**
 * Category icon mapping
 */
export const categoryIcons: Record<NotificationCategory, LucideIcon> = {
  system: Info,
  job_alert: Briefcase,
  application: FileText,
  recommendation: Sparkles,
  social: Users,
};

/**
 * Category color mapping for badges
 */
export const categoryColors: Record<NotificationCategory, string> = {
  system: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  job_alert: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  application: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  recommendation: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  social: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300',
};

/**
 * Category labels
 */
export const categoryLabels: Record<NotificationCategory, string> = {
  system: 'System',
  job_alert: 'Job Alert',
  application: 'Application',
  recommendation: 'Recommendation',
  social: 'Social',
};

/**
 * Priority icon mapping
 */
export const priorityIcons: Record<NotificationPriority, LucideIcon> = {
  low: Info,
  normal: Info,
  high: AlertCircle,
  urgent: AlertCircle,
};

/**
 * Priority color mapping
 */
export const priorityColors: Record<NotificationPriority, string> = {
  low: 'text-neutral-500',
  normal: 'text-blue-500',
  high: 'text-orange-500',
  urgent: 'text-red-500',
};

/**
 * Template variable replacement
 */
export function interpolateTemplate(
  template: string,
  variables: Record<string, any>
): string {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    return variables[key]?.toString() || match;
  });
}

/**
 * Notification template definitions
 */
export const notificationTemplates = {
  // Job Alert Templates
  jobMatch: {
    type: 'job_match',
    title: 'New Job Match',
    description: 'New job: {jobTitle} at {company}',
    category: 'job_alert' as NotificationCategory,
    priority: 'high' as NotificationPriority,
    actionUrl: '/jobs/{jobId}',
    actionLabel: 'View Job',
  },

  jobSaved: {
    type: 'job_saved',
    title: 'Job Saved',
    description: 'You saved {jobTitle} at {company}',
    category: 'job_alert' as NotificationCategory,
    priority: 'low' as NotificationPriority,
    actionUrl: '/jobs/{jobId}',
    actionLabel: 'View Job',
  },

  jobExpiring: {
    type: 'job_expiring',
    title: 'Job Posting Expiring Soon',
    description: '{jobTitle} at {company} expires in {days} days',
    category: 'job_alert' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
    actionUrl: '/jobs/{jobId}',
    actionLabel: 'Apply Now',
  },

  // Application Templates
  applicationStatusChange: {
    type: 'application_status_change',
    title: 'Application Status Updated',
    description: 'Your application for {jobTitle} status changed to {status}',
    category: 'application' as NotificationCategory,
    priority: 'high' as NotificationPriority,
    actionUrl: '/applications/{applicationId}',
    actionLabel: 'View Application',
  },

  applicationSubmitted: {
    type: 'application_submitted',
    title: 'Application Submitted',
    description: 'Your application for {jobTitle} at {company} has been submitted',
    category: 'application' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
    actionUrl: '/applications/{applicationId}',
    actionLabel: 'View Application',
  },

  applicationRejected: {
    type: 'application_rejected',
    title: 'Application Update',
    description: 'Your application for {jobTitle} at {company} was not selected',
    category: 'application' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
    actionUrl: '/applications/{applicationId}',
    actionLabel: 'View Details',
  },

  applicationAccepted: {
    type: 'application_accepted',
    title: 'Congratulations!',
    description: 'Your application for {jobTitle} at {company} has been accepted',
    category: 'application' as NotificationCategory,
    priority: 'urgent' as NotificationPriority,
    actionUrl: '/applications/{applicationId}',
    actionLabel: 'View Offer',
  },

  // Interview Templates
  interviewScheduled: {
    type: 'interview_scheduled',
    title: 'Interview Scheduled',
    description: 'Interview scheduled for {jobTitle} on {date} at {time}',
    category: 'application' as NotificationCategory,
    priority: 'urgent' as NotificationPriority,
    actionUrl: '/applications/{applicationId}',
    actionLabel: 'View Details',
  },

  interviewReminder: {
    type: 'interview_reminder',
    title: 'Interview Reminder',
    description: 'Your interview for {jobTitle} is in {hours} hours',
    category: 'application' as NotificationCategory,
    priority: 'urgent' as NotificationPriority,
    actionUrl: '/applications/{applicationId}',
    actionLabel: 'Prepare Now',
  },

  interviewCompleted: {
    type: 'interview_completed',
    title: 'Interview Completed',
    description: 'You completed your interview for {jobTitle}. Good luck!',
    category: 'application' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
    actionUrl: '/applications/{applicationId}',
    actionLabel: 'Add Notes',
  },

  // Recommendation Templates
  newRecommendations: {
    type: 'new_recommendations',
    title: 'New Job Recommendations',
    description: 'We found {count} jobs matching your profile',
    category: 'recommendation' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
    actionUrl: '/recommendations',
    actionLabel: 'View Recommendations',
  },

  skillGapUpdate: {
    type: 'skill_gap_update',
    title: 'Skill Gap Analysis Updated',
    description: 'Your skill gap analysis has been refreshed with new insights',
    category: 'recommendation' as NotificationCategory,
    priority: 'low' as NotificationPriority,
    actionUrl: '/analytics',
    actionLabel: 'View Analysis',
  },

  profileStrengthUpdate: {
    type: 'profile_strength_update',
    title: 'Profile Strength Improved',
    description: 'Your profile strength increased to {percentage}%',
    category: 'recommendation' as NotificationCategory,
    priority: 'low' as NotificationPriority,
    actionUrl: '/profile',
    actionLabel: 'View Profile',
  },

  // System Templates
  systemMaintenance: {
    type: 'system_maintenance',
    title: 'Scheduled Maintenance',
    description: 'System maintenance scheduled for {date} at {time}',
    category: 'system' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
  },

  systemUpdate: {
    type: 'system_update',
    title: 'New Features Available',
    description: 'Check out the latest features and improvements',
    category: 'system' as NotificationCategory,
    priority: 'low' as NotificationPriority,
    actionUrl: '/changelog',
    actionLabel: 'Learn More',
  },

  systemError: {
    type: 'system_error',
    title: 'System Error',
    description: 'An error occurred: {errorMessage}',
    category: 'system' as NotificationCategory,
    priority: 'high' as NotificationPriority,
  },

  // Social Templates
  connectionRequest: {
    type: 'connection_request',
    title: 'New Connection Request',
    description: '{userName} wants to connect with you',
    category: 'social' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
    actionUrl: '/social/connections',
    actionLabel: 'View Request',
  },

  messageReceived: {
    type: 'message_received',
    title: 'New Message',
    description: 'You have a new message from {userName}',
    category: 'social' as NotificationCategory,
    priority: 'normal' as NotificationPriority,
    actionUrl: '/messages/{messageId}',
    actionLabel: 'Read Message',
  },
};

/**
 * Create a notification from a template
 */
export function createNotificationFromTemplate(
  templateKey: keyof typeof notificationTemplates,
  variables: Record<string, any>,
  overrides?: Partial<NotificationTemplate>
): NotificationTemplate {
  const template = notificationTemplates[templateKey];
  
  return {
    ...template,
    title: interpolateTemplate(template.title, variables),
    description: interpolateTemplate(template.description, variables),
    actionUrl: template.actionUrl 
      ? interpolateTemplate(template.actionUrl, variables)
      : undefined,
    ...overrides,
  };
}

/**
 * Get icon for notification category
 */
export function getCategoryIcon(category: NotificationCategory): LucideIcon {
  return categoryIcons[category];
}

/**
 * Get color class for notification category
 */
export function getCategoryColor(category: NotificationCategory): string {
  return categoryColors[category];
}

/**
 * Get label for notification category
 */
export function getCategoryLabel(category: NotificationCategory): string {
  return categoryLabels[category];
}

/**
 * Get icon for notification priority
 */
export function getPriorityIcon(priority: NotificationPriority): LucideIcon {
  return priorityIcons[priority];
}

/**
 * Get color class for notification priority
 */
export function getPriorityColor(priority: NotificationPriority): string {
  return priorityColors[priority];
}
