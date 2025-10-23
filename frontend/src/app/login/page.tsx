'use client';

import LoginForm from '@/components/LoginForm';
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  const handleLogin = (token: string, userData: any) => {
    localStorage.setItem('auth_token', token);
    apiClient.setToken(token);
    setUser(userData);
    router.push('/dashboard');
  };

  return <LoginForm onLogin={handleLogin} />;
}
