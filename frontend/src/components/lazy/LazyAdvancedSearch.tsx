/**
 * LazyAdvancedSearch
 * 
 * Lazy-loaded wrapper for AdvancedSearch component.
 * This component uses dynamic import to code-split the complex search UI.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

import { AdvancedSearchSkeleton } from '@/components/loading/AdvancedSearchSkeleton';
import type { AdvancedSearchProps } from '@/components/features/AdvancedSearch';

// Lazy load AdvancedSearch
const AdvancedSearch = dynamic(
  () => import('@/components/features/AdvancedSearch').then((mod) => ({ default: mod.AdvancedSearch })),
  {
    loading: () => <AdvancedSearchSkeleton />,
    ssr: false, // Advanced search is client-side only
  }
);

export default function LazyAdvancedSearch(props: AdvancedSearchProps) {
  // Don't render anything if not open to avoid loading the component unnecessarily
  if (!props.isOpen) {
    return null;
  }

  return (
    <Suspense fallback={<AdvancedSearchSkeleton />}>
      <AdvancedSearch {...props} />
    </Suspense>
  );
}
