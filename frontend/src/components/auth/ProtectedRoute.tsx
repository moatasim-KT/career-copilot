
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { getToken } from '../../lib/auth/cookies';

const ProtectedRoute = (WrappedComponent: React.ComponentType) => {
  const Wrapper = (props: any) => {
    const router = useRouter();

    useEffect(() => {
      const token = getToken();
      if (!token) {
        router.push('/login');
      }
    }, [router]);

    return <WrappedComponent {...props} />;
  };

  return Wrapper;
};

export default ProtectedRoute;
