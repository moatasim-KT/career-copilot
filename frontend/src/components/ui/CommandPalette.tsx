/**
 * Command Palette Component
 * 
 * Keyboard-driven command interface inspired by Linear, Raycast, and Spotlight.
 * Provides quick access to navigation, actions, and search.
 */

'use client';

import { Command } from 'cmdk';
import { Search, Clock, X, Briefcase, FileText, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';

import { useDebouncedValue } from '@/hooks/useDebouncedSearch';
import { useSearchApplications } from '@/hooks/useSearchApplications';
import { useSearchJobs } from '@/hooks/useSearchJobs';
import { backdropVariants, modalVariants } from '@/lib/animations';
import type { Job, Application } from '@/lib/api/api';
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
import { m, AnimatePresence } from '@/lib/motion';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [commands] = useState(() => createCommandRegistry(router));
  const [recentCommandIds, setRecentCommandIds] = useState<string[]>([]);

  // Debounce search for API calls (300ms delay)
  const debouncedSearch = useDebouncedValue(search, 300);

  // Dynamic search for jobs and applications
  const { data: searchedJobs = [], isLoading: isLoadingJobs } = useSearchJobs(
    debouncedSearch,
    isOpen && debouncedSearch.length >= 2,
  );
  const { data: searchedApplications = [], isLoading: isLoadingApplications } = useSearchApplications(
    debouncedSearch,
    isOpen && debouncedSearch.length >= 2,
  );

  const isSearching = isLoadingJobs || isLoadingApplications;

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

  // Navigate to job detail
  const navigateToJob = useCallback(
    (jobId: number) => {
      router.push(`/jobs/${jobId}`);
      onClose();
    },
    [router, onClose],
  );

  // Navigate to application detail
  const navigateToApplication = useCallback(
    (appId: number) => {
      router.push(`/applications/${appId}`);
      onClose();
    },
    [router, onClose],
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
          <m.div
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[1040]"
            onClick={onClose}
          />

          {/* Command Palette */}
          <div className="fixed inset-0 z-[1050] flex items-start justify-center pt-[15vh] px-4">
            <m.div
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
                    {isSearching ? (
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Searching...</span>
                      </div>
                    ) : (
                      'No results found.'
                    )}
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

                  {/* Dynamic Search Results - Jobs */}
                  {debouncedSearch.length >= 2 && searchedJobs.length > 0 && (
                    <Command.Group
                      heading={
                        <div className="px-2 py-1.5 text-xs font-medium text-neutral-500 dark:text-neutral-400 flex items-center gap-2">
                          <Briefcase className="w-3.5 h-3.5" />
                          Jobs
                        </div>
                      }
                      className="mb-2"
                    >
                      {searchedJobs.map((job) => (
                        <JobSearchItem
                          key={`job-${job.id}`}
                          job={job}
                          onSelect={() => navigateToJob(job.id)}
                        />
                      ))}
                    </Command.Group>
                  )}

                  {/* Dynamic Search Results - Applications */}
                  {debouncedSearch.length >= 2 && searchedApplications.length > 0 && (
                    <Command.Group
                      heading={
                        <div className="px-2 py-1.5 text-xs font-medium text-neutral-500 dark:text-neutral-400 flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5" />
                          Applications
                        </div>
                      }
                      className="mb-2"
                    >
                      {searchedApplications.map((app) => (
                        <ApplicationSearchItem
                          key={`app-${app.id}`}
                          application={app}
                          onSelect={() => navigateToApplication(app.id)}
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
            </m.div>
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
 * Job Search Item Component
 */
interface JobSearchItemProps {
  job: Job;
  onSelect: () => void;
}

function JobSearchItem({ job, onSelect }: JobSearchItemProps) {
  return (
    <Command.Item
      value={`job-${job.id}`}
      onSelect={onSelect}
      className="flex items-start gap-3 px-3 py-2.5 rounded-lg cursor-pointer
        text-neutral-700 dark:text-neutral-300
        hover:bg-neutral-100 dark:hover:bg-neutral-800
        data-[selected=true]:bg-primary-50 dark:data-[selected=true]:bg-primary-900/20
        data-[selected=true]:text-primary-700 dark:data-[selected=true]:text-primary-300
        transition-colors"
    >
      <Briefcase className="w-4 h-4 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{job.title}</div>
        <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
          {job.company}
          {job.location && ` • ${job.location}`}
          {job.remote && ' • Remote'}
        </div>
      </div>
      {job.match_score !== undefined && job.match_score > 0 && (
        <div className="flex-shrink-0 text-xs font-medium text-primary-600 dark:text-primary-400">
          {Math.round(job.match_score)}% match
        </div>
      )}
    </Command.Item>
  );
}

/**
 * Application Search Item Component
 */
interface ApplicationSearchItemProps {
  application: Application;
  onSelect: () => void;
}

function ApplicationSearchItem({ application, onSelect }: ApplicationSearchItemProps) {
  const statusColors: Record<string, string> = {
    interested: 'text-neutral-600 dark:text-neutral-400',
    applied: 'text-blue-600 dark:text-blue-400',
    interview: 'text-purple-600 dark:text-purple-400',
    offer: 'text-green-600 dark:text-green-400',
    rejected: 'text-red-600 dark:text-red-400',
    accepted: 'text-emerald-600 dark:text-emerald-400',
    declined: 'text-orange-600 dark:text-orange-400',
  };

  const statusColor = statusColors[application.status] || statusColors.interested;

  return (
    <Command.Item
      value={`app-${application.id}`}
      onSelect={onSelect}
      className="flex items-start gap-3 px-3 py-2.5 rounded-lg cursor-pointer
        text-neutral-700 dark:text-neutral-300
        hover:bg-neutral-100 dark:hover:bg-neutral-800
        data-[selected=true]:bg-primary-50 dark:data-[selected=true]:bg-primary-900/20
        data-[selected=true]:text-primary-700 dark:data-[selected=true]:text-primary-300
        transition-colors"
    >
      <FileText className="w-4 h-4 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">
          {application.job?.title || 'Application'}
        </div>
        <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
          {application.job?.company || 'Unknown Company'}
        </div>
      </div>
      <div className={`flex-shrink-0 text-xs font-medium capitalize ${statusColor}`}>
        {application.status}
      </div>
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
