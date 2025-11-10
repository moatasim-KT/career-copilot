/**
 * useRecentSearches Hook
 * 
 * Manages recent search history with localStorage persistence.
 * Tracks the last 10 searches with their criteria and result counts.
 */

'use client';

import { useCallback } from 'react';

import { useLocalStorage } from '@/hooks/useLocalStorage';
import type { RecentSearch, SearchGroup } from '@/types/search';

const MAX_RECENT_SEARCHES = 10;

/**
 * Generate a simple label for a search query
 */
function generateSearchLabel(query: SearchGroup): string {
  const ruleCount = query.rules.length;
  const groupCount = query.groups?.length || 0;
  const totalCriteria = ruleCount + groupCount;

  if (totalCriteria === 0) {
    return 'Empty search';
  }

  if (totalCriteria === 1 && ruleCount === 1) {
    const rule = query.rules[0];
    return `${rule.field} ${rule.operator} ${rule.value}`;
  }

  return `${totalCriteria} criteria (${query.logic})`;
}

/**
 * Check if two search queries are equivalent
 */
function areQueriesEqual(a: SearchGroup, b: SearchGroup): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export interface UseRecentSearchesReturn {
  /** List of recent searches (most recent first) */
  recentSearches: RecentSearch[];
  
  /** Add a search to recent history */
  addRecentSearch: (query: SearchGroup, resultCount?: number, label?: string) => void;
  
  /** Clear all recent searches */
  clearRecentSearches: () => void;
  
  /** Remove a specific recent search */
  removeRecentSearch: (searchId: string) => void;
}

/**
 * Hook to manage recent search history
 */
export function useRecentSearches(context: 'jobs' | 'applications'): UseRecentSearchesReturn {
  const storageKey = `recentSearches_${context}`;
  const [recentSearches, setRecentSearches] = useLocalStorage<RecentSearch[]>(storageKey, []);

  const addRecentSearch = useCallback((
    query: SearchGroup,
    resultCount?: number,
    label?: string,
  ) => {
    setRecentSearches(prev => {
      // Check if this exact query already exists
      const existingIndex = prev.findIndex(search =>
        areQueriesEqual(search.query, query),
      );

      const newSearch: RecentSearch = {
        id: `recent-${Date.now()}`,
        query,
        timestamp: new Date(),
        resultCount,
        label: label || generateSearchLabel(query),
      };

      let updated: RecentSearch[];

      if (existingIndex >= 0) {
        // Move existing search to top and update metadata
        updated = [
          newSearch,
          ...prev.slice(0, existingIndex),
          ...prev.slice(existingIndex + 1),
        ];
      } else {
        // Add new search to top
        updated = [newSearch, ...prev];
      }

      // Keep only the most recent MAX_RECENT_SEARCHES
      return updated.slice(0, MAX_RECENT_SEARCHES);
    });
  }, [setRecentSearches]);

  const clearRecentSearches = useCallback(() => {
    setRecentSearches([]);
  }, [setRecentSearches]);

  const removeRecentSearch = useCallback((searchId: string) => {
    setRecentSearches(prev => prev.filter(search => search.id !== searchId));
  }, [setRecentSearches]);

  return {
    recentSearches,
    addRecentSearch,
    clearRecentSearches,
    removeRecentSearch,
  };
}
