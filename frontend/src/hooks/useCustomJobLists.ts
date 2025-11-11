/**
 * Hook for managing custom job lists with reordering
 */

import { useState, useEffect, useCallback } from 'react';
import { logger } from '@/lib/logger';

export interface CustomJobList {
  id: string;
  name: string;
  description?: string;
  jobIds: number[];
  createdAt: Date;
  order: number;
  color?: string;
}

const STORAGE_KEY = 'custom-job-lists';

export function useCustomJobLists() {
  const [lists, setLists] = useState<CustomJobList[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load lists from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setLists(
          parsed.map((l: any) => ({
            ...l,
            createdAt: new Date(l.createdAt),
          })),
        );
      }
    } catch (error) {
      logger.error('Failed to load custom job lists', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save lists to localStorage
  const saveToStorage = useCallback((newLists: CustomJobList[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newLists));
    } catch (error) {
      logger.error('Failed to save job lists', error);
    }
  }, []);

  // Add a new list
  const addList = useCallback(
    (name: string, description?: string, color?: string) => {
      const newList: CustomJobList = {
        id: Date.now().toString(),
        name,
        description,
        jobIds: [],
        createdAt: new Date(),
        order: lists.length,
        color,
      };

      const newLists = [...lists, newList];
      setLists(newLists);
      saveToStorage(newLists);
      return newList;
    },
    [lists, saveToStorage],
  );

  // Delete a list
  const deleteList = useCallback(
    (id: string) => {
      const newLists = lists.filter((l) => l.id !== id);
      setLists(newLists);
      saveToStorage(newLists);
    },
    [lists, saveToStorage],
  );

  // Reorder lists
  const reorderLists = useCallback(
    (reorderedLists: CustomJobList[]) => {
      // Update order property
      const updatedLists = reorderedLists.map((list, index) => ({
        ...list,
        order: index,
      }));
      setLists(updatedLists);
      saveToStorage(updatedLists);
    },
    [saveToStorage],
  );

  // Add job to list
  const addJobToList = useCallback(
    (listId: string, jobId: number) => {
      const newLists = lists.map((list) =>
        list.id === listId && !list.jobIds.includes(jobId)
          ? { ...list, jobIds: [...list.jobIds, jobId] }
          : list,
      );
      setLists(newLists);
      saveToStorage(newLists);
    },
    [lists, saveToStorage],
  );

  // Remove job from list
  const removeJobFromList = useCallback(
    (listId: string, jobId: number) => {
      const newLists = lists.map((list) =>
        list.id === listId
          ? { ...list, jobIds: list.jobIds.filter((id) => id !== jobId) }
          : list,
      );
      setLists(newLists);
      saveToStorage(newLists);
    },
    [lists, saveToStorage],
  );

  // Get sorted lists
  const sortedLists = [...lists].sort((a, b) => a.order - b.order);

  return {
    lists: sortedLists,
    isLoading,
    addList,
    deleteList,
    reorderLists,
    addJobToList,
    removeJobFromList,
  };
}
