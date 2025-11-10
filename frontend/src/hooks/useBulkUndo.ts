import { useState, useCallback, useRef, useEffect } from 'react';

export interface UndoState<T = any> {
  actionId: string;
  actionName: string;
  previousState: T;
  affectedIds: (string | number)[];
  timestamp: number;
}

export interface UseBulkUndoOptions {
  timeout?: number; // Timeout in milliseconds (default: 5000)
  onUndo?: (state: UndoState) => void | Promise<void>;
}

export function useBulkUndo<T = any>(options: UseBulkUndoOptions = {}) {
  const { timeout = 5000, onUndo } = options;
  
  const [undoState, setUndoState] = useState<UndoState<T> | null>(null);
  const [isUndoing, setIsUndoing] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Clear timeout when component unmounts
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Store action for undo
  const storeUndo = useCallback((
    actionId: string,
    actionName: string,
    previousState: T,
    affectedIds: (string | number)[]
  ) => {
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const newUndoState: UndoState<T> = {
      actionId,
      actionName,
      previousState,
      affectedIds,
      timestamp: Date.now(),
    };

    setUndoState(newUndoState);

    // Set timeout to clear undo state
    timeoutRef.current = setTimeout(() => {
      setUndoState(null);
      timeoutRef.current = null;
    }, timeout);
  }, [timeout]);

  // Perform undo
  const undo = useCallback(async () => {
    if (!undoState || isUndoing) return;

    setIsUndoing(true);

    try {
      if (onUndo) {
        await onUndo(undoState);
      }

      // Clear undo state after successful undo
      setUndoState(null);
      
      // Clear timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    } catch (error) {
      console.error('Undo failed:', error);
      throw error;
    } finally {
      setIsUndoing(false);
    }
  }, [undoState, isUndoing, onUndo]);

  // Clear undo state manually
  const clearUndo = useCallback(() => {
    setUndoState(null);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Calculate remaining time
  const getRemainingTime = useCallback(() => {
    if (!undoState) return 0;
    const elapsed = Date.now() - undoState.timestamp;
    const remaining = Math.max(0, timeout - elapsed);
    return remaining;
  }, [undoState, timeout]);

  return {
    undoState,
    isUndoing,
    storeUndo,
    undo,
    clearUndo,
    getRemainingTime,
    canUndo: undoState !== null && !isUndoing,
  };
}
