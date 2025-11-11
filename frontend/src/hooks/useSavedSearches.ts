/**
 * Hook for managing saved searches with reordering
 */

import { useState, useEffect, useCallback } from 'react';
import { logger } from '@/lib/logger';

export interface SavedSearch {
  id: string;
  name: string;
  query: any; // Search query object
  createdAt: Date;
  order: number;
}

const STORAGE_KEY = 'saved-searches';

export function useSavedSearches() {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load searches from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setSearches(
          parsed.map((s: any) => ({
            ...s,
            createdAt: new Date(s.createdAt),
          })),
        );
      }
    } catch (error) {
      logger.error('Failed to load saved searches', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save searches to localStorage
  const saveToStorage = useCallback((newSearches: SavedSearch[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newSearches));
    } catch (error) {
      logger.error('Failed to save searches', error);
    }
  }, []);

  // Add a new search
  const addSearch = useCallback(
    (name: string, query: any) => {
      const newSearch: SavedSearch = {
        id: Date.now().toString(),
        name,
        query,
        createdAt: new Date(),
        order: searches.length,
      };

      const newSearches = [...searches, newSearch];
      setSearches(newSearches);
      saveToStorage(newSearches);
      return newSearch;
    },
    [searches, saveToStorage],
  );

  // Delete a search
  const deleteSearch = useCallback(
    (id: string) => {
      const newSearches = searches.filter((s) => s.id !== id);
      setSearches(newSearches);
      saveToStorage(newSearches);
    },
    [searches, saveToStorage],
  );

  // Reorder searches
  const reorderSearches = useCallback(
    (reorderedSearches: SavedSearch[]) => {
      // Update order property
      const updatedSearches = reorderedSearches.map((search, index) => ({
        ...search,
        order: index,
      }));
      setSearches(updatedSearches);
      saveToStorage(updatedSearches);
    },
    [saveToStorage],
  );

  // Get sorted searches
  const sortedSearches = [...searches].sort((a, b) => a.order - b.order);

  return {
    searches: sortedSearches,
    isLoading,
    addSearch,
    deleteSearch,
    reorderSearches,
  };
}
