'use client';

import { useRouter } from 'next/navigation';
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';

import { fetchApi } from '@/lib/api/client';

interface User {
    id: number;
    email: string;
    username: string;
    full_name?: string;
    skills?: string[];
    preferred_locations?: string[];
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (identifier: string, password: string) => Promise<void>;
    register: (username: string, email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    // Load user from token on mount
    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem('access_token');
            const storedUser = localStorage.getItem('user');

            if (token && storedUser) {
                try {
                    // Verify token is still valid by fetching current user
                    const response = await fetchApi<User>('/auth/me', {
                        requiresAuth: true,
                    });

                    if (response.data) {
                        setUser(response.data);
                    } else {
                        // Token invalid, clear storage
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('user');
                    }
                } catch (error) {
                    console.error('Auth initialization error:', error);
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('user');
                }
            }

            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = useCallback(
        async (identifier: string, password: string) => {
            const isEmail = identifier.includes('@');
            const loginPayload = {
                [isEmail ? 'email' : 'username']: identifier,
                password,
            };

            const response = await fetchApi<{
                access_token: string;
                token_type: string;
                user: User;
            }>('/auth/login', {
                method: 'POST',
                body: JSON.stringify(loginPayload),
                requiresAuth: false,
            });

            if (response.error) {
                throw new Error(response.error || 'Login failed');
            }

            if (response.data) {
                localStorage.setItem('access_token', response.data.access_token);
                localStorage.setItem('user', JSON.stringify(response.data.user));
                setUser(response.data.user);
                router.push('/dashboard');
            }
        },
        [router],
    );

    const register = useCallback(
        async (username: string, email: string, password: string) => {
            const response = await fetchApi<{
                access_token: string;
                token_type: string;
                user: User;
            }>('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ username, email, password }),
                requiresAuth: false,
            });

            if (response.error) {
                throw new Error(response.error || 'Registration failed');
            }

            if (response.data) {
                localStorage.setItem('access_token', response.data.access_token);
                localStorage.setItem('user', JSON.stringify(response.data.user));
                setUser(response.data.user);
                router.push('/dashboard');
            }
        },
        [router],
    );

    const logout = useCallback(async () => {
        try {
            // Call logout endpoint (for server-side cleanup if needed)
            await fetchApi('/auth/logout', {
                method: 'POST',
                requiresAuth: true,
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage regardless of API call success
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            setUser(null);
            router.push('/login');
        }
    }, [router]);

    const refreshUser = useCallback(async () => {
        const token = localStorage.getItem('access_token');

        if (!token) {
            setUser(null);
            return;
        }

        try {
            const response = await fetchApi<User>('/auth/me', {
                requiresAuth: true,
            });

            if (response.data) {
                setUser(response.data);
                localStorage.setItem('user', JSON.stringify(response.data));
            } else {
                // Token invalid
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                setUser(null);
            }
        } catch (error) {
            console.error('Refresh user error:', error);
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            setUser(null);
        }
    }, []);

    const value: AuthContextType = {
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
