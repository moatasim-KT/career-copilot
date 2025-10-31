'use client';

import { useRouter } from 'next/navigation';

import LoginForm from '@/components/forms/LoginForm';
import { apiClient } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();

  const handleLogin = (token: string, _userData: unknown) => {
    localStorage.setItem('auth_token', token);
    apiClient.setToken(token);
    router.push('/dashboard');
  };

  return <LoginForm onLogin={handleLogin} />;
}
