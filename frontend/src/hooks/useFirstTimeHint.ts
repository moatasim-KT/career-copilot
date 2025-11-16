/**
 * First Time Hint Hook
 * 
 * Tracks which features the user has seen and shows tooltips on first interaction.
 * Hints are stored in localStorage and can be permanently dismissed.
 * 
 * Usage:
 * ```tsx
 * const { shouldShow, dismiss } = useFirstTimeHint('command-palette');
 * 
 * if (shouldShow) {
 *   return <Tooltip>Press ⌘K to open command palette</Tooltip>
 * }
 * ```
 */

'use client';

import { useEffect, useState, useCallback } from 'react';

import { logger } from '@/lib/logger';

const STORAGE_KEY = 'first-time-hints';

interface HintState {
  [featureId: string]: {
    seen: boolean;
    dismissedAt?: string;
  };
}

/**
 * Get all hint states from localStorage
 */
function getHintStates(): HintState {
  if (typeof window === 'undefined') return {};
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    logger.error('Failed to read hints from localStorage:', error);
  }
  
  return {};
}

/**
 * Save hint states to localStorage
 */
function saveHintStates(states: HintState): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(states));
  } catch (error) {
    logger.error('Failed to save hints to localStorage:', error);
  }
}

/**
 * Check if a hint should be shown for a feature
 */
function shouldShowHint(featureId: string, states: HintState): boolean {
  const state = states[featureId];
  return !state || !state.seen;
}

/**
 * Mark a hint as seen
 */
function markHintAsSeen(featureId: string): void {
  const states = getHintStates();
  states[featureId] = {
    seen: true,
    dismissedAt: new Date().toISOString(),
  };
  saveHintStates(states);
}

/**
 * Reset a specific hint (for testing or re-onboarding)
 */
function resetHint(featureId: string): void {
  const states = getHintStates();
  delete states[featureId];
  saveHintStates(states);
}

/**
 * Reset all hints (for testing or re-onboarding)
 */
function resetAllHints(): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    logger.error('Failed to reset hints:', error);
  }
}

/**
 * Get list of all seen hints
 */
function getSeenHints(): string[] {
  const states = getHintStates();
  return Object.entries(states)
    .filter(([, state]) => state.seen)
    .map(([featureId]) => featureId);
}

interface UseFirstTimeHintReturn {
  shouldShow: boolean;
  dismiss: () => void;
  reset: () => void;
  isLoading: boolean;
}

/**
 * Hook to manage first-time hints for a specific feature
 * 
 * @param featureId - Unique identifier for the feature (e.g., 'command-palette', 'bulk-actions')
 * @param options - Configuration options
 * @returns Object with shouldShow flag and dismiss function
 */
export function useFirstTimeHint(
  featureId: string,
  options: {
    autoShow?: boolean; // Automatically show on mount (default: true)
    delay?: number; // Delay before showing hint in ms (default: 500)
  } = {},
): UseFirstTimeHintReturn {
  const { autoShow = true, delay = 500 } = options;
  
  const [shouldShow, setShouldShow] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  /**
   * Initialize hint state
   */
  useEffect(() => {
    const states = getHintStates();
    const show = shouldShowHint(featureId, states);
    
    if (show && autoShow) {
      // Delay showing hint to avoid overwhelming user
      const timer = setTimeout(() => {
        setShouldShow(true);
        setIsLoading(false);
      }, delay);
      
      return () => clearTimeout(timer);
    } else {
      setShouldShow(false);
      setIsLoading(false);
    }
  }, [featureId, autoShow, delay]);
  
  /**
   * Dismiss hint permanently
   */
  const dismiss = useCallback(() => {
    markHintAsSeen(featureId);
    setShouldShow(false);
  }, [featureId]);
  
  /**
   * Reset hint (for testing)
   */
  const reset = useCallback(() => {
    resetHint(featureId);
    setShouldShow(true);
  }, [featureId]);
  
  return {
    shouldShow,
    dismiss,
    reset,
    isLoading,
  };
}

/**
 * Hook to check if any hints should be shown
 * Useful for showing a "Tips" indicator
 */
export function useHasUnseenHints(featureIds: string[]): boolean {
  const [hasUnseen, setHasUnseen] = useState(false);
  
  useEffect(() => {
    const states = getHintStates();
    const unseenExists = featureIds.some(id => shouldShowHint(id, states));
    setHasUnseen(unseenExists);
  }, [featureIds]);
  
  return hasUnseen;
}

/**
 * Hook to get hint statistics
 * Useful for analytics or debugging
 */
export function useHintStats() {
  const [stats, setStats] = useState({
    total: 0,
    seen: 0,
    unseen: 0,
    seenList: [] as string[],
  });
  
  useEffect(() => {
    const states = getHintStates();
    const seenList = getSeenHints();
    
    setStats({
      total: Object.keys(states).length,
      seen: seenList.length,
      unseen: Object.keys(states).length - seenList.length,
      seenList,
    });
  }, []);
  
  return stats;
}

/**
 * Utility functions exported for advanced use cases
 */
export const hintUtils = {
  getHintStates,
  saveHintStates,
  shouldShowHint,
  markHintAsSeen,
  resetHint,
  resetAllHints,
  getSeenHints,
};
