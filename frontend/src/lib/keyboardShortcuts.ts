/**
 * Keyboard Shortcuts System
 * 
 * Enterprise-grade keyboard shortcuts manager with conflict detection,
 * help dialog, and customizable bindings.
 * 
 * @module lib/keyboardShortcuts
 */

'use client';

import { useEffect, useCallback, useRef } from 'react';

export interface KeyboardShortcut {
    key: string;
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    meta?: boolean;
    description: string;
    category?: string;
    handler: (event: KeyboardEvent) => void;
    preventDefault?: boolean;
    enabled?: boolean;
}

export interface ShortcutCategory {
    name: string;
    shortcuts: KeyboardShortcut[];
}

/**
 * Keyboard shortcuts manager
 */
class KeyboardShortcutsManager {
    private shortcuts: Map<string, KeyboardShortcut> = new Map();
    private listeners: Set<(event: KeyboardEvent) => void> = new Set();

    /**
     * Register a keyboard shortcut
     */
    register(shortcut: KeyboardShortcut): () => void {
        const key = this.getShortcutKey(shortcut);

        if (this.shortcuts.has(key)) {
            console.warn(`Shortcut ${key} is already registered`);
        }

        this.shortcuts.set(key, shortcut);

        return () => this.unregister(key);
    }

    /**
     * Unregister a keyboard shortcut
     */
    unregister(key: string): void {
        this.shortcuts.delete(key);
    }

    /**
     * Get shortcut key string
     */
    private getShortcutKey(shortcut: KeyboardShortcut | Partial<KeyboardShortcut> & { key: string }): string {
        const parts: string[] = [];
        if (shortcut.ctrl) parts.push('Ctrl');
        if (shortcut.shift) parts.push('Shift');
        if (shortcut.alt) parts.push('Alt');
        if (shortcut.meta) parts.push('Meta');
        parts.push(shortcut.key.toUpperCase());
        return parts.join('+');
    }

    /**
     * Check if event matches shortcut
     */
    private matchesShortcut(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
        return (
            event.key.toLowerCase() === shortcut.key.toLowerCase() &&
            !!event.ctrlKey === !!shortcut.ctrl &&
            !!event.shiftKey === !!shortcut.shift &&
            !!event.altKey === !!shortcut.alt &&
            !!event.metaKey === !!shortcut.meta
        );
    }

    /**
     * Handle keyboard event
     */
    handleKeyDown = (event: KeyboardEvent): void => {
        // Don't handle shortcuts when typing in input fields
        const target = event.target as HTMLElement;
        if (
            target.tagName === 'INPUT' ||
            target.tagName === 'TEXTAREA' ||
            target.isContentEditable
        ) {
            return;
        }

        for (const shortcut of this.shortcuts.values()) {
            if (shortcut.enabled !== false && this.matchesShortcut(event, shortcut)) {
                if (shortcut.preventDefault !== false) {
                    event.preventDefault();
                }
                shortcut.handler(event);
                break;
            }
        }

        // Notify listeners
        this.listeners.forEach((listener) => listener(event));
    };

    /**
     * Add event listener
     */
    addEventListener(listener: (event: KeyboardEvent) => void): () => void {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    /**
     * Get all registered shortcuts
     */
    getAllShortcuts(): KeyboardShortcut[] {
        return Array.from(this.shortcuts.values());
    }

    /**
     * Get shortcuts by category
     */
    getShortcutsByCategory(): ShortcutCategory[] {
        const categories = new Map<string, KeyboardShortcut[]>();

        for (const shortcut of this.shortcuts.values()) {
            const category = shortcut.category || 'General';
            if (!categories.has(category)) {
                categories.set(category, []);
            }
            categories.get(category)!.push(shortcut);
        }

        return Array.from(categories.entries()).map(([name, shortcuts]) => ({
            name,
            shortcuts,
        }));
    }

    /**
     * Format shortcut for display
     */
    formatShortcut(shortcut: KeyboardShortcut): string {
        return this.getShortcutKey(shortcut);
    }
}

// Global instance
const shortcutsManager = new KeyboardShortcutsManager();

/**
 * Initialize keyboard shortcuts system
 */
export function initKeyboardShortcuts(): void {
    if (typeof window !== 'undefined') {
        window.addEventListener('keydown', shortcutsManager.handleKeyDown);
    }
}

/**
 * Cleanup keyboard shortcuts system
 */
export function cleanupKeyboardShortcuts(): void {
    if (typeof window !== 'undefined') {
        window.removeEventListener('keydown', shortcutsManager.handleKeyDown);
    }
}

/**
 * useKeyboardShortcut Hook
 * 
 * Register a keyboard shortcut
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   useKeyboardShortcut({
 *     key: 's',
 *     ctrl: true,
 *     description: 'Save',
 *     handler: handleSave,
 *   });
 * }
 * ```
 */
export function useKeyboardShortcut(shortcut: KeyboardShortcut): void {
    const shortcutRef = useRef(shortcut);
    shortcutRef.current = shortcut;

    useEffect(() => {
        const unregister = shortcutsManager.register(shortcutRef.current);
        return unregister;
    }, []);
}

/**
 * useKeyboardShortcuts Hook
 * 
 * Register multiple keyboard shortcuts
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   useKeyboardShortcuts([
 *     { key: 's', ctrl: true, description: 'Save', handler: handleSave },
 *     { key: 'n', ctrl: true, description: 'New', handler: handleNew },
 *   ]);
 * }
 * ```
 */
export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]): void {
    const shortcutsRef = useRef(shortcuts);
    shortcutsRef.current = shortcuts;

    useEffect(() => {
        const unregisterFns = shortcutsRef.current.map((shortcut) =>
            shortcutsManager.register(shortcut),
        );
        return () => unregisterFns.forEach((fn) => fn());
    }, []);
}

/**
 * Get all registered shortcuts
 */
export function getAllShortcuts(): KeyboardShortcut[] {
    return shortcutsManager.getAllShortcuts();
}

/**
 * Get shortcuts by category
 */
export function getShortcutsByCategory(): ShortcutCategory[] {
    return shortcutsManager.getShortcutsByCategory();
}

/**
 * Format shortcut for display
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
    return shortcutsManager.formatShortcut(shortcut);
}

/**
 * Common keyboard shortcuts
 */
export const COMMON_SHORTCUTS = {
    SAVE: { key: 's', ctrl: true, description: 'Save' },
    NEW: { key: 'n', ctrl: true, description: 'Create new' },
    SEARCH: { key: 'k', ctrl: true, description: 'Open search' },
    HELP: { key: '?', shift: true, description: 'Show keyboard shortcuts' },
    CLOSE: { key: 'Escape', description: 'Close dialog/modal' },
    REFRESH: { key: 'r', ctrl: true, description: 'Refresh' },
    DELETE: { key: 'Delete', description: 'Delete selected item' },
    SELECT_ALL: { key: 'a', ctrl: true, description: 'Select all' },
    UNDO: { key: 'z', ctrl: true, description: 'Undo' },
    REDO: { key: 'y', ctrl: true, description: 'Redo' },
} as const;
