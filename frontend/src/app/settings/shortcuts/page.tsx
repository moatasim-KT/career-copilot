/**
 * Keyboard Shortcuts Reference Page
 * 
 * Displays all available keyboard shortcuts:
 * - Searchable shortcut list
 * - Grouped by category
 * - Customize shortcuts (optional future feature)
 */

'use client';

import {
  Search,
  Command,
  Navigation,
  Zap,
  Settings,
  FileText,
  Briefcase,
  BarChart3,
  Keyboard,
} from 'lucide-react';
import { useState, useMemo } from 'react';

import Card2 from '@/components/ui/Card2';
import Input2 from '@/components/ui/Input2';

interface KeyboardShortcut {
  id: string;
  category: string;
  action: string;
  keys: string[];
  description: string;
}

const shortcuts: KeyboardShortcut[] = [
  // Navigation
  {
    id: 'nav-dashboard',
    category: 'Navigation',
    action: 'Go to Dashboard',
    keys: ['g', 'd'],
    description: 'Navigate to the dashboard page',
  },
  {
    id: 'nav-jobs',
    category: 'Navigation',
    action: 'Go to Jobs',
    keys: ['g', 'j'],
    description: 'Navigate to the jobs page',
  },
  {
    id: 'nav-applications',
    category: 'Navigation',
    action: 'Go to Applications',
    keys: ['g', 'a'],
    description: 'Navigate to the applications page',
  },
  {
    id: 'nav-recommendations',
    category: 'Navigation',
    action: 'Go to Recommendations',
    keys: ['g', 'r'],
    description: 'Navigate to the recommendations page',
  },
  {
    id: 'nav-analytics',
    category: 'Navigation',
    action: 'Go to Analytics',
    keys: ['g', 'n'],
    description: 'Navigate to the analytics page',
  },
  {
    id: 'nav-settings',
    category: 'Navigation',
    action: 'Go to Settings',
    keys: ['g', 's'],
    description: 'Navigate to the settings page',
  },

  // Global Actions
  {
    id: 'command-palette',
    category: 'Global',
    action: 'Open Command Palette',
    keys: ['⌘', 'k'],
    description: 'Open the command palette for quick actions',
  },
  {
    id: 'search',
    category: 'Global',
    action: 'Focus Search',
    keys: ['/'],
    description: 'Focus the search input',
  },
  {
    id: 'toggle-theme',
    category: 'Global',
    action: 'Toggle Theme',
    keys: ['⌘', 'd'],
    description: 'Switch between light and dark mode',
  },
  {
    id: 'notifications',
    category: 'Global',
    action: 'Open Notifications',
    keys: ['⌘', 'n'],
    description: 'Open the notification center',
  },
  {
    id: 'help',
    category: 'Global',
    action: 'Open Help',
    keys: ['?'],
    description: 'Open the help center',
  },

  // Jobs Page
  {
    id: 'new-job',
    category: 'Jobs',
    action: 'Create New Job',
    keys: ['c'],
    description: 'Open dialog to create a new job',
  },
  {
    id: 'filter-jobs',
    category: 'Jobs',
    action: 'Open Filters',
    keys: ['f'],
    description: 'Open the filter panel',
  },
  {
    id: 'advanced-search',
    category: 'Jobs',
    action: 'Advanced Search',
    keys: ['⌘', 'f'],
    description: 'Open advanced search builder',
  },
  {
    id: 'refresh-jobs',
    category: 'Jobs',
    action: 'Refresh Jobs',
    keys: ['r'],
    description: 'Refresh the jobs list',
  },

  // Applications Page
  {
    id: 'new-application',
    category: 'Applications',
    action: 'Create New Application',
    keys: ['c'],
    description: 'Open dialog to create a new application',
  },
  {
    id: 'filter-applications',
    category: 'Applications',
    action: 'Open Filters',
    keys: ['f'],
    description: 'Open the filter panel',
  },
  {
    id: 'kanban-view',
    category: 'Applications',
    action: 'Toggle Kanban View',
    keys: ['k'],
    description: 'Switch to kanban board view',
  },
  {
    id: 'table-view',
    category: 'Applications',
    action: 'Toggle Table View',
    keys: ['t'],
    description: 'Switch to table view',
  },

  // Table Navigation
  {
    id: 'select-row',
    category: 'Table',
    action: 'Select Row',
    keys: ['Space'],
    description: 'Select or deselect the focused row',
  },
  {
    id: 'select-all',
    category: 'Table',
    action: 'Select All',
    keys: ['⌘', 'a'],
    description: 'Select all rows in the table',
  },
  {
    id: 'next-row',
    category: 'Table',
    action: 'Next Row',
    keys: ['↓'],
    description: 'Move focus to the next row',
  },
  {
    id: 'prev-row',
    category: 'Table',
    action: 'Previous Row',
    keys: ['↑'],
    description: 'Move focus to the previous row',
  },
  {
    id: 'open-row',
    category: 'Table',
    action: 'Open Row',
    keys: ['Enter'],
    description: 'Open the focused row details',
  },

  // Editing
  {
    id: 'save',
    category: 'Editing',
    action: 'Save',
    keys: ['⌘', 's'],
    description: 'Save the current form or changes',
  },
  {
    id: 'cancel',
    category: 'Editing',
    action: 'Cancel',
    keys: ['Esc'],
    description: 'Cancel the current action or close modal',
  },
  {
    id: 'undo',
    category: 'Editing',
    action: 'Undo',
    keys: ['⌘', 'z'],
    description: 'Undo the last action',
  },
];

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  Navigation,
  Global: Command,
  Jobs: Briefcase,
  Applications: FileText,
  Table: BarChart3,
  Editing: Zap,
};

function KeyBadge({ keyName }: { keyName: string }) {
  return (
    <kbd className="inline-flex items-center justify-center min-w-[2rem] h-8 px-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 bg-neutral-100 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded shadow-sm">
      {keyName}
    </kbd>
  );
}

export default function KeyboardShortcutsPage() {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter shortcuts based on search query
  const filteredShortcuts = useMemo(() => {
    if (!searchQuery) return shortcuts;

    const query = searchQuery.toLowerCase();
    return shortcuts.filter(
      shortcut =>
        shortcut.action.toLowerCase().includes(query) ||
        shortcut.description.toLowerCase().includes(query) ||
        shortcut.category.toLowerCase().includes(query) ||
        shortcut.keys.some(key => key.toLowerCase().includes(query)),
    );
  }, [searchQuery]);

  // Group shortcuts by category
  const groupedShortcuts = useMemo(() => {
    const groups: Record<string, KeyboardShortcut[]> = {};
    filteredShortcuts.forEach(shortcut => {
      if (!groups[shortcut.category]) {
        groups[shortcut.category] = [];
      }
      groups[shortcut.category].push(shortcut);
    });
    return groups;
  }, [filteredShortcuts]);

  const categories = Object.keys(groupedShortcuts).sort();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
          Keyboard Shortcuts
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          Master these shortcuts to navigate Career Copilot like a pro
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
        <Input2
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search shortcuts..."
          className="pl-10"
        />
      </div>

      {/* Platform Note */}
      <Card2 className="p-4 bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <Keyboard className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-neutral-700 dark:text-neutral-300">
            <p className="font-medium mb-1">Platform Note</p>
            <p>
              On Windows and Linux, use <KeyBadge keyName="Ctrl" /> instead of <KeyBadge keyName="⌘" /> (Command).
              All shortcuts work the same way across platforms.
            </p>
          </div>
        </div>
      </Card2>

      {/* Shortcuts by Category */}
      {categories.length > 0 ? (
        <div className="space-y-6">
          {categories.map(category => {
            const Icon = categoryIcons[category] || Command;
            const categoryShortcuts = groupedShortcuts[category];

            return (
              <Card2 key={category} className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                    {category}
                  </h3>
                </div>

                <div className="space-y-3">
                  {categoryShortcuts.map(shortcut => (
                    <div
                      key={shortcut.id}
                      className="flex items-start justify-between gap-4 p-3 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                          {shortcut.action}
                        </div>
                        <div className="text-xs text-neutral-600 dark:text-neutral-400">
                          {shortcut.description}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {shortcut.keys.map((key, index) => (
                          <span key={index} className="flex items-center gap-1">
                            <KeyBadge keyName={key} />
                            {index < shortcut.keys.length - 1 && (
                              <span className="text-neutral-400 dark:text-neutral-500 text-sm">
                                then
                              </span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </Card2>
            );
          })}
        </div>
      ) : (
        <Card2 className="p-12 text-center">
          <Search className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            No shortcuts found
          </h3>
          <p className="text-neutral-600 dark:text-neutral-400">
            Try searching with different keywords
          </p>
        </Card2>
      )}

      {/* Customization Note */}
      <Card2 className="p-4 bg-neutral-50 dark:bg-neutral-800/50">
        <div className="flex items-start gap-3">
          <Settings className="w-5 h-5 text-neutral-500 dark:text-neutral-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-neutral-700 dark:text-neutral-300">
            <p className="font-medium mb-1">Custom Shortcuts</p>
            <p>
              The ability to customize keyboard shortcuts is coming soon. Stay tuned for updates!
            </p>
          </div>
        </div>
      </Card2>

      {/* Tips */}
      <Card2 className="p-6">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
          Pro Tips
        </h3>
        <ul className="space-y-3 text-sm text-neutral-700 dark:text-neutral-300">
          <li className="flex items-start gap-3">
            <span className="text-primary-600 dark:text-primary-400 font-bold">•</span>
            <span>
              Press <KeyBadge keyName="?" /> anywhere to see this shortcuts reference
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-primary-600 dark:text-primary-400 font-bold">•</span>
            <span>
              Use <KeyBadge keyName="⌘" /> + <KeyBadge keyName="k" /> to quickly access any feature via the command palette
            </span>
          </li>,
          <li className="flex items-start gap-3">
            <span className="text-primary-600 dark:text-primary-400 font-bold">•</span>
            <span>
              Navigation shortcuts starting with <KeyBadge keyName="g" /> work from any page
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-primary-600 dark:text-primary-400 font-bold">•</span>
            <span>
              Press <KeyBadge keyName="Esc" /> to close any modal or cancel the current action
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-primary-600 dark:text-primary-400 font-bold">•</span>
            <span>
              Use arrow keys to navigate through tables and lists for faster browsing
            </span>
          </li>
        </ul>
      </Card2>
    </div>
  );
}
