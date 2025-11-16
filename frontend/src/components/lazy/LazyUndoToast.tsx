/**
 * Lazy-loaded UndoToast component
 * 
 * Dynamically imports the UndoToast component to reduce initial bundle size.
 * This component shows a toast notification with an undo button for bulk operations.
 */

'use client';

import dynamic from 'next/dynamic';

// Lazy load UndoToast
const UndoToast = dynamic(
  () => import('@/components/ui/UndoToast').then((mod) => ({ default: mod.UndoToast })),
  {
    loading: () => null, // No skeleton needed for toast - it's small and appears quickly
    ssr: false,
  },
);

export default UndoToast;
