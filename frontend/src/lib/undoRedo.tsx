/**
 * Undo/Redo System
 * 
 * Enterprise-grade undo/redo functionality with history management,
 * command pattern, and keyboard shortcuts.
 * 
 * @module lib/undoRedo
 */

'use client';

import { useState, useCallback, useEffect } from 'react';

export interface UndoableAction<T = any> {
  type: string;
  execute: (data: T) => void | Promise<void>;
  undo: (data: T) => void | Promise<void>;
  data: T;
  timestamp: number;
}

export interface UndoRedoState {
  canUndo: boolean;
  canRedo: boolean;
  historySize: number;
  currentIndex: number;
}

/**
 * Undo/Redo Manager
 * 
 * Manages undo/redo history with command pattern
 */
export class UndoRedoManager<T = any> {
  private history: UndoableAction<T>[] = [];
  private currentIndex = -1;
  private maxHistorySize: number;

  constructor(maxHistorySize = 50) {
    this.maxHistorySize = maxHistorySize;
  }

  /**
   * Execute an action and add to history
   */
  async execute(action: Omit<UndoableAction<T>, 'timestamp'>): Promise<void> {
    // Execute the action
    await action.execute(action.data);

    // Remove any actions after current index (redo history)
    this.history = this.history.slice(0, this.currentIndex + 1);

    // Add new action to history
    const undoableAction: UndoableAction<T> = {
      ...action,
      timestamp: Date.now(),
    };
    this.history.push(undoableAction);

    // Maintain max history size
    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
    } else {
      this.currentIndex++;
    }
  }

  /**
   * Undo the last action
   */
  async undo(): Promise<boolean> {
    if (!this.canUndo()) return false;

    const action = this.history[this.currentIndex];
    await action.undo(action.data);
    this.currentIndex--;
    return true;
  }

  /**
   * Redo the next action
   */
  async redo(): Promise<boolean> {
    if (!this.canRedo()) return false;

    this.currentIndex++;
    const action = this.history[this.currentIndex];
    await action.execute(action.data);
    return true;
  }

  /**
   * Check if undo is available
   */
  canUndo(): boolean {
    return this.currentIndex >= 0;
  }

  /**
   * Check if redo is available
   */
  canRedo(): boolean {
    return this.currentIndex < this.history.length - 1;
  }

  /**
   * Get current state
   */
  getState(): UndoRedoState {
    return {
      canUndo: this.canUndo(),
      canRedo: this.canRedo(),
      historySize: this.history.length,
      currentIndex: this.currentIndex,
    };
  }

  /**
   * Clear history
   */
  clear(): void {
    this.history = [];
    this.currentIndex = -1;
  }

  /**
   * Get history
   */
  getHistory(): UndoableAction<T>[] {
    return [...this.history];
  }
}

/**
 * useUndoRedo Hook
 * 
 * React hook for undo/redo functionality
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { execute, undo, redo, canUndo, canRedo } = useUndoRedo();
 *   
 *   const updateName = (newName: string, oldName: string) => {
 *     execute({
 *       type: 'UPDATE_NAME',
 *       execute: () => setName(newName),
 *       undo: () => setName(oldName),
 *       data: { newName, oldName },
 *     });
 *   };
 *   
 *   return (
 *     <>
 *       <button onClick={undo} disabled={!canUndo}>Undo</button>
 *       <button onClick={redo} disabled={!canRedo}>Redo</button>
 *     </>
 *   );
 * }
 * ```
 */
export function useUndoRedo<T = any>(maxHistorySize = 50) {
  const [manager] = useState(() => new UndoRedoManager<T>(maxHistorySize));
  const [state, setState] = useState<UndoRedoState>(manager.getState());

  /**
   * Update state after any operation
   */
  const updateState = useCallback(() => {
    setState(manager.getState());
  }, [manager]);

  /**
   * Execute an action
   */
  const execute = useCallback(
    async (action: Omit<UndoableAction<T>, 'timestamp'>) => {
      await manager.execute(action);
      updateState();
    },
    [manager, updateState],
  );

  /**
   * Undo last action
   */
  const undo = useCallback(async () => {
    await manager.undo();
    updateState();
  }, [manager, updateState]);

  /**
   * Redo next action
   */
  const redo = useCallback(async () => {
    await manager.redo();
    updateState();
  }, [manager, updateState]);

  /**
   * Clear history
   */
  const clear = useCallback(() => {
    manager.clear();
    updateState();
  }, [manager, updateState]);

  /**
   * Get history
   */
  const getHistory = useCallback(() => {
    return manager.getHistory();
  }, [manager]);

  /**
   * Keyboard shortcuts
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Z or Cmd+Z - Undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (state.canUndo) {
          undo();
        }
      }

      // Ctrl+Shift+Z or Cmd+Shift+Z - Redo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        if (state.canRedo) {
          redo();
        }
      }

      // Ctrl+Y or Cmd+Y - Redo (alternative)
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        if (state.canRedo) {
          redo();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state.canUndo, state.canRedo, undo, redo]);

  return {
    execute,
    undo,
    redo,
    clear,
    getHistory,
    canUndo: state.canUndo,
    canRedo: state.canRedo,
    historySize: state.historySize,
    currentIndex: state.currentIndex,
  };
}

/**
 * Undo/Redo Controls Component
 * 
 * @example
 * ```tsx
 * <UndoRedoControls
 *   onUndo={undo}
 *   onRedo={redo}
 *   canUndo={canUndo}
 *   canRedo={canRedo}
 * />
 * ```
 */
export function UndoRedoControls({
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  className = '',
}: {
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  className?: string;
}) {
  return (
    <div className={`flex gap-2 ${className}`}>
      <button
        onClick={onUndo}
        disabled={!canUndo}
        className="inline-flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        title="Undo (Ctrl+Z)"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
          />
        </svg>
        Undo
      </button>
      <button
        onClick={onRedo}
        disabled={!canRedo}
        className="inline-flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        title="Redo (Ctrl+Shift+Z)"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 10H11a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6"
          />
        </svg>
        Redo
      </button>
    </div>
  );
}

/**
 * Common undoable actions for job applications
 */
export const createJobApplicationActions = {
  /**
   * Create action
   */
  create: <T extends { id: string }>(
    item: T,
    onCreate: (item: T) => void | Promise<void>,
    onDelete: (id: string) => void | Promise<void>,
  ): Omit<UndoableAction<{ item: T }>, 'timestamp'> => ({
    type: 'CREATE_APPLICATION',
    execute: async (data) => await onCreate(data.item),
    undo: async (data) => await onDelete(data.item.id),
    data: { item },
  }),

  /**
   * Update action
   */
  update: <T,>(
    id: string,
    oldValue: T,
    newValue: T,
    onUpdate: (id: string, value: T) => void | Promise<void>,
  ): Omit<UndoableAction<{ id: string; oldValue: T; newValue: T }>, 'timestamp'> => ({
    type: 'UPDATE_APPLICATION',
    execute: async (data) => await onUpdate(data.id, data.newValue),
    undo: async (data) => await onUpdate(data.id, data.oldValue),
    data: { id, oldValue, newValue },
  }),

  /**
   * Delete action
   */
  delete: <T extends { id: string },>(
    item: T,
    onDelete: (id: string) => void | Promise<void>,
    onRestore: (item: T) => void | Promise<void>,
  ): Omit<UndoableAction<{ item: T }>, 'timestamp'> => ({
    type: 'DELETE_APPLICATION',
    execute: async (data) => await onDelete(data.item.id),
    undo: async (data) => await onRestore(data.item),
    data: { item },
  }),

  /**
   * Bulk action
   */
  bulk: <T extends { id: string }>(
    items: T[],
    operation: (items: T[]) => void | Promise<void>,
    reverseOperation: (items: T[]) => void | Promise<void>,
  ): Omit<UndoableAction<{ items: T[] }>, 'timestamp'> => ({
    type: 'BULK_OPERATION',
    execute: async (data) => await operation(data.items),
    undo: async (data) => await reverseOperation(data.items),
    data: { items },
  }),
};
