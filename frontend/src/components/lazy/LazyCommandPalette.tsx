/**
 * LazyCommandPalette
 * 
 * Lazy-loaded wrapper for CommandPalette with cmdk library.
 * This component uses dynamic import to code-split the command palette.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

import { CommandPaletteSkeleton } from '@/components/loading/CommandPaletteSkeleton';

// Lazy load CommandPalette with cmdk
const CommandPalette = dynamic(
  () => import('@/components/ui/CommandPalette').then((mod) => ({ default: mod.CommandPalette })),
  {
    loading: () => <CommandPaletteSkeleton />,
    ssr: false, // Command palette is client-side only
  }
);

interface LazyCommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LazyCommandPalette({ isOpen, onClose }: LazyCommandPaletteProps) {
  // Don't render anything if not open to avoid loading the component unnecessarily
  if (!isOpen) {
    return null;
  }

  return (
    <Suspense fallback={<CommandPaletteSkeleton />}>
      <CommandPalette isOpen={isOpen} onClose={onClose} />
    </Suspense>
  );
}
