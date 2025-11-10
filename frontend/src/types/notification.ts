/**
 * Notification System Types
 * Comprehensive type definitions for the notification system
 */

import type { LucideIcon } from 'lucide-react';

/**
 * Notification categories
 */
export type NotificationCategory = 
  | 'system' 
  | 'job_alert' 
  | 'application' 
  | 'recommendation' 
  | 'social';

/**
 * Notification priority levels
 */
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';

/**
 * Main Notification interface
 */
export interface Notification {
  id: string;
  userId: string;
  category: NotificationCategory;
  title: string;
  description: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
  icon?: LucideIcon;
  priority?: NotificationPriority;
  metadata?: Record<string, any>;
  expiresAt?: Date;
}

/**
 * Notification preferences per category
 */
export interface NotificationPreference {
  category: NotificationCategory;
  enabled: boolean;
  emailEnabled: boolean;
  emailFrequency: 'immediate' | 'daily' | 'weekly' | 'off';
  pushEnabled: boolean;
  soundEnabled: boolean;
  vibrationEnabled?: boolean;
}

/**
 * User notification settings
 */
export interface NotificationSettings {
  userId: string;
  preferences: NotificationPreference[];
  doNotDisturb?: {
    enabled: boolean;
    startTime: string; // HH:mm format
    endTime: string; // HH:mm format
    days: number[]; // 0-6, Sunday-Saturday
  };
  globalMute: boolean;
}

/**
 * Notification template data
 */
export interface NotificationTemplate {
  type: string;
  title: string;
  description: string;
  category: NotificationCategory;
  priority: NotificationPriority;
  actionUrl?: string;
  actionLabel?: string;
}

/**
 * Notification action types
 */
export type NotificationAction = 
  | 'view'
  | 'dismiss'
  | 'snooze'
  | 'mark_read'
  | 'mark_unread'
  | 'delete';

/**
 * Notification filter options
 */
export interface NotificationFilter {
  categories?: NotificationCategory[];
  read?: boolean;
  priority?: NotificationPriority[];
  dateFrom?: Date;
  dateTo?: Date;
  searchQuery?: string;
}

/**
 * Notification statistics
 */
export interface NotificationStats {
  total: number;
  unread: number;
  byCategory: Record<NotificationCategory, number>;
  byPriority: Record<NotificationPriority, number>;
}

/**
 * Push notification subscription
 */
export interface PushSubscription {
  userId: string;
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
  createdAt: Date;
  lastUsed?: Date;
}

/**
 * Notification event for real-time updates
 */
export interface NotificationEvent {
  type: 'new' | 'update' | 'delete' | 'mark_read' | 'mark_unread';
  notification: Notification;
  timestamp: Date;
}
