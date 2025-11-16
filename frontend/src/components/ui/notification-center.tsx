'use client';

import { Bell } from 'lucide-react';
import React from 'react';

import { Button } from '@/components/ui/Button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { useNotifications } from '@/contexts/NotificationContext';
import type { NotificationMessage } from '@/services/websocket'; function formatNotificationTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

function getNotificationMessage(notification: NotificationMessage): string {
    switch (notification.type) {
        case 'job_match_notification':
            return `New job match: ${notification.job_title} at ${notification.company} (${notification.match_score}% match)`;
        case 'application_status_update':
            return `Application status updated to: ${notification.status}`;
        case 'analytics_notification':
            return `Analytics update: ${notification.metric} = ${notification.value}`;
        case 'system_notification':
            return String(notification.message || 'System notification');
        default:
            return 'New notification';
    }
} function getNotificationLink(notification: NotificationMessage): string | null {
    switch (notification.type) {
        case 'job_match_notification':
            return `/jobs/${notification.job_id}`;
        case 'application_status_update':
            return `/applications/${notification.application_id}`;
        case 'analytics_notification':
            return '/analytics';
        default:
            return null;
    }
}

export function NotificationCenter() {
    const { notifications, clearNotifications, isConnected } = useNotifications();
    const unreadCount = notifications.length;

    const handleNotificationClick = (notification: NotificationMessage) => {
        const link = getNotificationLink(notification);
        if (link) {
            window.location.href = link;
        }
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="md" className="relative h-10 w-10">
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && (
                        <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                            {unreadCount > 9 ? '9+' : unreadCount}
                        </span>
                    )}
                    {!isConnected && (
                        <span className="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-gray-400" />
                    )}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
                <DropdownMenuLabel className="flex items-center justify-between">
                    <span>Notifications</span>
                    {unreadCount > 0 && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={clearNotifications}
                            className="h-auto p-1 text-xs"
                        >
                            Clear all
                        </Button>
                    )}
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                {notifications.length === 0 ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                        No notifications
                    </div>
                ) : (
                    <div className="max-h-96 overflow-y-auto">
                        {notifications.map((notification, index) => (
                            <DropdownMenuItem
                                key={`${notification.timestamp}-${index}`}
                                className="flex cursor-pointer flex-col items-start gap-1 p-3"
                                onClick={() => handleNotificationClick(notification)}
                            >
                                <p className="text-sm">{getNotificationMessage(notification)}</p>
                                <span className="text-xs text-muted-foreground">
                                    {formatNotificationTime(String(notification.timestamp))}
                                </span>
                            </DropdownMenuItem>
                        ))}
                    </div>
                )}
                {!isConnected && (
                    <>
                        <DropdownMenuSeparator />
                        <div className="p-2 text-center text-xs text-muted-foreground">
                            Disconnected - attempting to reconnect...
                        </div>
                    </>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
