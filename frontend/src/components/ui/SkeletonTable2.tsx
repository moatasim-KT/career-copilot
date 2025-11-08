'use client';

import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface SkeletonTable2Props extends HTMLAttributes<HTMLDivElement> {
  /**
   * Number of columns
   */
  columns?: number;
  
  /**
   * Number of rows (excluding header)
   */
  rows?: number;
  
  /**
   * Animation style
   */
  animation?: 'pulse' | 'shimmer' | 'none';
  
  /**
   * Show header row
   */
  showHeader?: boolean;
}

const animations = {
  pulse: 'animate-pulse',
  shimmer: 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
  none: '',
};

/**
 * SkeletonTable2 - Table loading placeholder component
 * 
 * @example
 * ```tsx
 * // Simple table
 * <SkeletonTable2 columns={4} rows={5} />
 * 
 * // Table with shimmer animation
 * <SkeletonTable2 columns={6} rows={10} animation="shimmer" />
 * 
 * // Table without header
 * <SkeletonTable2 columns={3} rows={8} showHeader={false} />
 * ```
 */
export const SkeletonTable2 = forwardRef<HTMLDivElement, SkeletonTable2Props>(
  (
    {
      columns = 4,
      rows = 5,
      animation = 'pulse',
      showHeader = true,
      className,
      ...props
    },
    ref
  ) => {
    const animationClass = animations[animation];

    return (
      <div
        ref={ref}
        role="status"
        aria-label={`Loading table with ${columns} columns and ${rows} rows`}
        className={cn(
          'w-full rounded-lg border border-neutral-200 dark:border-neutral-700 overflow-hidden',
          className
        )}
        {...props}
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            {/* Header */}
            {showHeader && (
              <thead className="bg-neutral-50 dark:bg-neutral-800">
                <tr>
                  {Array.from({ length: columns }).map((_, index) => (
                    <th key={index} className="px-6 py-4">
                      <div
                        className={cn(
                          'h-4 bg-neutral-300 dark:bg-neutral-600 rounded w-3/4',
                          animationClass
                        )}
                      />
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            
            {/* Body */}
            <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
              {Array.from({ length: rows }).map((_, rowIndex) => (
                <tr key={rowIndex} className="bg-white dark:bg-neutral-900">
                  {Array.from({ length: columns }).map((_, colIndex) => (
                    <td key={colIndex} className="px-6 py-4">
                      <div
                        className={cn(
                          'h-4 bg-neutral-200 dark:bg-neutral-700 rounded',
                          // Vary widths for more natural appearance
                          colIndex === 0 ? 'w-2/3' : colIndex === columns - 1 ? 'w-1/2' : 'w-full',
                          animationClass
                        )}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <span className="sr-only">Loading...</span>
      </div>
    );
  }
);

SkeletonTable2.displayName = 'SkeletonTable2';

export default SkeletonTable2;
