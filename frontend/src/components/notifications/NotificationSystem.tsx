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

import { webSocketService } from '@/lib/api/websocket';
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
          <div className="shrink-0">
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
          <div className="ml-4 shrink-0 flex">
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
  const [statusBarDismissed, setStatusBarDismissed] = useState(() => {
    // Check if status bar was permanently dismissed
    if (typeof window !== 'undefined') {
      return localStorage.getItem('connection-status-dismissed') === 'true';
    }
    return false;
  });

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

  const handleDismissStatusBar = () => {
    setStatusBarDismissed(true);
    if (typeof window !== 'undefined') {
      localStorage.setItem('connection-status-dismissed', 'true');
    }
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

      // Removed connection_established - it's a state not an event

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

  // Use singleton webSocketService instead of creating a new connection
  const [connectionStatus, setConnectionStatus] = useState('closed');

  useEffect(() => {
    const handleStatusChange = (status: string) => {
      setConnectionStatus(status);
    };

    const handleNotificationEvent = (data: any) => {
      handleWebSocketMessage(data);
    };

    // Initial status
    // @ts-ignore - accessing private property for initial state if needed, or just assume closed/connecting
    // Better to rely on events

    // Subscribe to service events
    const onConnected = () => handleStatusChange('open');
    const onDisconnected = () => handleStatusChange('closed');
    const onReconnecting = () => handleStatusChange('connecting');

    const onNotificationNew = (data: any) => handleNotificationEvent({ type: 'system_notification', ...data });
    const onJobMatch = (data: any) => handleNotificationEvent({ type: 'job_match', ...data });
    const onApplicationStatus = (data: any) => handleNotificationEvent({ type: 'application_status_update', ...data });
    const onAnalyticsUpdate = (data: any) => handleNotificationEvent({ type: 'analytics_update', ...data });

    webSocketService.on('connected', onConnected);
    webSocketService.on('disconnected', onDisconnected);
    webSocketService.on('reconnecting', onReconnecting);

    webSocketService.on('notification:new', onNotificationNew);
    webSocketService.on('job:match', onJobMatch);
    webSocketService.on('application:status', onApplicationStatus);
    webSocketService.on('analytics:update', onAnalyticsUpdate);

    return () => {
      webSocketService.off('connected', onConnected);
      webSocketService.off('disconnected', onDisconnected);
      webSocketService.off('reconnecting', onReconnecting);

      webSocketService.off('notification:new', onNotificationNew);
      webSocketService.off('job:match', onJobMatch);
      webSocketService.off('application:status', onApplicationStatus);
      webSocketService.off('analytics:update', onAnalyticsUpdate);
    };
  }, []);

  const connected = connectionStatus === 'open';
  const connecting = connectionStatus === 'connecting';
  const disconnected = connectionStatus === 'closed' && !connecting;

  // Show connection status in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      logger.log('WebSocket status:', { connected, connecting, connectionStatus });
    }
  }, [connected, connecting, connectionStatus]);

  // Automatic reconnection is handled by useWebSocket hook
  // No need for explicit toasts for connection state changes

  return (
    <>
      {/* Connection Status Bar - Only show when disconnected and not dismissed */}
      {disconnected && !statusBarDismissed && (
        <div className="fixed top-0 left-0 right-0 z-40 bg-amber-50 border-b border-amber-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-12">
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <span className="text-sm font-medium text-amber-900">
                  Real-time updates are temporarily unavailable. Reconnecting automatically...
                </span>
              </div>
              <button
                onClick={handleDismissStatusBar}
                className="inline-flex items-center text-amber-900 hover:text-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500 rounded-md p-1"
                aria-label="Dismiss status bar"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notification Container - Bottom Right */}
      <div
        aria-live="assertive"
        className="fixed bottom-0 right-0 flex flex-col-reverse items-end px-4 py-6 pointer-events-none sm:p-6 z-50 space-y-4 space-y-reverse"
      >
        {notifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onClose={removeNotification}
          />
        ))}
      </div>
    </>
  );
}