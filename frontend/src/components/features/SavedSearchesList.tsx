/**
 * Saved Searches List Component
 * Displays saved searches with drag-to-reorder functionality
 */

'use client';

import { Search, Trash2, Play } from 'lucide-react';
import { toast } from 'sonner';

import { DraggableList } from '@/components/ui/DraggableList';
import { useSavedSearches, SavedSearch } from '@/hooks/useSavedSearches';

interface SavedSearchesListProps {
  onLoadSearch?: (search: SavedSearch) => void;
}

export function SavedSearchesList({ onLoadSearch }: SavedSearchesListProps) {
  const { searches, isLoading, deleteSearch, reorderSearches } = useSavedSearches();

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this saved search?')) {
      deleteSearch(id);
      toast.success('Search deleted');
    }
  };

  const handleLoad = (search: SavedSearch) => {
    if (onLoadSearch) {
      onLoadSearch(search);
      toast.success(`Loaded search: ${search.name}`);
    }
  };

  const renderSearchItem = (search: SavedSearch, isDragging = false) => (
    <div
      className={`flex items-center justify-between p-4 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 transition-shadow ${
        isDragging ? 'shadow-2xl ring-2 ring-blue-500 dark:ring-blue-400' : 'hover:shadow-md'
      }`}
    >
      <div className="flex items-center space-x-3 flex-1 ml-8">
        <Search className="h-5 w-5 text-neutral-400 dark:text-neutral-500" />
        <div className="flex-1">
          <h4 className="font-medium text-neutral-900 dark:text-neutral-100">{search.name}</h4>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            Created {search.createdAt.toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={() => handleLoad(search)}
          className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
          aria-label="Load search"
        >
          <Play className="h-4 w-4" />
        </button>
        <button
          onClick={() => handleDelete(search.id)}
          className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
          aria-label="Delete search"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="h-16 bg-neutral-200 dark:bg-neutral-700 rounded-lg animate-pulse"
          ></div>
        ))}
      </div>
    );
  }

  if (searches.length === 0) {
    return (
      <div className="text-center py-8">
        <Search className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
        <p className="text-neutral-600 dark:text-neutral-400">No saved searches</p>
        <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
          Save your searches to quickly access them later
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Drag searches to reorder them
        </p>
      </div>

      <DraggableList
        items={searches}
        onReorder={reorderSearches}
        renderItem={renderSearchItem}
        getItemId={(search) => search.id}
        className="space-y-3"
      />
    </div>
  );
}
