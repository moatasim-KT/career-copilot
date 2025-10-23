
'use client';

import RegistrationForm from '@/components/RegistrationForm';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const router = useRouter();

  const handleRegister = () => {
    router.push('/login');
  };

  return <RegistrationForm onRegister={handleRegister} />;
}
