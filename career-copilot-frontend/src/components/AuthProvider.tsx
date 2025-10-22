'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

interface AuthContextType {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

import { useNotification } from './NotificationProvider';

// ... (existing code)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setTokenState] = useState<string | null>(null);
  const router = useRouter();
  const { showNotification } = useNotification();

  useEffect(() => {
    const storedToken = Cookies.get('auth_token');
    if (storedToken) {
      setTokenState(storedToken);
    }
  }, []);

  const setToken = (newToken: string | null) => {
    setTokenState(newToken);
    if (newToken) {
      Cookies.set('auth_token', newToken, { expires: 7 }); // Store for 7 days
    } else {
      Cookies.remove('auth_token');
    }
  };

  const logout = () => {
    setToken(null);
    Cookies.remove('auth_token');
    router.push('/login');
  };

  useEffect(() => {
    if (token) {
      const ws = new WebSocket(`ws://localhost:8002/ws/${token}`);

      ws.onopen = () => {
        console.log('WebSocket connection established');
      };

      ws.onmessage = (event) => {
        console.log('WebSocket message received:', event.data);
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'job_match') {
            showNotification({
              message: `New Job Match: ${message.jobTitle} at ${message.company}! Apply here: ${message.link}`,
              type: 'success'
            });
          } else {
            showNotification({ message: message.message, type: message.type || 'info' });
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return () => {
        ws.close();
      };
    }
  }, [token, showNotification]);

  return (
    <AuthContext.Provider value={{ token, setToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
