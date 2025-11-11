/**
 * VirtualApplicationList Component
 * 
 * A virtualized application list component that efficiently renders large lists of applications
 * by only rendering visible items in the viewport. Uses @tanstack/react-virtual
 * for optimal performance with 100+ applications.
 * 
 * Features:
 * - Virtual scrolling for performance with large datasets
 * - Smooth animations with Framer Motion
 * - Configurable overscan for smoother scrolling
 * - Responsive design
 * - Selection support
 * - Empty state handling
 * - Status-based filtering
 */

'use client';

import { useVirtualizer } from '@tanstack/react-virtual';
import { motion, AnimatePresence } from 'framer-motion';
import React, { useRef } from 'react';

import ApplicationCard, { Application } from '@/components/ui/ApplicationCard';
import { fadeVariants, staggerItem } from '@/lib/animations';

/**
 * VirtualApplicationList Props
 */
interface VirtualApplicationListProps {
  /** Array of applications to display */
  applications: Application[];
  /** Callback when an application is clicked */
  onApplicationClick: (applicationId: number) => void;
  /** Array of selected application IDs */
  selectedApplicationIds: number[];
  /** Callback when an application is selected/deselected */
  onSelectApplication: (applicationId: number) => void;
  /** Estimated height of each application card in pixels (default: 220) */
  estimatedSize?: number;
  /** Number of items to render outside the visible area (default: 5) */
  overscan?: number;
  /** Custom className for the container */
  className?: string;
  /** Custom empty state message */
  emptyMessage?: string;
  /** Card variant to use */
  variant?: 'default' | 'compact' | 'detailed';
}

/**
 * VirtualApplicationList Component
 * 
 * Renders a virtualized list of application cards for optimal performance with large datasets.
 * Only renders items that are visible in the viewport plus a configurable overscan.
 * 
 * @example
 * ```tsx
 * <VirtualApplicationList
 *   applications={applications}
 *   onApplicationClick={(id) => router.push(`/applications/${id}`)}
 *   selectedApplicationIds={selectedIds}
 *   onSelectApplication={handleSelect}
 *   estimatedSize={240}
 *   overscan={5}
 * />
 * ```
 */
export function VirtualApplicationList({
  applications,
  onApplicationClick,
  selectedApplicationIds,
  onSelectApplication,
  estimatedSize = 220,
  overscan = 5,
  className = '',
  emptyMessage = 'No applications found. Start applying to jobs to track your progress.',
  variant = 'default',
}: VirtualApplicationListProps) {
  // Reference to the scrollable container
  const parentRef = useRef<HTMLDivElement>(null);

  // Initialize the virtualizer
  const virtualizer = useVirtualizer({
    count: applications.length,
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
  if (applications.length === 0) {
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-lg font-medium">{emptyMessage}</p>
          <p className="mt-2 text-sm text-neutral-400 dark:text-neutral-500">
            Applications you submit will appear here
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
            const application = applications[virtualItem.index];
            const isSelected = selectedApplicationIds.includes(application.id);

            return (
              <motion.div
                key={application.id}
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
                  onClick={() => onApplicationClick(application.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onApplicationClick(application.id);
                    }
                  }}
                  aria-label={`View application: ${application.job_title || `Job #${application.job_id}`} - Status: ${application.status}`}
                >
                  <ApplicationCard
                    application={application}
                    variant={variant}
                    isSelected={isSelected}
                    onSelect={() => onSelectApplication(application.id)}
                  />
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Scroll indicator for large lists */}
      {applications.length > 20 && (
        <div className="fixed bottom-4 right-4 bg-white dark:bg-neutral-800 rounded-full shadow-lg px-4 py-2 text-sm text-neutral-600 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700">
          Showing {virtualItems.length} of {applications.length} applications
        </div>
      )}
    </div>
  );
}

/**
 * VirtualApplicationListGrid Component
 * 
 * A grid variant of the virtual application list that displays applications in a responsive grid layout.
 * Useful for displaying applications in a card grid format while maintaining virtualization benefits.
 * 
 * @example
 * ```tsx
 * <VirtualApplicationListGrid
 *   applications={applications}
 *   onApplicationClick={(id) => router.push(`/applications/${id}`)}
 *   selectedApplicationIds={selectedIds}
 *   onSelectApplication={handleSelect}
 *   columns={{ sm: 1, md: 2, lg: 3 }}
 * />
 * ```
 */
interface VirtualApplicationListGridProps extends VirtualApplicationListProps {
  /** Number of columns per breakpoint */
  columns?: {
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

export function VirtualApplicationListGrid({
  applications,
  onApplicationClick,
  selectedApplicationIds,
  onSelectApplication,
  estimatedSize = 240,
  overscan = 5,
  className = '',
  emptyMessage = 'No applications found. Start applying to jobs to track your progress.',
  variant = 'default',
  columns = { sm: 1, md: 2, lg: 3 },
}: VirtualApplicationListGridProps) {
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

  // Group applications into rows
  const rows = Math.ceil(applications.length / currentColumns);

  const virtualizer = useVirtualizer({
    count: rows,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan,
  });

  const virtualItems = virtualizer.getVirtualItems();

  if (applications.length === 0) {
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-lg font-medium">{emptyMessage}</p>
          <p className="mt-2 text-sm text-neutral-400 dark:text-neutral-500">
            Applications you submit will appear here
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
          const rowApplications = applications.slice(startIndex, startIndex + currentColumns);

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
                {rowApplications.map((application) => {
                  const isSelected = selectedApplicationIds.includes(application.id);

                  return (
                    <motion.div
                      key={application.id}
                      variants={staggerItem}
                      initial="hidden"
                      animate="visible"
                      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                      layout
                      onClick={() => onApplicationClick(application.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onApplicationClick(application.id);
                        }
                      }}
                      aria-label={`View application: ${application.job_title || `Job #${application.job_id}`} - Status: ${application.status}`}
                    >
                      <ApplicationCard
                        application={application}
                        variant={variant}
                        isSelected={isSelected}
                        onSelect={() => onSelectApplication(application.id)}
                      />
                    </motion.div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {applications.length > 20 && (
        <div className="fixed bottom-4 right-4 bg-white dark:bg-neutral-800 rounded-full shadow-lg px-4 py-2 text-sm text-neutral-600 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700">
          Showing {virtualItems.length * currentColumns} of {applications.length} applications
        </div>
      )}
    </div>
  );
}

export default VirtualApplicationList;
