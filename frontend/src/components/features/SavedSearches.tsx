/**
 * SavedSearches Component
 * 
 * Manages saved search queries with load, edit, and delete operations.
 */

'use client';

import { Save, Search, Edit, Trash2, Clock, Tag, ChevronDown } from 'lucide-react';
import { useState, useEffect } from 'react';

import Button2 from '@/components/ui/Button2';
import Card2, { CardContent } from '@/components/ui/Card2';
import Input from '@/components/ui/Input';
import Modal, { ModalFooter } from '@/components/ui/Modal';
import { useLocalStorage } from '@/hooks/useLocalStorage';
import { fadeVariants, slideVariants, staggerContainer, staggerItem, springConfigs } from '@/lib/animations';
import { logger } from '@/lib/logger';
import { m, AnimatePresence } from '@/lib/motion';
import type { SavedSearch } from '@/types/search';


export interface SavedSearchesProps {
  /** Callback when a saved search is loaded */
  onLoad: (search: SavedSearch) => void;

  /** Callback to save a new search */
  onSave?: (search: SavedSearch) => Promise<void>;

  /** Callback to delete a search */
  onDelete?: (searchId: string) => Promise<void>;

  /** Context for saved searches (jobs, applications, etc.) */
  context: 'jobs' | 'applications';

  /** Custom class name */
  className?: string;
}

/**
 * SavedSearches Component
 */
export function SavedSearches({
  onLoad,
  onSave,
  onDelete,
  context,
  className = '',
}: SavedSearchesProps) {
  const storageKey = `savedSearches_${context}`;
  const [savedSearches, setSavedSearches] = useLocalStorage<SavedSearch[]>(storageKey, []);
  const [isOpen, setIsOpen] = useState(false);
  const [editingSearch, setEditingSearch] = useState<SavedSearch | null>(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);

  // Sync with backend if onSave is provided
  useEffect(() => {
    // In a real implementation, fetch saved searches from backend
    // For now, we're using localStorage
  }, []);

  const handleLoadSearch = (search: SavedSearch) => {
    // Update last used timestamp and use count
    const updatedSearch: SavedSearch = {
      ...search,
      lastUsedAt: new Date(),
      useCount: (search.useCount || 0) + 1,
    };

    setSavedSearches(prev =>
      prev.map(s => s.id === search.id ? updatedSearch : s),
    );

    onLoad(updatedSearch);
    setIsOpen(false);
  };

  const handleEditSearch = (search: SavedSearch) => {
    setEditingSearch(search);
    setEditName(search.name);
    setEditDescription(search.description || '');
    setShowEditModal(true);
  };
  const handleSaveEdit = async () => {
    if (!editingSearch || !editName.trim()) return;

    const updatedSearch: SavedSearch = {
      ...editingSearch,
      name: editName.trim(),
      description: editDescription.trim() || undefined,
    };

    setSavedSearches(prev =>
      prev.map(s => (s.id === editingSearch.id ? updatedSearch : s)),
    );

    if (onSave) {
      try {
        await onSave(updatedSearch);
      } catch (error) {
        logger.error('Failed to save search:', error);
      }
    }

    setShowEditModal(false);
    setEditingSearch(null);
    setEditName('');
    setEditDescription('');
  };

  const handleDeleteSearch = async (searchId: string) => {
    if (!confirm('Are you sure you want to delete this saved search?')) return;

    setSavedSearches(prev => prev.filter(s => s.id !== searchId));

    if (onDelete) {
      try {
        await onDelete(searchId);
      } catch (error) {
        logger.error('Failed to delete search:', error);
      }
    }
  };

  const sortedSearches = [...savedSearches].sort((a, b) => {
    // Sort by last used (most recent first), then by use count
    if (a.lastUsedAt && b.lastUsedAt) {
      return new Date(b.lastUsedAt).getTime() - new Date(a.lastUsedAt).getTime();
    }
    if (a.lastUsedAt) return -1;
    if (b.lastUsedAt) return 1;
    return (b.useCount || 0) - (a.useCount || 0);
  });

  return (
    <>
      <div className={`relative ${className}`}>
        {/* Dropdown Button */}
        <Button2
          type="button"
          variant="outline"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center space-x-2"
        >
          <Save className="h-4 w-4" />
          <span>Saved Searches</span>
          {savedSearches.length > 0 && (
            <span className="ml-1 px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full">
              {savedSearches.length}
            </span>
          )}
          <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </Button2>

        {/* Dropdown Panel */}
        <AnimatePresence>
          {isOpen && (
            <>
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
                <Card2 className="shadow-xl">
                  <CardContent className="p-4">
                    {savedSearches.length === 0 ? (
                      <m.div
                        variants={fadeVariants}
                        initial="hidden"
                        animate="visible"
                        className="text-center py-8"
                      >
                        <Save className="h-12 w-12 text-neutral-400 dark:text-neutral-600 mx-auto mb-3" />
                        <p className="text-sm text-neutral-600 dark:text-neutral-400">
                          No saved searches yet
                        </p>
                        <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-1">
                          Use Advanced Search to create and save complex queries
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
                          {sortedSearches.map((search) => (
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
                                <Card2 hover>
                                  <CardContent className="p-3">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center space-x-2 mb-1">
                                          <Search className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                                          <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                                            {search.name}
                                          </h4>
                                        </div>

                                        {search.description && (
                                          <p className="text-xs text-neutral-600 dark:text-neutral-400 line-clamp-2 mb-2">
                                            {search.description}
                                          </p>
                                        )}

                                        <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-500 dark:text-neutral-500">
                                          {search.resultCount !== undefined && (
                                            <span className="flex items-center space-x-1">
                                              <span>{search.resultCount} results</span>
                                            </span>
                                          )}

                                          {search.lastUsedAt && (
                                            <span className="flex items-center space-x-1">
                                              <Clock className="h-3 w-3" />
                                              <span>
                                                {new Date(search.lastUsedAt).toLocaleDateString()}
                                              </span>
                                            </span>
                                          )}

                                          {search.useCount && search.useCount > 0 && (
                                            <span>Used {search.useCount}x</span>
                                          )}

                                          {search.tags && search.tags.length > 0 && (
                                            <div className="flex items-center space-x-1">
                                              <Tag className="h-3 w-3" />
                                              <span>{search.tags.join(', ')}</span>
                                            </div>
                                          )}
                                        </div>
                                      </div>

                                      <div className="flex items-center space-x-1 ml-2">
                                        <button
                                          type="button"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleEditSearch(search);
                                          }}
                                          className="p-1 text-neutral-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                                          aria-label="Edit search"
                                        >
                                          <Edit className="h-4 w-4" />
                                        </button>

                                        <button
                                          type="button"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteSearch(search.id);
                                          }}
                                          className="p-1 text-neutral-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                                          aria-label="Delete search"
                                        >
                                          <Trash2 className="h-4 w-4" />
                                        </button>
                                      </div>
                                    </div>
                                  </CardContent>
                                </Card2>
                              </div>
                            </m.div>
                          ))}
                        </AnimatePresence>
                      </m.div>
                    )}
                  </CardContent>
                </Card2>
              </m.div>
            </>
          )}
        </AnimatePresence>
      </div>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Saved Search"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Search Name *"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            placeholder="e.g., Senior React Jobs in SF"
            autoFocus
          />

          <Input
            label="Description (Optional)"
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="Add a description to help remember this search..."
          />
        </div>

        <ModalFooter>
          <Button2
            type="button"
            variant="outline"
            onClick={() => setShowEditModal(false)}
          >
            Cancel
          </Button2>
          <Button2
            type="button"
            onClick={handleSaveEdit}
            disabled={!editName.trim()}
          >
            Save Changes
          </Button2>
        </ModalFooter>
      </Modal>
    </>
  );
}

/**
 * Hook to manage saved searches
 */
export function useSavedSearches(context: 'jobs' | 'applications') {
  const storageKey = `savedSearches_${context}`;
  const [savedSearches, setSavedSearches] = useLocalStorage<SavedSearch[]>(storageKey, []);

  const saveSearch = async (search: SavedSearch): Promise<void> => {
    setSavedSearches(prev => {
      // Check if search with same name exists
      const existingIndex = prev.findIndex(s => s.name === search.name);
      if (existingIndex >= 0) {
        // Update existing
        const updated = [...prev];
        updated[existingIndex] = search;
        return updated;
      }
      // Add new
      return [...prev, search];
    });

    // In a real implementation, also save to backend
    // await apiClient.saveSearch(search);
  };

  const deleteSearch = async (searchId: string): Promise<void> => {
    setSavedSearches(prev => prev.filter(s => s.id !== searchId));

    // In a real implementation, also delete from backend
    // await apiClient.deleteSearch(searchId);
  };

  const loadSearch = (searchId: string): SavedSearch | undefined => {
    return savedSearches.find(s => s.id === searchId);
  };

  return {
    savedSearches,
    saveSearch,
    deleteSearch,
    loadSearch,
  };
}
