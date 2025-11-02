'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import LoginForm from '@/components/forms/LoginForm';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  if (isAuthenticated) {
    return null;
  }

  return <LoginForm onLogin={login} />;
}

