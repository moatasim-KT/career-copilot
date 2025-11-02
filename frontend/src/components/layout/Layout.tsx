'use client';

import { ReactNode } from 'react';

import NotificationSystem from '@/components/notifications/NotificationSystem';
import { useAuth } from '@/contexts/AuthContext';

import Footer from './Footer';
import Navigation from './Navigation';

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <NotificationSystem />
      <Navigation
        user={user ? {
          username: user.username,
          id: user.id.toString(),
          email: user.email,
        } : undefined}
        onLogout={logout}
      />
      <main className="flex-1 container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
}