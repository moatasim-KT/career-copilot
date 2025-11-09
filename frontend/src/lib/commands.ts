/**
 * Command Registry
 * 
 * Centralized registry of all commands available in the command palette.
 */

import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Sparkles,
  TrendingUp,
  Settings,
  HelpCircle,
  Plus,
  Search,
  Moon,
  Sun,
  LogOut,
  User,
  Bell,
  Download,
  Upload,
  type LucideIcon,
} from 'lucide-react';

export interface Command {
  id: string;
  label: string;
  category: 'navigation' | 'action' | 'setting' | 'search';
  icon: LucideIcon;
  keywords: string[];
  action: () => void | Promise<void>;
  shortcut?: string;
}

/**
 * Create command registry with router
 */
export function createCommandRegistry(router: any): Command[] {
  return [
    // Navigation Commands
    {
      id: 'nav-dashboard',
      label: 'Go to Dashboard',
      category: 'navigation',
      icon: LayoutDashboard,
      keywords: ['home', 'overview', 'dashboard', 'main'],
      action: () => router.push('/dashboard'),
      shortcut: 'g d',
    },
    {
      id: 'nav-jobs',
      label: 'Go to Jobs',
      category: 'navigation',
      icon: Briefcase,
      keywords: ['jobs', 'positions', 'openings', 'listings'],
      action: () => router.push('/jobs'),
      shortcut: 'g j',
    },
    {
      id: 'nav-applications',
      label: 'Go to Applications',
      category: 'navigation',
      icon: FileText,
      keywords: ['applications', 'applied', 'tracking'],
      action: () => router.push('/applications'),
      shortcut: 'g a',
    },
    {
      id: 'nav-recommendations',
      label: 'Go to Recommendations',
      category: 'navigation',
      icon: Sparkles,
      keywords: ['recommendations', 'suggestions', 'matches', 'ai'],
      action: () => router.push('/recommendations'),
      shortcut: 'g r',
    },
    {
      id: 'nav-analytics',
      label: 'Go to Analytics',
      category: 'navigation',
      icon: TrendingUp,
      keywords: ['analytics', 'stats', 'statistics', 'insights', 'reports'],
      action: () => router.push('/analytics'),
      shortcut: 'g n',
    },
    {
      id: 'nav-settings',
      label: 'Go to Settings',
      category: 'navigation',
      icon: Settings,
      keywords: ['settings', 'preferences', 'config', 'configuration'],
      action: () => router.push('/settings'),
      shortcut: 'g s',
    },
    {
      id: 'nav-help',
      label: 'Go to Help Center',
      category: 'navigation',
      icon: HelpCircle,
      keywords: ['help', 'support', 'docs', 'documentation', 'faq'],
      action: () => router.push('/help'),
      shortcut: 'g h',
    },

    // Action Commands
    {
      id: 'action-create-job',
      label: 'Create New Job',
      category: 'action',
      icon: Plus,
      keywords: ['create', 'new', 'add', 'job', 'position'],
      action: () => router.push('/jobs/new'),
      shortcut: 'c j',
    },
    {
      id: 'action-create-application',
      label: 'Create New Application',
      category: 'action',
      icon: Plus,
      keywords: ['create', 'new', 'add', 'application', 'apply'],
      action: () => router.push('/applications/new'),
      shortcut: 'c a',
    },
    {
      id: 'action-search-jobs',
      label: 'Search Jobs',
      category: 'action',
      icon: Search,
      keywords: ['search', 'find', 'jobs', 'filter'],
      action: () => {
        router.push('/jobs');
        // Focus search input after navigation
        setTimeout(() => {
          const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
          if (searchInput) searchInput.focus();
        }, 100);
      },
      shortcut: '/',
    },
    {
      id: 'action-export-data',
      label: 'Export Data',
      category: 'action',
      icon: Download,
      keywords: ['export', 'download', 'backup', 'csv', 'pdf'],
      action: () => router.push('/settings/data'),
    },
    {
      id: 'action-import-data',
      label: 'Import Data',
      category: 'action',
      icon: Upload,
      keywords: ['import', 'upload', 'restore', 'csv'],
      action: () => router.push('/settings/data'),
    },

    // Setting Commands
    {
      id: 'setting-profile',
      label: 'Edit Profile',
      category: 'setting',
      icon: User,
      keywords: ['profile', 'account', 'user', 'edit', 'personal'],
      action: () => router.push('/settings/profile'),
    },
    {
      id: 'setting-notifications',
      label: 'Notification Settings',
      category: 'setting',
      icon: Bell,
      keywords: ['notifications', 'alerts', 'email', 'push'],
      action: () => router.push('/settings/notifications'),
    },
    {
      id: 'setting-appearance',
      label: 'Appearance Settings',
      category: 'setting',
      icon: Sun,
      keywords: ['appearance', 'theme', 'dark', 'light', 'ui'],
      action: () => router.push('/settings/appearance'),
    },
  ];
}

/**
 * Get commands filtered by search query
 */
export function searchCommands(commands: Command[], query: string): Command[] {
  if (!query.trim()) {
    return commands;
  }

  const lowerQuery = query.toLowerCase();
  
  return commands.filter((command) => {
    // Search in label
    if (command.label.toLowerCase().includes(lowerQuery)) {
      return true;
    }
    
    // Search in keywords
    return command.keywords.some((keyword) =>
      keyword.toLowerCase().includes(lowerQuery),
    );
  });
}

/**
 * Group commands by category
 */
export function groupCommandsByCategory(commands: Command[]): Record<string, Command[]> {
  return commands.reduce(
    (acc, command) => {
      if (!acc[command.category]) {
        acc[command.category] = [];
      }
      acc[command.category].push(command);
      return acc;
    },
    {} as Record<string, Command[]>,
  );
}

/**
 * Get category display name
 */
export function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    navigation: 'Navigation',
    action: 'Actions',
    setting: 'Settings',
    search: 'Search Results',
  };
  
  return labels[category] || category;
}

/**
 * Recent commands storage
 */
const RECENT_COMMANDS_KEY = 'recent-commands';
const MAX_RECENT_COMMANDS = 10;

export function getRecentCommands(): string[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const stored = localStorage.getItem(RECENT_COMMANDS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to read recent commands:', error);
    return [];
  }
}

export function addRecentCommand(commandId: string): void {
  if (typeof window === 'undefined') return;
  
  try {
    const recent = getRecentCommands();
    
    // Remove if already exists
    const filtered = recent.filter((id) => id !== commandId);
    
    // Add to front
    const updated = [commandId, ...filtered].slice(0, MAX_RECENT_COMMANDS);
    
    localStorage.setItem(RECENT_COMMANDS_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Failed to save recent command:', error);
  }
}

export function clearRecentCommands(): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(RECENT_COMMANDS_KEY);
  } catch (error) {
    console.error('Failed to clear recent commands:', error);
  }
}
