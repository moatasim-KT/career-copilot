/**
 * AdvancedSearch Component
 * 
 * A slide-out panel for building complex search queries with the QueryBuilder.
 * Includes live preview, save functionality, and quick actions.
 */

'use client';

import { Search, Save, Trash2, Download, Upload, Loader2 } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

import Button2 from '@/components/ui/Button2';
import Card, { CardContent } from '@/components/ui/Card2';
import Input from '@/components/ui/Input2';
import Modal, { ModalFooter } from '@/components/ui/Modal2';
import { slideVariants, springConfigs } from '@/lib/animations';
import { logger } from '@/lib/logger';
import { m, AnimatePresence } from '@/lib/motion';
import type { SearchGroup, SearchField, SavedSearch } from '@/types/search';

import { QueryBuilder } from './QueryBuilder';


export interface AdvancedSearchProps {
  /** Whether the panel is open */
  isOpen: boolean;

  /** Callback when panel should close */
  onClose: () => void;

  /** Callback when search should be applied */
  onSearch: (query: SearchGroup) => void;

  /** Available fields for searching */
  fields: SearchField[];

  /** Initial query (optional) */
  initialQuery?: SearchGroup;

  /** Callback for live preview (optional) */
  onPreview?: (query: SearchGroup) => Promise<number>;

  /** Callback to save search */
  onSave?: (search: SavedSearch) => Promise<void>;

  /** Current result count (optional) */
  resultCount?: number;

  /** Whether search is loading */
  isLoading?: boolean;

  /** Custom class name */
  className?: string;
}

/**
 * Create an empty search group
 */
function createEmptyQuery(): SearchGroup {
  return {
    id: `root-${Date.now()}`,
    logic: 'AND',
    rules: [],
    groups: [],
  };
}

/**
 * Check if query has any criteria
 */
function hasSearchCriteria(query: SearchGroup): boolean {
  return query.rules.length > 0 || (query.groups?.length || 0) > 0;
}

/**
 * AdvancedSearch Component
 */
export function AdvancedSearch({
  isOpen,
  onClose,
  onSearch,
  fields,
  initialQuery,
  onPreview,
  onSave,
  resultCount,
  isLoading = false,
  className = '',
}: AdvancedSearchProps) {
  const [query, setQuery] = useState<SearchGroup>(initialQuery || createEmptyQuery());
  const [previewCount, setPreviewCount] = useState<number | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Reset query when initial query changes
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);

  // Live preview with debounce
  useEffect(() => {
    if (!onPreview || !hasSearchCriteria(query)) {
      setPreviewCount(null);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setIsPreviewLoading(true);
      try {
        const count = await onPreview(query);
        setPreviewCount(count);
      } catch (error) {
        logger.error('Preview failed:', error);
        setPreviewCount(null);
      } finally {
        setIsPreviewLoading(false);
      }
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [query, onPreview]);

  const handleApplySearch = useCallback(() => {
    if (hasSearchCriteria(query)) {
      onSearch(query);
      onClose();
    }
  }, [query, onSearch, onClose]);

  const handleClearAll = useCallback(() => {
    setQuery(createEmptyQuery());
    setPreviewCount(null);
  }, []);

  const handleSaveSearch = useCallback(async () => {
    if (!onSave || !saveName.trim()) return;

    setIsSaving(true);
    try {
      const savedSearch: SavedSearch = {
        id: `saved-${Date.now()}`,
        name: saveName.trim(),
        description: saveDescription.trim() || undefined,
        query,
        createdAt: new Date(),
        resultCount: previewCount || undefined,
      };

      await onSave(savedSearch);
      setShowSaveModal(false);
      setSaveName('');
      setSaveDescription('');
    } catch (error) {
      logger.error('Failed to save search:', error);
    } finally {
      setIsSaving(false);
    }
  }, [onSave, saveName, saveDescription, query, previewCount]);

  const handleExportQuery = useCallback(() => {
    const dataStr = JSON.stringify(query, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `search-query-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [query]);

  const handleImportQuery = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const imported = JSON.parse(event.target?.result as string);
          setQuery(imported);
        } catch (error) {
          logger.error('Failed to import query:', error);
          alert('Invalid query file');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  }, []);

  const hasCriteria = hasSearchCriteria(query);
  const displayCount = resultCount !== undefined ? resultCount : previewCount;

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <m.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
              onClick={onClose}
            />

            {/* Slide-out Panel */}
            <m.div
              variants={slideVariants.right}
              initial="hidden"
              animate="visible"
              exit="hidden"
              transition={springConfigs.smooth}
              className={`
                fixed right-0 top-0 bottom-0 w-full md:w-2/3 lg:w-1/2 xl:w-2/5
                bg-white dark:bg-neutral-900 shadow-2xl z-50 overflow-hidden
                flex flex-col ${className}
              `}
            >
              {/* Header */}
              <div className="flex-shrink-0 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                <div className="flex items-center justify-between p-6">
                  <div>
                    <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                      Advanced Search
                    </h2>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                      Build complex queries with multiple conditions
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={onClose}
                    className="p-2 text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
                    aria-label="Close advanced search"
                  >
                    <svg
                      className="h-6 w-6"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>

                {/* Preview Bar */}
                {hasCriteria && (
                  <m.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="px-6 pb-4"
                  >
                    <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
                      <CardContent className="p-3 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {isPreviewLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 text-blue-600 dark:text-blue-400 animate-spin" />
                              <span className="text-sm text-blue-700 dark:text-blue-300">
                                Calculating results...
                              </span>
                            </>
                          ) : displayCount !== null ? (
                            <>
                              <Search className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                              <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                                {displayCount} result{displayCount !== 1 ? 's' : ''} found
                              </span>
                            </>
                          ) : (
                            <>
                              <Search className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                              <span className="text-sm text-blue-700 dark:text-blue-300">
                                Ready to search
                              </span>
                            </>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </m.div>
                )}
              </div>

              {/* Query Builder */}
              <div className="flex-1 overflow-y-auto p-6">
                <QueryBuilder
                  query={query}
                  onChange={setQuery}
                  fields={fields}
                />
              </div>

              {/* Footer Actions */}
              <div className="flex-shrink-0 border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900 p-6">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                  {/* Secondary Actions */}
                  <div className="flex items-center space-x-2">
                    {onSave && (
                      <Button2
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setShowSaveModal(true)}
                        disabled={!hasCriteria}
                        className="flex items-center space-x-1"
                      >
                        <Save className="h-4 w-4" />
                        <span>Save</span>
                      </Button2>
                    )}

                    <Button2
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleExportQuery}
                      disabled={!hasCriteria}
                      className="flex items-center space-x-1"
                      title="Export query as JSON"
                    >
                      <Download className="h-4 w-4" />
                    </Button2>

                    <Button2
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleImportQuery}
                      className="flex items-center space-x-1"
                      title="Import query from JSON"
                    >
                      <Upload className="h-4 w-4" />
                    </Button2>
                  </div>

                  {/* Primary Actions */}
                  <div className="flex items-center space-x-2">
                    <Button2
                      type="button"
                      variant="outline"
                      onClick={handleClearAll}
                      disabled={!hasCriteria}
                      className="flex items-center space-x-1"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Clear All</span>
                    </Button2>

                    <Button2
                      type="button"
                      onClick={handleApplySearch}
                      disabled={!hasCriteria || isLoading}
                      loading={isLoading}
                      className="flex items-center space-x-1"
                    >
                      <Search className="h-4 w-4" />
                      <span>Apply Search</span>
                    </Button2>
                  </div>
                </div>
              </div>
            </m.div>
          </>
        )}
      </AnimatePresence>

      {/* Save Search Modal */}
      <Modal
        open={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        title="Save Search"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Search Name *"
            value={saveName}
            onChange={(e) => setSaveName(e.target.value)}
            placeholder="e.g., Senior React Jobs in SF"
            autoFocus
          />

          <Input
            label="Description (Optional)"
            value={saveDescription}
            onChange={(e) => setSaveDescription(e.target.value)}
            placeholder="Add a description to help remember this search..."
          />

          {previewCount !== null && (
            <div className="text-sm text-neutral-600 dark:text-neutral-400">
              This search currently returns {previewCount} result{previewCount !== 1 ? 's' : ''}.
            </div>
          )}
        </div>

        <ModalFooter>
          <Button2
            type="button"
            variant="outline"
            onClick={() => setShowSaveModal(false)}
          >
            Cancel
          </Button2>
          <Button2
            type="button"
            onClick={handleSaveSearch}
            disabled={!saveName.trim() || isSaving}
            loading={isSaving}
          >
            Save Search
          </Button2>
        </ModalFooter>
      </Modal>
    </>
  );
}