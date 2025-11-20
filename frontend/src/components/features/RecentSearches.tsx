/**
 * RecentSearches Component
 * 
 * Displays recent search history with quick access to re-run searches.
 */

'use client';

import { Clock, Search, X, ChevronDown } from 'lucide-react';
import { useState } from 'react';

import Button2 from '@/components/ui/Button2';
import Card, { CardContent } from '@/components/ui/Card2';
import { useRecentSearches } from '@/hooks/useRecentSearches';
import { fadeVariants, slideVariants, staggerContainer, staggerItem, springConfigs } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
import type { RecentSearch, SearchGroup } from '@/types/search';

export interface RecentSearchesProps {
  /** Callback when a recent search is loaded */
  onLoad: (query: SearchGroup) => void;

  /** Context for recent searches (jobs, applications, etc.) */
  context: 'jobs' | 'applications';

  /** Custom class name */
  className?: string;
}

/**
 * Format timestamp as relative time
 */
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - new Date(date).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return new Date(date).toLocaleDateString();
}

/**
 * RecentSearches Component
 */
export function RecentSearches({
  onLoad,
  context,
  className = '',
}: RecentSearchesProps) {
  const { recentSearches, clearRecentSearches, removeRecentSearch } = useRecentSearches(context);
  const [isOpen, setIsOpen] = useState(false);

  const handleLoadSearch = (search: RecentSearch) => {
    onLoad(search.query);
    setIsOpen(false);
  };

  const handleClearAll = () => {
    if (confirm('Are you sure you want to clear all recent searches?')) {
      clearRecentSearches();
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Dropdown Button */}
      <Button2
        type="button"
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2"
      >
        <Clock className="h-4 w-4" />
        <span>Recent</span>
        {recentSearches.length > 0 && (
          <span className="ml-1 px-2 py-0.5 text-xs bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-full">
            {recentSearches.length}
          </span>
        )}
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button2>

      {/* Dropdown Panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown Content */}
            <m.div
              variants={slideVariants.down}
              initial="hidden"
              animate="visible"
              exit="hidden"
              transition={springConfigs.smooth}
              className="absolute top-full left-0 mt-2 w-96 max-w-[calc(100vw-2rem)] z-20"
            >
              <Card className="shadow-xl">
                <CardContent className="p-4">
                  {/* Header */}
                  {recentSearches.length > 0 && (
                    <div className="flex items-center justify-between mb-3 pb-3 border-b border-neutral-200 dark:border-neutral-700">
                      <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                        Recent Searches
                      </h3>
                      <button
                        type="button"
                        onClick={handleClearAll}
                        className="text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                      >
                        Clear All
                      </button>
                    </div>
                  )}

                  {recentSearches.length === 0 ? (
                    <m.div
                      variants={fadeVariants}
                      initial="hidden"
                      animate="visible"
                      className="text-center py-8"
                    >
                      <Clock className="h-12 w-12 text-neutral-400 dark:text-neutral-600 mx-auto mb-3" />
                      <p className="text-sm text-neutral-600 dark:text-neutral-400">
                        No recent searches
                      </p>
                      <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-1">
                        Your search history will appear here
                      </p>
                    </m.div>
                  ) : (
                    <m.div
                      variants={staggerContainer}
                      initial="hidden"
                      animate="visible"
                      className="space-y-2 max-h-96 overflow-y-auto"
                    >
                      <AnimatePresence mode="popLayout">
                        {recentSearches.map((search) => (
                          <m.div
                            key={search.id}
                            variants={staggerItem}
                            layout
                            exit={{
                              opacity: 0,
                              x: -20,
                              transition: { duration: 0.2 },
                            }}
                          >
                            <div
                              role="button"
                              tabIndex={0}
                              onClick={() => handleLoadSearch(search)}
                              onKeyDown={(event) => {
                                if (event.key === 'Enter' || event.key === ' ') {
                                  event.preventDefault();
                                  handleLoadSearch(search);
                                }
                              }}
                              className="cursor-pointer transition-all duration-200 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                            >
                              <Card hover>
                                <CardContent className="p-3">
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center space-x-2 mb-1">
                                        <Search className="h-4 w-4 text-neutral-500 dark:text-neutral-400 flex-shrink-0" />
                                        <p className="text-sm text-neutral-900 dark:text-neutral-100 truncate">
                                          {search.label}
                                        </p>
                                      </div>

                                      <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-500 dark:text-neutral-500">
                                        <span className="flex items-center space-x-1">
                                          <Clock className="h-3 w-3" />
                                          <span>{formatRelativeTime(search.timestamp)}</span>
                                        </span>

                                        {search.resultCount !== undefined && (
                                          <span>
                                            {search.resultCount} result{search.resultCount !== 1 ? 's' : ''}
                                          </span>
                                        )}
                                      </div>
                                    </div>

                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        removeRecentSearch(search.id);
                                      }}
                                      className="p-1 text-neutral-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors ml-2"
                                      aria-label="Remove from recent searches"
                                    >
                                      <X className="h-4 w-4" />
                                    </button>
                                  </div>
                                </CardContent>
                              </Card>
                            </div>
                          </m.div>
                        ))}
                      </AnimatePresence>
                    </m.div>
                  )}
                </CardContent>
              </Card>
            </m.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
