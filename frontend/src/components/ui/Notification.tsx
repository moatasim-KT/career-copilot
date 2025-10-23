
'use client';

import { useState, useEffect } from 'react';
import { webSocketService } from '@/lib/websocket';
import { Bell, X } from 'lucide-react';

interface Notification {
  id: string;
  message: string;
}

export default function Notification() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      webSocketService.connect(token);
    }

    webSocketService.on('notification', (data: Notification) => {
      setNotifications(prev => [...prev, data]);
    });

    return () => {
      webSocketService.disconnect();
    };
  }, []);

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <div className="fixed top-20 right-5 z-50">
      {notifications.map(notification => (
        <div key={notification.id} className="bg-white shadow-lg rounded-lg p-4 mb-4 flex items-start">
          <div className="flex-shrink-0">
            <Bell className="h-6 w-6 text-blue-500" />
          </div>
          <div className="ml-3 w-0 flex-1 pt-0.5">
            <p className="text-sm font-medium text-gray-900">New Notification</p>
            <p className="mt-1 text-sm text-gray-500">{notification.message}</p>
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              onClick={() => removeNotification(notification.id)}
              className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <span className="sr-only">Close</span>
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
