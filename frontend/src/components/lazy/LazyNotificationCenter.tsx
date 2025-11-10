/**
 * LazyNotificationCenter
 * 
 * Lazy-loaded wrapper for NotificationCenter component.
 * This component uses dynamic import to code-split the notification UI.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

import { NotificationCenterSkeleton } from '@/components/loading/NotificationCenterSkeleton';

// Lazy load NotificationCenter
const NotificationCenter = dynamic(
  () => import('@/components/ui/NotificationCenter').then((mod) => ({ default: mod.NotificationCenter })),
  {
    loading: () => <NotificationCenterSkeleton />,
    ssr: false, // Notification center is client-side only
  }
);

interface LazyNotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LazyNotificationCenter({ isOpen, onClose }: LazyNotificationCenterProps) {
  // Don't render anything if not open to avoid loading the component unnecessarily
  if (!isOpen) {
    return null;
  }

  return (
    <Suspense fallback={<NotificationCenterSkeleton />}>
      <NotificationCenter isOpen={isOpen} onClose={onClose} />
    </Suspense>
  );
}
