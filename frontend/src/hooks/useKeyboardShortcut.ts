/**
 * Keyboard Shortcut Hook
 * 
 * Listen for keyboard shortcuts with support for modifiers.
 * Handles platform differences (Cmd on Mac, Ctrl on Windows/Linux).
 */

'use client';

import { useEffect, useCallback, useRef } from 'react';

interface KeyboardShortcutOptions {
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  preventDefault?: boolean;
  enabled?: boolean;
}

/**
 * Check if the platform is Mac
 */
function isMac(): boolean {
  if (typeof navigator === 'undefined') return false;
  return navigator.platform.toUpperCase().indexOf('MAC') >= 0;
}

/**
 * Normalize key for cross-browser compatibility
 */
function normalizeKey(key: string): string {
  return key.toLowerCase();
}

/**
 * Check if modifiers match
 */
function checkModifiers(
  event: KeyboardEvent,
  options: KeyboardShortcutOptions,
): boolean {
  const {
    ctrl = false,
    meta = false,
    shift = false,
    alt = false,
  } = options;
  
  // On Mac, meta (Cmd) is often used instead of ctrl
  // If both ctrl and meta are specified, check for either based on platform
  const ctrlOrMeta = ctrl && meta;
  const expectedCtrl = ctrlOrMeta ? (isMac() ? event.metaKey : event.ctrlKey) : ctrl;
  const expectedMeta = ctrlOrMeta ? false : meta;
  
  return (
    (expectedCtrl ? event.ctrlKey : !event.ctrlKey) &&
    (expectedMeta ? event.metaKey : !event.metaKey) &&
    (shift ? event.shiftKey : !event.shiftKey) &&
    (alt ? event.altKey : !event.altKey)
  );
}

/**
 * Custom hook for keyboard shortcuts
 * 
 * @param key - The key to listen for (e.g., 'k', 'Enter', 'Escape')
 * @param callback - Function to call when shortcut is triggered
 * @param options - Modifier keys and other options
 * 
 * @example
 * // Listen for Cmd+K or Ctrl+K
 * useKeyboardShortcut('k', openCommandPalette, { meta: true, ctrl: true });
 * 
 * @example
 * // Listen for Shift+?
 * useKeyboardShortcut('?', openHelp, { shift: true });
 * 
 * @example
 * // Listen for Escape
 * useKeyboardShortcut('Escape', closeModal);
 */
export function useKeyboardShortcut(
  key: string,
  callback: (event: KeyboardEvent) => void,
  options: KeyboardShortcutOptions = {},
) {
  const {
    preventDefault = true,
    enabled = true,
  } = options;
  
  const callbackRef = useRef(callback);
  
  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);
  
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;
    
    const normalizedKey = normalizeKey(event.key);
    const targetKey = normalizeKey(key);
    
    // Check if the key matches
    if (normalizedKey !== targetKey) return;
    
    // Check if modifiers match
    if (!checkModifiers(event, options)) return;
    
    // Ignore if user is typing in an input
    const target = event.target as HTMLElement;
    const isInput = target.tagName === 'INPUT' || 
                    target.tagName === 'TEXTAREA' || 
                    target.isContentEditable;
    
    // Allow Escape key even in inputs
    if (isInput && normalizedKey !== 'escape') return;
    
    // Prevent default browser behavior
    if (preventDefault) {
      event.preventDefault();
    }
    
    // Call the callback
    callbackRef.current(event);
  }, [key, options, preventDefault, enabled]);
  
  useEffect(() => {
    if (!enabled) return;
    
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, enabled]);
}

/**
 * Hook for multiple keyboard shortcuts
 * 
 * @example
 * useKeyboardShortcuts({
 *   'k': { callback: openSearch, meta: true, ctrl: true },
 *   'Escape': { callback: closeModal },
 *   '/': { callback: focusSearch }
 * });
 */
export function useKeyboardShortcuts(
  shortcuts: Record<string, {
    callback: (event: KeyboardEvent) => void;
  } & KeyboardShortcutOptions>,
) {
  const shortcutsRef = useRef(shortcuts);
  
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);
  
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const normalizedKey = normalizeKey(event.key);
      
      for (const [key, config] of Object.entries(shortcutsRef.current)) {
        const targetKey = normalizeKey(key);
        
        if (normalizedKey !== targetKey) continue;
        
        const { callback, enabled = true, preventDefault = true, ...modifiers } = config;
        
        if (!enabled) continue;
        if (!checkModifiers(event, modifiers)) continue;
        
        // Ignore if user is typing in an input
        const target = event.target as HTMLElement;
        const isInput = target.tagName === 'INPUT' || 
                        target.tagName === 'TEXTAREA' || 
                        target.isContentEditable;
        
        if (isInput && normalizedKey !== 'escape') continue;
        
        if (preventDefault) {
          event.preventDefault();
        }
        
        callback(event);
        break;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
}

/**
 * Get keyboard shortcut display string
 * 
 * @example
 * getShortcutString('k', { meta: true, ctrl: true }) // "⌘K" on Mac, "Ctrl+K" on Windows
 */
export function getShortcutString(
  key: string,
  options: KeyboardShortcutOptions = {},
): string {
  const { ctrl, meta, shift, alt } = options;
  const parts: string[] = [];
  
  const mac = isMac();
  
  // Handle ctrl/meta
  if (ctrl && meta) {
    parts.push(mac ? '⌘' : 'Ctrl');
  } else {
    if (ctrl) parts.push(mac ? '⌃' : 'Ctrl');
    if (meta) parts.push(mac ? '⌘' : 'Meta');
  }
  
  if (shift) parts.push(mac ? '⇧' : 'Shift');
  if (alt) parts.push(mac ? '⌥' : 'Alt');
  
  // Format key
  const formattedKey = key.length === 1 ? key.toUpperCase() : key;
  parts.push(formattedKey);
  
  return parts.join(mac ? '' : '+');
}
