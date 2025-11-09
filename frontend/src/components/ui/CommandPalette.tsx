/**
 * Command Palette Component
 * 
 * Keyboard-driven command interface inspired by Linear, Raycast, and Spotlight.
 * Provides quick access to navigation, actions, and search.
 */

'use client';

import { Command } from 'cmdk';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Clock, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';

import {
  createCommandRegistry,
  searchCommands,
  groupCommandsByCategory,
  getCategoryLabel,
  getRecentCommands,
  addRecentCommand,
  clearRecentCommands,
  type Command as CommandType,
} from '@/lib/commands';
import { backdropVariants, modalVariants } from '@/lib/animations';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [commands] = useState(() => createCommandRegistry(router));
  const [recentCommandIds, setRecentCommandIds] = useState<string[]>([]);

  // Load recent commands on mount
  useEffect(() => {
    if (isOpen) {
      setRecentCommandIds(getRecentCommands());
    }
  }, [isOpen]);

  // Reset search when closing
  useEffect(() => {
    if (!isOpen) {
      setSearch('');
    }
  }, [isOpen]);

  // Filter commands based on search
  const filteredCommands = searchCommands(commands, search);
  const groupedCommands = groupCommandsByCategory(filteredCommands);

  // Get recent commands
  const recentCommands = recentCommandIds
    .map((id) => commands.find((cmd) => cmd.id === id))
    .filter(Boolean) as CommandType[];

  // Execute command
  const executeCommand = useCallback(
    (command: CommandType) => {
      addRecentCommand(command.id);
      setRecentCommandIds(getRecentCommands());
      command.action();
      onClose();
    },
    [onClose],
  );

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Close on Escape
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[1040]"
            onClick={onClose}
          />

          {/* Command Palette */}
          <div className="fixed inset-0 z-[1050] flex items-start justify-center pt-[15vh] px-4">
            <motion.div
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="w-full max-w-2xl"
            >
              <Command
                className="glass rounded-xl shadow-2xl overflow-hidden border border-neutral-200 dark:border-neutral-700"
                shouldFilter={false}
              >
                {/* Search Input */}
                <div className="flex items-center gap-3 px-4 py-3 border-b border-neutral-200 dark:border-neutral-700">
                  <Search className="w-5 h-5 text-neutral-400 flex-shrink-0" />
                  <Command.Input
                    value={search}
                    onValueChange={setSearch}
                    placeholder="Type a command or search..."
                    className="flex-1 bg-transparent border-none outline-none text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400"
                    autoFocus
                  />
                  {search && (
                    <button
                      onClick={() => setSearch('')}
                      className="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                      aria-label="Clear search"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                  <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs font-mono text-neutral-500 bg-neutral-100 dark:bg-neutral-800 rounded">
                    ESC
                  </kbd>
                </div>

                {/* Command List */}
                <Command.List className="max-h-[400px] overflow-y-auto p-2">
                  <Command.Empty className="py-12 text-center text-sm text-neutral-500">
                    No results found.
                  </Command.Empty>

                  {/* Recent Commands */}
                  {!search && recentCommands.length > 0 && (
                    <Command.Group
                      heading={
                        <div className="flex items-center justify-between px-2 py-1.5">
                          <div className="flex items-center gap-2 text-xs font-medium text-neutral-500 dark:text-neutral-400">
                            <Clock className="w-3.5 h-3.5" />
                            Recent
                          </div>
                          <button
                            onClick={() => {
                              clearRecentCommands();
                              setRecentCommandIds([]);
                            }}
                            className="text-xs text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                          >
                            Clear
                          </button>
                        </div>
                      }
                      className="mb-2"
                    >
                      {recentCommands.map((command) => (
                        <CommandItem
                          key={command.id}
                          command={command}
                          onSelect={() => executeCommand(command)}
                        />
                      ))}
                    </Command.Group>
                  )}

                  {/* Grouped Commands */}
                  {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
                    <Command.Group
                      key={category}
                      heading={
                        <div className="px-2 py-1.5 text-xs font-medium text-neutral-500 dark:text-neutral-400">
                          {getCategoryLabel(category)}
                        </div>
                      }
                      className="mb-2"
                    >
                      {categoryCommands.map((command) => (
                        <CommandItem
                          key={command.id}
                          command={command}
                          onSelect={() => executeCommand(command)}
                        />
                      ))}
                    </Command.Group>
                  ))}
                </Command.List>

                {/* Footer */}
                <div className="flex items-center justify-between px-4 py-2 border-t border-neutral-200 dark:border-neutral-700 text-xs text-neutral-500">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded font-mono">↑↓</kbd>
                      <span>Navigate</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded font-mono">↵</kbd>
                      <span>Select</span>
                    </div>
                  </div>
                  <div className="hidden sm:block text-neutral-400">
                    Press <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded font-mono">⌘K</kbd> to open
                  </div>
                </div>
              </Command>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}

/**
 * Command Item Component
 */
interface CommandItemProps {
  command: CommandType;
  onSelect: () => void;
}

function CommandItem({ command, onSelect }: CommandItemProps) {
  const Icon = command.icon;

  return (
    <Command.Item
      value={command.id}
      onSelect={onSelect}
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer
        text-neutral-700 dark:text-neutral-300
        hover:bg-neutral-100 dark:hover:bg-neutral-800
        data-[selected=true]:bg-primary-50 dark:data-[selected=true]:bg-primary-900/20
        data-[selected=true]:text-primary-700 dark:data-[selected=true]:text-primary-300
        transition-colors"
    >
      <Icon className="w-4 h-4 flex-shrink-0" />
      <span className="flex-1 text-sm font-medium">{command.label}</span>
      {command.shortcut && (
        <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-xs font-mono text-neutral-500 bg-neutral-100 dark:bg-neutral-800 rounded">
          {command.shortcut.split(' ').map((key, i) => (
            <span key={i}>
              {i > 0 && <span className="mx-0.5">→</span>}
              {key}
            </span>
          ))}
        </kbd>
      )}
    </Command.Item>
  );
}

/**
 * Command Palette Provider Hook
 */
export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

  return {
    isOpen,
    open,
    close,
    toggle,
  };
}
