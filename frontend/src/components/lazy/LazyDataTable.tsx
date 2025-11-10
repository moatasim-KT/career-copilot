/**
 * LazyDataTable
 * 
 * Lazy-loaded wrapper for DataTable component with dnd-kit.
 * This component uses dynamic import to code-split the heavy table library.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

// Table skeleton
function DataTableSkeleton() {
  return (
    <div className="w-full animate-pulse">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="h-10 w-64 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        <div className="flex space-x-2">
          <div className="h-10 w-24 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          <div className="h-10 w-24 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
      </div>
      
      {/* Table */}
      <div className="border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden">
        {/* Table header */}
        <div className="bg-neutral-100 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center p-4 space-x-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded flex-1"></div>
            ))}
          </div>
        </div>
        
        {/* Table rows */}
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="border-b border-neutral-200 dark:border-neutral-700 last:border-b-0">
            <div className="flex items-center p-4 space-x-4">
              {[1, 2, 3, 4, 5].map((j) => (
                <div key={j} className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded flex-1"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {/* Pagination */}
      <div className="flex items-center justify-between mt-4">
        <div className="h-4 w-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        <div className="flex space-x-2">
          <div className="h-10 w-10 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          <div className="h-10 w-10 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          <div className="h-10 w-10 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
      </div>
    </div>
  );
}

// Lazy load DataTable
const DataTable = dynamic(
  () => import('@/components/ui/DataTable/DataTable').then((mod) => ({ default: mod.DataTable })),
  {
    loading: () => <DataTableSkeleton />,
    ssr: false, // DataTable with drag-drop needs client-side rendering
  }
);

interface LazyDataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  [key: string]: any; // Allow other props to pass through
}

export default function LazyDataTable<TData, TValue>({
  columns,
  data,
  ...props
}: LazyDataTableProps<TData, TValue>) {
  return (
    <Suspense fallback={<DataTableSkeleton />}>
      <DataTable columns={columns} data={data} {...props} />
    </Suspense>
  );
}
