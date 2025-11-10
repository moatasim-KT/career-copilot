/**
 * Command Palette Provider
 * 
 * Provides global command palette with keyboard shortcut support.
 */

'use client';

import { createContext, useContext, ReactNode } from 'react';

import { LazyCommandPalette } from '@/components/lazy';
import { useCommandPalette } from '@/components/ui/CommandPalette';
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut';

interface CommandPaletteContextValue {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

const CommandPaletteContext = createContext<CommandPaletteContextValue | null>(null);

export function useCommandPaletteContext() {
  const context = useContext(CommandPaletteContext);
  if (!context) {
    throw new Error('useCommandPaletteContext must be used within CommandPaletteProvider');
  }
  return context;
}

interface CommandPaletteProviderProps {
  children: ReactNode;
}

export function CommandPaletteProvider({ children }: CommandPaletteProviderProps) {
  const { isOpen, open, close, toggle } = useCommandPalette();

  // Keyboard shortcut: Cmd+K or Ctrl+K
  useKeyboardShortcut('k', toggle, { meta: true, ctrl: true });

  return (
    <CommandPaletteContext.Provider value={{ isOpen, open, close, toggle }}>
      {children}
      <LazyCommandPalette isOpen={isOpen} onClose={close} />
    </CommandPaletteContext.Provider>
  );
}
