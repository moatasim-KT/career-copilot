/**
 * Settings Root Page
 * 
 * Redirects to the profile settings page by default
 */

'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/settings/profile');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto mb-4" />
        <p className="text-neutral-600 dark:text-neutral-400">Loading settings...</p>
      </div>
    </div>
  );
}
