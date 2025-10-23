'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import type { AnalyticsSummary } from '@/lib/api';
import Navigation from '@/components/Navigation';
import Dashboard from '@/components/Dashboard';
import JobsPage from '@/components/JobsPage';
import ApplicationsPage from '@/components/ApplicationsPage';
import ProfilePage from '@/components/ProfilePage';
import RecommendationsPage from '@/components/RecommendationsPage';
import AnalyticsPage from '@/components/AnalyticsPage';
import LoginForm from '@/components/LoginForm';

type PageType = 'dashboard' | 'jobs' | 'applications' | 'profile' | 'recommendations' | 'analytics';

export default function Home() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Check if user is authenticated (simplified for now)
    const token = localStorage.getItem('auth_token');
    if (token) {
      apiClient.setToken(token);
      setIsAuthenticated(true);
      // You could also fetch user profile here
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (token: string, userData: any) => {
    localStorage.setItem('auth_token', token);
    apiClient.setToken(token);
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    apiClient.clearToken();
    setIsAuthenticated(false);
    setUser(null);
    setCurrentPage('dashboard');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm onLogin={handleLogin} />;
  }

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'jobs':
        return <JobsPage />;
      case 'applications':
        return <ApplicationsPage />;
      case 'profile':
        return <ProfilePage />;
      case 'recommendations':
        return <RecommendationsPage />;
      case 'analytics':
        return <AnalyticsPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation 
        currentPage={currentPage} 
        onPageChange={setCurrentPage}
        user={user}
        onLogout={handleLogout}
      />
      <main className="container mx-auto px-4 py-8">
        {renderCurrentPage()}
      </main>
    </div>
  );
}
