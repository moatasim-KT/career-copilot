/**
 * Dark Mode Hook
 * 
 * Manages theme state with localStorage persistence and system preference detection.
 * Priority: localStorage > system preference > default (light)
 */

'use client';

import { useEffect, useState, useCallback } from 'react';

import { logger } from '@/lib/logger';
import { DARK_CLASS, THEME_STORAGE_KEY } from '@/lib/theme/constants';


type Theme = 'light' | 'dark' | 'system';
type ResolvedTheme = 'light' | 'dark';

interface DarkModeHook {
  isDark: boolean;
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  toggle: () => void;
  setDark: () => void;
  setLight: () => void;
  setSystem: () => void;
  setTheme: (theme: Theme) => void;
}

const STORAGE_KEY = THEME_STORAGE_KEY;

/**
 * Get system color scheme preference
 */
function getSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined') return 'light';

  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

/**
 * Get stored theme from localStorage
 */
function getStoredTheme(): Theme | null {
  if (typeof window === 'undefined') return null;

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
  } catch (error) {
    logger.error('Failed to read theme from localStorage:', error);
  }

  return null;
}

/**
 * Resolve theme to actual light/dark value
 */
function resolveTheme(theme: Theme): ResolvedTheme {
  if (theme === 'system') {
    return getSystemTheme();
  }
  return theme;
}

/**
 * Apply theme to document
 */
function applyTheme(resolvedTheme: ResolvedTheme) {
  if (typeof document === 'undefined') return;

  const root = document.documentElement;

  if (resolvedTheme === 'dark') {
    root.classList.add(DARK_CLASS);
  } else {
    root.classList.remove(DARK_CLASS);
  }

  // Set color-scheme for native browser elements
  root.style.colorScheme = resolvedTheme;
}

/**
 * Store theme in localStorage
 */
function storeTheme(theme: Theme) {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem(STORAGE_KEY, theme);

    // Emit storage event for cross-tab synchronization
    window.dispatchEvent(new StorageEvent('storage', {
      key: STORAGE_KEY,
      newValue: theme,
      storageArea: localStorage,
    }));
  } catch (error) {
    logger.error('Failed to store theme in localStorage:', error);
  }
}

/**
 * Custom hook for dark mode management
 */
export function useDarkMode(): DarkModeHook {
  // Initialize theme from localStorage or system preference
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = getStoredTheme();
    return stored || 'system';
  });

  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() => {
    return resolveTheme(theme);
  });

  const isDark = resolvedTheme === 'dark';

  /**
   * Update theme and apply changes
   */
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    const resolved = resolveTheme(newTheme);
    setResolvedTheme(resolved);
    applyTheme(resolved);
    storeTheme(newTheme);
  }, []);

  /**
   * Toggle between light and dark
   */
  const toggle = useCallback(() => {
    setTheme(isDark ? 'light' : 'dark');
  }, [isDark, setTheme]);

  /**
   * Set dark theme
   */
  const setDark = useCallback(() => {
    setTheme('dark');
  }, [setTheme]);

  /**
   * Set light theme
   */
  const setLight = useCallback(() => {
    setTheme('light');
  }, [setTheme]);

  /**
   * Set system theme
   */
  const setSystem = useCallback(() => {
    setTheme('system');
  }, [setTheme]);

  /**
   * Listen for system theme changes
   */
  useEffect(() => {
    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      const newResolvedTheme = e.matches ? 'dark' : 'light';
      setResolvedTheme(newResolvedTheme);
      applyTheme(newResolvedTheme);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
    // Legacy browsers
    else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [theme]);

  /**
   * Listen for storage changes (cross-tab synchronization)
   */
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key !== STORAGE_KEY) return;

      const newTheme = e.newValue as Theme | null;
      if (newTheme && (newTheme === 'light' || newTheme === 'dark' || newTheme === 'system')) {
        setThemeState(newTheme);
        const resolved = resolveTheme(newTheme);
        setResolvedTheme(resolved);
        applyTheme(resolved);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  /**
   * Apply theme on mount
   */
  useEffect(() => {
    applyTheme(resolvedTheme);
  }, [resolvedTheme]);

  return {
    isDark,
    theme,
    resolvedTheme,
    toggle,
    setDark,
    setLight,
    setSystem,
    setTheme,
  };
}
