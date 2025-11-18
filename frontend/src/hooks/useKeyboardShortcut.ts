/**
 * Keyboard Shortcut Hook
 * 
 * Adapter hook that uses the centralized KeyboardShortcutsManager.
 * Handles platform differences (Cmd on Mac, Ctrl on Windows/Linux).
 */

'use client';

import { useEffect, useRef } from 'react';
import { useKeyboardShortcut as useLibKeyboardShortcut } from '@/lib/keyboardShortcuts';

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
 * Custom hook for keyboard shortcuts
 * 
 * @param key - The key to listen for (e.g., 'k', 'Enter', 'Escape')
 * @param callback - Function to call when shortcut is triggered
 * @param options - Modifier keys and other options
 */
export function useKeyboardShortcut(
  key: string,
  callback: (event: KeyboardEvent) => void,
  options: KeyboardShortcutOptions = {},
) {
  const {
    ctrl = false,
    meta = false,
    shift = false,
    alt = false,
    preventDefault = true,
    enabled = true,
  } = options;

  // Handle platform-specific modifiers logic (Cmd+K vs Ctrl+K)
  // If both ctrl and meta are true, it means "Primary Modifier" (Cmd on Mac, Ctrl on Windows)
  const isMacPlatform = isMac();
  const ctrlOrMeta = ctrl && meta;

  const effectiveCtrl = ctrlOrMeta ? !isMacPlatform : ctrl;
  const effectiveMeta = ctrlOrMeta ? isMacPlatform : meta;

  useLibKeyboardShortcut({
    key,
    ctrl: effectiveCtrl,
    meta: effectiveMeta,
    shift,
    alt,
    preventDefault,
    enabled,
    description: 'Registered via useKeyboardShortcut hook',
    handler: callback,
  });
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
  // This is a simplified adapter. For full robustness, we should register each individually.
  // But since we are moving to the lib manager, let's just loop and call the single hook logic
  // or better, use the lib's useKeyboardShortcuts if it supports this structure.
  // The lib's useKeyboardShortcuts takes an array, not a record.

  // Let's just implement it using the lib manager directly for now to keep it clean.
  // We can't call hooks inside loops easily.

  // Actually, let's just leave this one as is but use the manager?
  // No, that's messy. Let's just remove the implementation and say "Not implemented" or fix it properly.
  // The user wants a comprehensive fix.

  // Let's map the record to an array and use the lib's hook if possible, 
  // but hooks rules prevent conditional hook calls.

  // So we will just use the manager directly in a useEffect.

  const { useKeyboardShortcuts: useLibKeyboardShortcuts } = require('@/lib/keyboardShortcuts');

  const shortcutsList = Object.entries(shortcuts).map(([key, config]) => {
    const { callback, enabled = true, preventDefault = true, ctrl, meta, shift, alt } = config;

    const isMacPlatform = isMac();
    const ctrlOrMeta = ctrl && meta;
    const effectiveCtrl = ctrlOrMeta ? !isMacPlatform : ctrl;
    const effectiveMeta = ctrlOrMeta ? isMacPlatform : meta;

    return {
      key,
      ctrl: effectiveCtrl,
      meta: effectiveMeta,
      shift,
      alt,
      preventDefault,
      enabled,
      description: 'Registered via useKeyboardShortcuts hook',
      handler: callback,
    };
  });

  useLibKeyboardShortcuts(shortcutsList);
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
