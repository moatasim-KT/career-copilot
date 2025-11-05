/**
 * Skeleton loader for data tables
 */

import { Skeleton } from './Skeleton';

interface SkeletonTableProps {
    rows?: number;
    columns?: number;
}

export function SkeletonTable({ rows = 5, columns = 5 }: SkeletonTableProps) {
    return (
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
            {/* Table Header */}
            <div className="border-b border-gray-200 bg-gray-50">
                <div className="flex gap-4 p-4">
                    {Array.from({ length: columns }).map((_, i) => (
                        <Skeleton key={i} className="h-5 flex-1" />
                    ))}
                </div>
            </div>

            {/* Table Body */}
            <div className="divide-y divide-gray-200">
                {Array.from({ length: rows }).map((_, rowIndex) => (
                    <div key={rowIndex} className="flex gap-4 p-4">
                        {Array.from({ length: columns }).map((_, colIndex) => (
                            <Skeleton key={colIndex} className="h-4 flex-1" />
                        ))}
                    </div>
                ))}
            </div>
        </div>
    );
}

export function SkeletonTableCompact({ rows = 10 }: { rows?: number }) {
    return (
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
            {/* Header */}
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
                <Skeleton className="h-5 w-32" />
            </div>

            {/* Rows */}
            <div className="divide-y divide-gray-200">
                {Array.from({ length: rows }).map((_, i) => (
                    <div key={i} className="flex items-center gap-3 px-4 py-3">
                        <Skeleton className="h-4 w-4 rounded" /> {/* Checkbox */}
                        <Skeleton className="h-4 flex-1" />
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-8 w-20 rounded" /> {/* Action button */}
                    </div>
                ))}
            </div>
        </div>
    );
}
