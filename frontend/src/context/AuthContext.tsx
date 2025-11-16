
import React, { createContext, useState, useEffect, ReactNode } from 'react';

import apiClient from '@/lib/api/client';

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string, username: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
  register: async () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkUser = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        const response = await apiClient.auth.me();
        if (response.data) {
          setUser(response.data);
        }
      }
      setLoading(false);
    };
    checkUser();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.auth.login(email, password);
    if (response.data) {
      localStorage.setItem('auth_token', response.data.access_token);
      const meResponse = await apiClient.auth.me();
      if (meResponse.data) {
        setUser(meResponse.data);
      }
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  const register = async (email: string, password: string, username: string) => {
    const response = await apiClient.auth.register(email, password, username);
    if (response.data) {
        // Automatically log in the user after registration
        await login(email, password);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};
