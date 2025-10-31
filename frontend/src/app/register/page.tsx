
'use client';

import { useRouter } from 'next/navigation';

import RegistrationForm from '@/components/forms/RegistrationForm';

export default function RegisterPage() {
  const router = useRouter();

  const handleRegister = () => {
    router.push('/login');
  };

  return <RegistrationForm onRegister={handleRegister} />;
}
