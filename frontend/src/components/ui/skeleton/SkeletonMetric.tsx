/**
 * Skeleton loader for metric/stat cards
 */

import { Skeleton } from './Skeleton';

export function SkeletonMetric() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      {/* Header with icon */}
      <div className="mb-4 flex items-center justify-between">
        <Skeleton className="h-5 w-32" /> {/* Label */}
        <Skeleton className="h-8 w-8 rounded-md" /> {/* Icon */}
      </div>

      {/* Value */}
      <Skeleton className="mb-2 h-8 w-24" />

      {/* Change indicator */}
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-12" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  );
}

export function SkeletonMetricGrid({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonMetric key={i} />
      ))}
    </div>
  );
}

export function SkeletonMetricLarge() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
      {/* Icon */}
      <div className="mb-4">
        <Skeleton className="h-12 w-12 rounded-full" />
      </div>

      {/* Label */}
      <Skeleton className="mb-4 h-6 w-48" />

      {/* Large Value */}
      <Skeleton className="mb-2 h-12 w-32" />

      {/* Description */}
      <Skeleton className="h-4 w-64" />

      {/* Progress bar or additional info */}
      <div className="mt-6">
        <Skeleton className="h-2 w-full rounded-full" />
      </div>
    </div>
  );
}
