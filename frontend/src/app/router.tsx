
'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const AppRouter = () => {
  const router = useRouter();

  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);

  return null;
};

export default AppRouter;
