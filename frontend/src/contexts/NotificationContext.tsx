'use client';

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { toast } from 'sonner';

import type {
    ApplicationStatusNotification,
    JobMatchNotification,
    NotificationMessage,
    SystemNotification,
} from '@/services/websocket';
import { webSocketClient } from '@/services/websocket';

import { useAuth } from './AuthContext';

interface NotificationContextType {
    isConnected: boolean;
    notifications: NotificationMessage[];
    clearNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
    const { user, isAuthenticated } = useAuth();
    const [isConnected, setIsConnected] = useState(false);
    const [notifications, setNotifications] = useState<NotificationMessage[]>([]);

    // Connect to WebSocket when user is authenticated
    useEffect(() => {
        if (!isAuthenticated || !user) {
            if (webSocketClient.isConnected) {
                webSocketClient.disconnect();
                setIsConnected(false);
            }
            return;
        }

        const token = localStorage.getItem('access_token');
        if (!token) return;

        // Connect to WebSocket
        webSocketClient
            .connect(user.id, token)
            .then(() => {
                setIsConnected(true);
                console.log('WebSocket connected for user:', user.id);

                // Subscribe to default channels
                webSocketClient.subscribeToChannel(`user_${user.id}`);
                webSocketClient.subscribeToChannel('job_matches');
                webSocketClient.subscribeToChannel('system_updates');
            })
            .catch((error) => {
                console.error('Failed to connect WebSocket:', error);
                setIsConnected(false);
            });

        return () => {
            webSocketClient.disconnect();
            setIsConnected(false);
        };
    }, [isAuthenticated, user]);

    // Handle notifications
    useEffect(() => {
        if (!isConnected) return;

        // Job match notifications
        const unsubscribeJobMatch = webSocketClient.subscribe('job_match_notification', (message) => {
            const notification = message as unknown as JobMatchNotification;
            setNotifications((prev) => [notification, ...prev].slice(0, 50)); // Keep last 50

            toast.success(`New Job Match: ${notification.job_title}`, {
                description: `${notification.company} - ${notification.match_score}% match`,
                action: {
                    label: 'View',
                    onClick: () => (window.location.href = `/jobs/${notification.job_id}`),
                },
            });
        });    // Application status updates
        const unsubscribeAppStatus = webSocketClient.subscribe('application_status_update', (message) => {
            const notification = message as unknown as ApplicationStatusNotification;
            setNotifications((prev) => [notification, ...prev].slice(0, 50));

            toast.info('Application Status Updated', {
                description: `Status changed to: ${notification.status}`,
                action: {
                    label: 'View',
                    onClick: () => (window.location.href = `/applications/${notification.application_id}`),
                },
            });
        });    // System notifications
        const unsubscribeSystem = webSocketClient.subscribe('system_notification', (message) => {
            const notification = message as unknown as SystemNotification;
            setNotifications((prev) => [notification, ...prev].slice(0, 50));

            const toastFn =
                {
                    info: toast.info,
                    warning: toast.warning,
                    error: toast.error,
                }[notification.notification_type] || toast.info;

            toastFn(notification.message);
        });        // Pong handler (keep-alive)
        const unsubscribePong = webSocketClient.subscribe('pong', () => {
            // Connection is alive
        });

        return () => {
            unsubscribeJobMatch();
            unsubscribeAppStatus();
            unsubscribeSystem();
            unsubscribePong();
        };
    }, [isConnected]);

    const clearNotifications = useCallback(() => {
        setNotifications([]);
    }, []);

    const value: NotificationContextType = {
        isConnected,
        notifications,
        clearNotifications,
    };

    return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications() {
    const context = useContext(NotificationContext);
    if (context === undefined) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
}
