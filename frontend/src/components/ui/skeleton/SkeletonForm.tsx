/**
 * Skeleton loader for forms
 */

import { Skeleton } from './Skeleton';

export function SkeletonForm() {
    return (
        <div className="space-y-6 rounded-lg border border-gray-200 bg-white p-6">
            {/* Form field 1 */}
            <div className="space-y-2">
                <Skeleton className="h-5 w-24" /> {/* Label */}
                <Skeleton className="h-10 w-full rounded-md" /> {/* Input */}
            </div>

            {/* Form field 2 */}
            <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-10 w-full rounded-md" />
            </div>

            {/* Form field 3 - Textarea */}
            <div className="space-y-2">
                <Skeleton className="h-5 w-28" />
                <Skeleton className="h-32 w-full rounded-md" />
            </div>

            {/* Form field 4 - Select/Dropdown */}
            <div className="space-y-2">
                <Skeleton className="h-5 w-36" />
                <Skeleton className="h-10 w-full rounded-md" />
            </div>

            {/* Submit button */}
            <div className="flex justify-end gap-3 pt-4">
                <Skeleton className="h-10 w-24 rounded-md" /> {/* Cancel */}
                <Skeleton className="h-10 w-28 rounded-md" /> {/* Submit */}
            </div>
        </div>
    );
}

export function SkeletonFormCompact() {
    return (
        <div className="space-y-4">
            <div className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-9 w-full rounded-md" />
            </div>
            <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-9 w-full rounded-md" />
            </div>
            <Skeleton className="h-9 w-full rounded-md" /> {/* Button */}
        </div>
    );
}
