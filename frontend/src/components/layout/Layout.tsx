'use client';

import { ReactNode, useEffect } from 'react';
import { toast } from 'sonner';

import NotificationSystem from '@/components/notifications/NotificationSystem';
import { webSocketService } from '@/lib/api/websocket';

import Footer from './Footer';
import Navigation from './Navigation';

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  useEffect(() => {
    const handleJobRecommendation = (data: any) => {
      toast.success(`New Job Recommendation: ${data.job.title} at ${data.job.company.name}`);
      // TODO: Update jobs list in real-time
      // TODO: Add a badge on the Jobs tab
    };

    const handleApplicationStatusChange = (data: any) => {
      toast.info(`Application for ${data.application.job_title} at ${data.application.company_name} changed to ${data.application.status}`);
      // TODO: Update application status in the UI instantly
      // TODO: Update dashboard stats in real-time
      // TODO: Add a badge animation for status changes
    };

    const handleNewNotification = (data: any) => {
      toast.success(`New Notification: ${data.message}`);
      // TODO: Update the notification bell badge count
      // TODO: Add new notifications to the notification center list
      // TODO: Implement sound playback based on user preferences
    };

    webSocketService.on('job:recommendation', handleJobRecommendation);
    webSocketService.on('application:status_change', handleApplicationStatusChange);
    webSocketService.on('notification:new', handleNewNotification);
    webSocketService.on('reconnecting', (data) => {
      toast.loading(`Reconnecting to WebSocket... Attempt ${data.reconnectAttempts}`, { id: 'reconnecting' });
    });
    webSocketService.on('connected', () => {
      toast.success('WebSocket reconnected!', { id: 'reconnecting' });
    });

    const handleOnline = () => {
      toast.success('Network reconnected!');
      webSocketService.reconnect();
    };

    const handleOffline = () => {
      toast.error('Network disconnected. Attempting to reconnect...');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      webSocketService.off('job:recommendation', handleJobRecommendation);
      webSocketService.off('application:status_change', handleApplicationStatusChange);
      webSocketService.off('notification:new', handleNewNotification);
      webSocketService.off('reconnecting', () => { }); // Remove dummy listener
      webSocketService.off('connected', () => { }); // Remove dummy listener
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-neutral-950">
      <NotificationSystem />
      <Navigation />
      <main className="flex-1 container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8 max-w-7xl">
        <div className="w-full">
          {children}
        </div>
      </main>
      <Footer />
    </div>
  );
}