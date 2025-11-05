
import { createContext, useContext, useEffect } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { getToken } from '../lib/auth/cookies';
import { getUser, User } from '../lib/auth/rbac';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({ isAuthenticated: false, user: null, isLoading: true });

export const AuthProvider: React.FC = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useLocalStorage('isAuthenticated', false);
  const [user, setUser] = useLocalStorage<User | null>('user', null);
  const [isLoading, setIsLoading] = useLocalStorage('isLoading', true);

  useEffect(() => {
    const token = getToken();
    if (token) {
      setIsAuthenticated(true);
      setUser(getUser());
    } else {
      setIsAuthenticated(false);
      setUser(null);
    }
    setIsLoading(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
