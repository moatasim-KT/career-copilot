
'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const AppRouter = () => {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [router]);

  return null;
};

export default AppRouter;
