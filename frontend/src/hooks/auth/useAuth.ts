import { useCallback, useState } from 'react';

import { API_ENDPOINTS } from '../../lib/constants';
import { User } from '../../lib/types';

/**
 * Return type for useAuth hook
 */
interface AuthHook {
	/** Current authenticated user or null */
	user: User | null;
	/** Loading state for auth operations */
	isLoading: boolean;
	/** Error message if auth operation failed */
	error: string | null;
	/** Login function */
	login: (email: string, password: string) => Promise<void>;
	/** Logout function */
	logout: () => Promise<void>;
	/** Register function */
	register: (email: string, password: string, name: string) => Promise<void>;
}

/**
 * Custom hook for authentication operations
 * 
 * Provides login, logout, and registration functionality with state management.
 * 
 * @returns {AuthHook} Authentication state and methods
 * 
 * @example
 * ```tsx
 * const { user, login, logout, isLoading, error } = useAuth();
 * 
 * await login('user@example.com', 'password');
 * ```
 */
export function useAuth(): AuthHook {
	const [user, setUser] = useState<User | null>(null);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      setUser(data.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
		} finally {
			setIsLoading(false);
		}
	}, []);

	const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      await fetch(API_ENDPOINTS.AUTH.LOGOUT, {
        method: 'POST',
      });
      setUser(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
		} finally {
			setIsLoading(false);
		}
	}, []);

	const register = useCallback(async (email: string, password: string, name: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }

      const data = await response.json();
      setUser(data.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
		} finally {
			setIsLoading(false);
		}
	}, []);

	return {
		user,
		isLoading,
		error,
		login,
		logout,
		register,
	};
}