/**
 * VirtualJobList Component
 * 
 * A virtualized job list component that efficiently renders large lists of jobs
 * by only rendering visible items in the viewport. Uses @tanstack/react-virtual
 * for optimal performance with 100+ jobs.
 * 
 * Features:
 * - Virtual scrolling for performance with large datasets
 * - Smooth animations with Framer Motion
 * - Configurable overscan for smoother scrolling
 * - Responsive design
 * - Selection support
 * - Empty state handling
 */

'use client';

import { useVirtualizer } from '@tanstack/react-virtual';
import { motion, AnimatePresence } from 'framer-motion';
import React, { useRef } from 'react';

import JobCard from '@/components/ui/JobCard';
import { fadeVariants, staggerItem } from '@/lib/animations';

/**
 * Job interface - flexible to accommodate various job data shapes
 */
interface Job {
  id: number | string;
  title: string;
  company: string;
  location?: string;
  type?: string;
  postedAt?: string;
  [key: string]: any; // Allow additional properties
}

/**
 * VirtualJobList Props
 */
interface VirtualJobListProps {
  /** Array of jobs to display */
  jobs: Job[];
  /** Callback when a job is clicked */
  onJobClick: (jobId: number | string) => void;
  /** Array of selected job IDs */
  selectedJobIds: (number | string)[];
  /** Callback when a job is selected/deselected */
  onSelectJob: (jobId: number | string) => void;
  /** Estimated height of each job card in pixels (default: 200) */
  estimatedSize?: number;
  /** Number of items to render outside the visible area (default: 5) */
  overscan?: number;
  /** Custom className for the container */
  className?: string;
  /** Custom empty state message */
  emptyMessage?: string;
}

/**
 * VirtualJobList Component
 * 
 * Renders a virtualized list of job cards for optimal performance with large datasets.
 * Only renders items that are visible in the viewport plus a configurable overscan.
 * 
 * @example
 * ```tsx
 * <VirtualJobList
 *   jobs={jobs}
 *   onJobClick={(id) => router.push(`/jobs/${id}`)}
 *   selectedJobIds={selectedIds}
 *   onSelectJob={handleSelect}
 *   estimatedSize={220}
 *   overscan={5}
 * />
 * ```
 */
export function VirtualJobList({
  jobs,
  onJobClick,
  selectedJobIds,
  onSelectJob,
  estimatedSize = 200,
  overscan = 5,
  className = '',
  emptyMessage = 'No jobs found. Adjust your filters or search criteria.',
}: VirtualJobListProps) {
  // Reference to the scrollable container
  const parentRef = useRef<HTMLDivElement>(null);

  // Initialize the virtualizer
  const virtualizer = useVirtualizer({
    count: jobs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimatedSize,
    overscan,
    // Enable smooth scrolling
    scrollMargin: 0,
    // Gap between items (in pixels)
    gap: 24,
  });

  // Get virtual items (only the visible ones + overscan)
  const virtualItems = virtualizer.getVirtualItems();

  // Handle empty state
  if (jobs.length === 0) {
    return (
      <motion.div
        className="text-center py-12 text-neutral-500 dark:text-neutral-400"
        variants={fadeVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <div className="max-w-md mx-auto">
          <svg
            className="mx-auto h-12 w-12 text-neutral-400 dark:text-neutral-600 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p className="text-lg font-medium">{emptyMessage}</p>
          <p className="mt-2 text-sm text-neutral-400 dark:text-neutral-500">
            Try adjusting your search or filter criteria
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <div
      ref={parentRef}
      className={`h-[calc(100vh-300px)] overflow-auto ${className}`}
      style={{
        // Ensure smooth scrolling on all browsers
        WebkitOverflowScrolling: 'touch',
      }}
    >
      {/* Virtual list container */}
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {/* Render only visible items */}
        <AnimatePresence mode="popLayout">
          {virtualItems.map((virtualItem) => {
            const job = jobs[virtualItem.index];
            const isSelected = selectedJobIds.includes(job.id);

            return (
              <motion.div
                key={job.id}
                variants={staggerItem}
                initial="hidden"
                animate="visible"
                exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                layout
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`,
                }}
                data-index={virtualItem.index}
              >
                <div
                  className="px-1"
                  onClick={() => onJobClick(job.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onJobClick(job.id);
                    }
                  }}
                  aria-label={`View job: ${job.title} at ${job.company}`}
                >
                  <JobCard
                    job={job}
                    isSelected={isSelected}
                    onSelect={() => onSelectJob(job.id)}
                  />
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Scroll indicator for large lists */}
      {jobs.length > 20 && (
        <div className="fixed bottom-4 right-4 bg-white dark:bg-neutral-800 rounded-full shadow-lg px-4 py-2 text-sm text-neutral-600 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700">
          Showing {virtualItems.length} of {jobs.length} jobs
        </div>
      )}
    </div>
  );
}

/**
 * VirtualJobListGrid Component
 * 
 * A grid variant of the virtual job list that displays jobs in a responsive grid layout.
 * Useful for displaying jobs in a card grid format while maintaining virtualization benefits.
 * 
 * @example
 * ```tsx
 * <VirtualJobListGrid
 *   jobs={jobs}
 *   onJobClick={(id) => router.push(`/jobs/${id}`)}
 *   selectedJobIds={selectedIds}
 *   onSelectJob={handleSelect}
 *   columns={{ sm: 1, md: 2, lg: 3 }}
 * />
 * ```
 */
interface VirtualJobListGridProps extends VirtualJobListProps {
  /** Number of columns per breakpoint */
  columns?: {
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

export function VirtualJobListGrid({
  jobs,
  onJobClick,
  selectedJobIds,
  onSelectJob,
  estimatedSize = 220,
  overscan = 5,
  className = '',
  emptyMessage = 'No jobs found. Adjust your filters or search criteria.',
  columns = { sm: 1, md: 2, lg: 3 },
}: VirtualJobListGridProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  // Calculate grid columns based on viewport
  const getColumns = () => {
    if (typeof window === 'undefined') return columns.sm || 1;
    
    const width = window.innerWidth;
    if (width >= 1280 && columns.xl) return columns.xl;
    if (width >= 1024 && columns.lg) return columns.lg;
    if (width >= 768 && columns.md) return columns.md;
    return columns.sm || 1;
  };

  const [currentColumns, setCurrentColumns] = React.useState(getColumns());

  // Update columns on resize
  React.useEffect(() => {
    const handleResize = () => {
      setCurrentColumns(getColumns());
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Calculate row height based on columns
  const rowHeight = estimatedSize + 24; // Add gap

  // Group jobs into rows
  const rows = Math.ceil(jobs.length / currentColumns);

  const virtualizer = useVirtualizer({
    count: rows,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan,
  });

  const virtualItems = virtualizer.getVirtualItems();

  if (jobs.length === 0) {
    return (
      <motion.div
        className="text-center py-12 text-neutral-500 dark:text-neutral-400"
        variants={fadeVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <div className="max-w-md mx-auto">
          <svg
            className="mx-auto h-12 w-12 text-neutral-400 dark:text-neutral-600 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p className="text-lg font-medium">{emptyMessage}</p>
          <p className="mt-2 text-sm text-neutral-400 dark:text-neutral-500">
            Try adjusting your search or filter criteria
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <div
      ref={parentRef}
      className={`h-[calc(100vh-300px)] overflow-auto ${className}`}
      style={{
        WebkitOverflowScrolling: 'touch',
      }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualRow) => {
          const startIndex = virtualRow.index * currentColumns;
          const rowJobs = jobs.slice(startIndex, startIndex + currentColumns);

          return (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div
                className={'grid gap-6'}
                style={{
                  gridTemplateColumns: `repeat(${currentColumns}, minmax(0, 1fr))`,
                }}
              >
                {rowJobs.map((job) => {
                  const isSelected = selectedJobIds.includes(job.id);

                  return (
                    <motion.div
                      key={job.id}
                      variants={staggerItem}
                      initial="hidden"
                      animate="visible"
                      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                      layout
                      onClick={() => onJobClick(job.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onJobClick(job.id);
                        }
                      }}
                      aria-label={`View job: ${job.title} at ${job.company}`}
                    >
                      <JobCard
                        job={job}
                        isSelected={isSelected}
                        onSelect={() => onSelectJob(job.id)}
                      />
                    </motion.div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {jobs.length > 20 && (
        <div className="fixed bottom-4 right-4 bg-white dark:bg-neutral-800 rounded-full shadow-lg px-4 py-2 text-sm text-neutral-600 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700">
          Showing {virtualItems.length * currentColumns} of {jobs.length} jobs
        </div>
      )}
    </div>
  );
}

export default VirtualJobList;
