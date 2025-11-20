/**
 * Skeleton loader for job cards
 */

import { Skeleton2 as Skeleton } from '../Skeleton2';

export function SkeletonCard() {
    return (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            {/* Header */}
            <div className="mb-4 flex items-start justify-between">
                <div className="flex-1 space-y-2">
                    <Skeleton className="h-6 w-3/4" /> {/* Title */}
                    <Skeleton className="h-4 w-1/2" /> {/* Company */}
                </div>
                <Skeleton className="h-8 w-8 rounded-full" /> {/* Icon/Button */}
            </div>

            {/* Tags/Badges */}
            <div className="mb-4 flex gap-2">
                <Skeleton className="h-6 w-16 rounded-full" />
                <Skeleton className="h-6 w-20 rounded-full" />
                <Skeleton className="h-6 w-24 rounded-full" />
            </div>

            {/* Description */}
            <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
            </div>

            {/* Footer */}
            <div className="mt-4 flex items-center justify-between pt-4 border-t border-gray-100">
                <Skeleton className="h-4 w-24" /> {/* Date/Info */}
                <Skeleton className="h-9 w-28 rounded-md" /> {/* Button */}
            </div>
        </div>
    );
}

export function SkeletonCardList({ count = 3 }: { count?: number }) {
    return (
        <div className="space-y-4">
            {Array.from({ length: count }).map((_, i) => (
                <SkeletonCard key={i} />
            ))}
        </div>
    );
}
