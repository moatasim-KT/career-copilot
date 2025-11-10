/**
 * NotificationCenter Component
 * Dropdown panel showing recent notifications with bell icon in navigation
 */

'use client';

import {
  Bell,
  X,
  Check,
  ExternalLink,
  Clock,
  Trash2,
} from 'lucide-react';
import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import type { Notification, NotificationCategory } from '@/types/notification';
import {
  getCategoryIcon,
  getCategoryColor,
  getCategoryLabel,
} from '@/lib/notificationTemplates';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface NotificationCenterProps {
  className?: string;
}

// Mock notifications for demo - in production, this would come from API/state
const mockNotifications: Notification[] = [
  {
    id: '1',
    userId: '1',
    category: 'job_alert',
    title: 'New Job Match',
    description: 'Senior Frontend Developer at TechCorp matches your profile',
    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
    read: false,
    actionUrl: '/jobs/123',
    actionLabel: 'View Job',
    priority: 'high',
  },
  {
    id: '2',
    userId: '1',
    category: 'application',
    title: 'Application Status Updated',
    description: 'Your application for React Developer at StartupXYZ moved to Interview stage',
    timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
    read: false,
    actionUrl: '/applications/456',
    actionLabel: 'View Application',
    priority: 'high',
  },
  {
    id: '3',
    userId: '1',
    category: 'recommendation',
    title: 'New Job Recommendations',
    description: 'We found 12 jobs matching your profile',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    read: true,
    actionUrl: '/recommendations',
    actionLabel: 'View Recommendations',
    priority: 'normal',
  },
  {
    id: '4',
    userId: '1',
    category: 'application',
    title: 'Interview Scheduled',
    description: 'Interview for Full Stack Engineer at BigTech on Dec 15, 2024 at 2:00 PM',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5), // 5 hours ago
    read: true,
    actionUrl: '/applications/789',
    actionLabel: 'View Details',
    priority: 'urgent',
  },
  {
    id: '5',
    userId: '1',
    category: 'system',
    title: 'Profile Strength Improved',
    description: 'Your profile strength increased to 85%',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
    read: true,
    actionUrl: '/profile',
    actionLabel: 'View Profile',
    priority: 'low',
  },
];

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
  onDismiss: (id: string) => void;
  onClose: () => void;
}

function NotificationItem({
  notification,
  onMarkAsRead,
  onDismiss,
  onClose,
}: NotificationItemProps) {
  const CategoryIcon = getCategoryIcon(notification.category);
  const categoryColor = getCategoryColor(notification.category);

  const handleAction = () => {
    if (!notification.read) {
      onMarkAsRead(notification.id);
    }
    onClose();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={cn(
        'group relative p-4 border-b border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors',
        !notification.read && 'bg-primary-50/30 dark:bg-primary-900/10'
      )}
    >
      {/* Unread indicator */}
      {!notification.read && (
        <div className="absolute left-2 top-1/2 -translate-y-1/2 w-2 h-2 bg-primary-600 dark:bg-primary-400 rounded-full" />
      )}

      <div className="flex items-start gap-3 pl-3">
        {/* Category Icon */}
        <div className={cn(
          'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
          categoryColor
        )}>
          <CategoryIcon className="w-5 h-5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title and Category Badge */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 line-clamp-1">
              {notification.title}
            </h4>
            <span className={cn(
              'flex-shrink-0 text-xs px-2 py-0.5 rounded-full font-medium',
              categoryColor
            )}>
              {getCategoryLabel(notification.category)}
            </span>
          </div>

          {/* Description */}
          <p className="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2 mb-2">
            {notification.description}
          </p>

          {/* Timestamp and Actions */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1 text-xs text-neutral-500 dark:text-neutral-500">
              <Clock className="w-3 h-3" />
              <span>{formatDistanceToNow(notification.timestamp, { addSuffix: true })}</span>
            </div>

            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {/* Mark as read/unread */}
              {!notification.read && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onMarkAsRead(notification.id);
                  }}
                  className="p-1.5 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
                  title="Mark as read"
                >
                  <Check className="w-4 h-4" />
                </button>
              )}

              {/* Dismiss */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDismiss(notification.id);
                }}
                className="p-1.5 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                title="Dismiss"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Action Button */}
          {notification.actionUrl && notification.actionLabel && (
            <Link
              href={notification.actionUrl}
              onClick={handleAction}
              className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
            >
              {notification.actionLabel}
              <ExternalLink className="w-3 h-3" />
            </Link>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function NotificationCenter({ className }: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        buttonRef.current?.focus();
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  const handleMarkAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const handleDismiss = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const recentNotifications = notifications.slice(0, 20);

  return (
    <div className={cn('relative', className)}>
      {/* Bell Icon Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-md text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
        aria-label="Notifications"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <Bell className="w-5 h-5" />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </motion.span>
        )}
      </button>

      {/* Dropdown Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={dropdownRef}
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-96 max-w-[calc(100vw-2rem)] bg-white dark:bg-neutral-900 rounded-lg shadow-xl border border-neutral-200 dark:border-neutral-700 overflow-hidden z-50"
            role="dialog"
            aria-label="Notifications panel"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-700">
              <div>
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  Notifications
                </h3>
                {unreadCount > 0 && (
                  <p className="text-xs text-neutral-600 dark:text-neutral-400">
                    {unreadCount} unread
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    className="text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
                  >
                    Mark all read
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-400 transition-colors"
                  aria-label="Close notifications"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Notifications List */}
            <div className="max-h-[32rem] overflow-y-auto">
              {recentNotifications.length > 0 ? (
                <AnimatePresence mode="popLayout">
                  {recentNotifications.map(notification => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onMarkAsRead={handleMarkAsRead}
                      onDismiss={handleDismiss}
                      onClose={() => setIsOpen(false)}
                    />
                  ))}
                </AnimatePresence>
              ) : (
                <div className="p-8 text-center">
                  <Bell className="w-12 h-12 mx-auto mb-3 text-neutral-300 dark:text-neutral-600" />
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    No notifications yet
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            {recentNotifications.length > 0 && (
              <div className="p-3 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50">
                <Link
                  href="/notifications"
                  onClick={() => setIsOpen(false)}
                  className="block text-center text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
                >
                  View all notifications
                </Link>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
