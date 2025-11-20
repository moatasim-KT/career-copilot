/**
 * Real-time notification system component
 * Displays toast notifications for WebSocket events
 */

'use client';

import {
  CheckCircle,
  AlertCircle,
  Info,
  X,
  Briefcase,
  TrendingUp,
  Bell,
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

import { useWebSocket } from '@/hooks/useWebSocket';
import { logger } from '@/lib/logger';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning' | 'job_match' | 'application_update';
  title: string;
  message: string;
  timestamp: Date;
  autoHide?: boolean;
  duration?: number;
  data?: any;
}

interface NotificationItemProps {
  notification: Notification;
  onClose: (id: string) => void;
}

function NotificationItem({ notification, onClose }: NotificationItemProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (notification.autoHide !== false) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose(notification.id), 300);
      }, notification.duration || 5000);

      return () => clearTimeout(timer);
    }
  }, [notification, onClose]);

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'job_match':
        return <Briefcase className="h-5 w-5 text-blue-500" />;
      case 'application_update':
        return <TrendingUp className="h-5 w-5 text-purple-500" />;
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'job_match':
        return 'bg-blue-50 border-blue-200';
      case 'application_update':
        return 'bg-purple-50 border-purple-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <div
      className={`
        transform transition-all duration-300 ease-in-out
        ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
        max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto border
        ${getBackgroundColor()}
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="ml-3 w-0 flex-1">
            <p className="text-sm font-medium text-gray-900">
              {notification.title}
            </p>
            <p className="mt-1 text-sm text-gray-600">
              {notification.message}
            </p>
            {notification.data && notification.type === 'job_match' && (
              <div className="mt-2 text-xs text-gray-500">
                <p>Match Score: {notification.data.match_score?.toFixed(1)}%</p>
                <p>Company: {notification.data.job?.company}</p>
              </div>
            )}
            <p className="mt-1 text-xs text-gray-400">
              {notification.timestamp.toLocaleTimeString()}
            </p>
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              onClick={() => onClose(notification.id)}
            >
              <span className="sr-only">Close</span>
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function NotificationSystem() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };

    setNotifications(prev => [newNotification, ...prev.slice(0, 4)]); // Keep max 5 notifications
  }, []);

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const handleWebSocketMessage = (message: { type?: string;[key: string]: any }) => {
    switch (message.type) {
      case 'job_match':
        addNotification({
          type: 'job_match',
          title: 'New Job Match!',
          message: message.message || 'A new job matches your profile',
          data: message,
          autoHide: false, // Keep job matches visible until manually closed
        });
        break;

      case 'application_status_update':
        addNotification({
          type: 'application_update',
          title: 'Application Updated',
          message: message.message || 'Your application status has been updated',
          data: message,
        });
        break;

      case 'analytics_update':
        addNotification({
          type: 'info',
          title: 'Analytics Updated',
          message: 'Your dashboard analytics have been refreshed',
          duration: 3000,
        });
        break;

      case 'system_notification':
        addNotification({
          type: message.notification_type === 'error' ? 'error' :
            message.notification_type === 'warning' ? 'warning' : 'info',
          title: 'System Notification',
          message: message.message || 'System update',
          autoHide: message.notification_type !== 'error',
        });
        break;

      case 'skill_gap_update':
        addNotification({
          type: 'info',
          title: 'Skill Analysis Updated',
          message: 'Your skill gap analysis has been refreshed',
          duration: 4000,
        });
        break;

      case 'connection_established':
        addNotification({
          type: 'success',
          title: 'Connected',
          message: 'Real-time updates are now active',
          duration: 2000,
        });
        break;

      default:
        // Handle unknown message types
        if (message.message) {
          addNotification({
            type: 'info',
            title: 'Update',
            message: message.message,
            duration: 4000,
          });
        }
        break;
    }
  };

  // Set up WebSocket connection and message handling
  const [wsUrl] = useState(() => {
    if (process.env.NEXT_PUBLIC_WS_URL) {
      return process.env.NEXT_PUBLIC_WS_URL + '/ws';
    }
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return apiUrl.replace(/^http/, 'ws') + '/ws';
  });

  const { connectionStatus } = useWebSocket(
    wsUrl,
    (data) => {
      // Handle dashboard updates if needed
      handleWebSocketMessage({ type: 'dashboard-update', ...data });
    },
    (data) => {
      // Handle application status updates
      handleWebSocketMessage({ type: 'application-status-update', ...data });
    },
    (data) => {
      // Handle analytics updates
      handleWebSocketMessage({ type: 'analytics-update', ...data });
    },
  );

  const connected = connectionStatus === 'open';
  const connecting = connectionStatus === 'connecting';

  // Show connection status in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      logger.log('WebSocket status:', { connected, connecting, connectionStatus });
    }
  }, [connected, connecting, connectionStatus]);

  // Show connection status when it changes
  useEffect(() => {
    if (connected) {
      addNotification({
        type: 'success',
        title: 'Connected',
        message: 'Real-time updates are now active',
        duration: 2000,
      });
    } else if (connectionStatus === 'closed' && !connecting) {
      addNotification({
        type: 'warning',
        title: 'Disconnected',
        message: 'Real-time updates are temporarily unavailable',
        autoHide: false,
      });
    }
  }, [connectionStatus, connected, connecting, addNotification]);

  return (
    <>
      {/* Connection Status Indicator (only show when there are issues) */}
      {connecting && (
        <div className="fixed top-4 left-4 z-50">
          <div className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium bg-yellow-100 text-yellow-800">
            <Bell className="h-4 w-4" />
            <span>Connecting...</span>
          </div>
        </div>
      )}

      {/* Notification Container */}
      <div
        aria-live="assertive"
        className="fixed inset-0 flex items-end px-4 py-6 pointer-events-none sm:p-6 sm:items-start z-50"
      >
        <div className="w-full flex flex-col items-center space-y-4 sm:items-end">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onClose={removeNotification}
            />
          ))}
        </div>
      </div>
    </>
  );
}