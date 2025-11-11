/**
 * Contextual Help Components
 * 
 * Pre-configured help components for common features throughout the application.
 * These can be imported and used wherever contextual help is needed.
 * 
 * Usage:
 * ```tsx
 * import { CommandPaletteHelp, AdvancedSearchHelp } from '@/components/help/ContextualHelp';
 * 
 * <CommandPaletteHelp />
 * ```
 */

'use client';

import { HelpIcon, InlineHelp } from '@/components/ui/HelpIcon';

/**
 * Command Palette Help
 */
export function CommandPaletteHelp() {
  return (
    <HelpIcon
      title="Command Palette"
      content={
        <div className="space-y-2">
          <p>
            Quickly access any feature, search for jobs and applications, or execute actions
            without clicking through menus.
          </p>
          <div className="mt-3 p-3 bg-neutral-100 dark:bg-neutral-800 rounded-md">
            <p className="text-xs font-semibold mb-2">Keyboard Shortcuts:</p>
            <ul className="text-xs space-y-1">
              <li>
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600">
                  ⌘K
                </kbd>{' '}
                or{' '}
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600">
                  Ctrl+K
                </kbd>{' '}
                - Open command palette
              </li>
              <li>
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600">
                  ↑↓
                </kbd>{' '}
                - Navigate results
              </li>
              <li>
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600">
                  Enter
                </kbd>{' '}
                - Execute command
              </li>
              <li>
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600">
                  Esc
                </kbd>{' '}
                - Close palette
              </li>
            </ul>
          </div>
        </div>
      }
      docsLink="/help#command-palette"
    />
  );
}

/**
 * Advanced Search Help
 */
export function AdvancedSearchHelp() {
  return (
    <HelpIcon
      title="Advanced Search"
      content={
        <div className="space-y-2">
          <p>
            Build complex queries using AND/OR logic to find exactly what you're looking for.
          </p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Combine multiple filters</li>
            <li>• Create nested groups</li>
            <li>• Save searches for later</li>
            <li>• Export search results</li>
          </ul>
        </div>
      }
      docsLink="/help#advanced-search"
    />
  );
}

/**
 * Bulk Operations Help
 */
export function BulkOperationsHelp() {
  return (
    <HelpIcon
      title="Bulk Operations"
      content={
        <div className="space-y-2">
          <p>Perform actions on multiple items at once to save time.</p>
          <ol className="text-sm space-y-1 mt-2 list-decimal list-inside">
            <li>Select items using checkboxes</li>
            <li>Choose an action from the toolbar</li>
            <li>Confirm the operation</li>
          </ol>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
            Tip: Use Shift+Click to select a range of items
          </p>
        </div>
      }
      docsLink="/help#bulk-operations"
    />
  );
}

/**
 * Kanban Board Help
 */
export function KanbanBoardHelp() {
  return (
    <HelpIcon
      title="Kanban Board"
      content={
        <div className="space-y-2">
          <p>Visualize and manage your applications by dragging cards between status columns.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Drag cards to change status</li>
            <li>• Click cards to view details</li>
            <li>• Use keyboard navigation (Space to pick up, arrows to move)</li>
          </ul>
        </div>
      }
      docsLink="/help#kanban-board"
    />
  );
}

/**
 * Dashboard Widgets Help
 */
export function DashboardWidgetsHelp() {
  return (
    <HelpIcon
      title="Dashboard Widgets"
      content={
        <div className="space-y-2">
          <p>Customize your dashboard by dragging widgets to reorder them.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Drag widgets to reorder</li>
            <li>• Your layout is saved automatically</li>
            <li>• Reset to default in Settings</li>
          </ul>
        </div>
      }
      docsLink="/help#dashboard"
    />
  );
}

/**
 * Notifications Help
 */
export function NotificationsHelp() {
  return (
    <HelpIcon
      title="Notifications"
      content={
        <div className="space-y-2">
          <p>Stay updated with real-time notifications for job matches and application updates.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Enable browser push notifications</li>
            <li>• Customize notification preferences</li>
            <li>• Set Do Not Disturb schedule</li>
          </ul>
        </div>
      }
      docsLink="/help#notifications"
    />
  );
}

/**
 * Data Export Help
 */
export function DataExportHelp() {
  return (
    <HelpIcon
      title="Export Data"
      content={
        <div className="space-y-2">
          <p>Export your data in various formats for backup or analysis.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• CSV - For spreadsheets</li>
            <li>• PDF - For printing</li>
            <li>• JSON - For full backup</li>
          </ul>
        </div>
      }
      docsLink="/help#data-export"
    />
  );
}

/**
 * Saved Searches Help
 */
export function SavedSearchesHelp() {
  return (
    <HelpIcon
      title="Saved Searches"
      content={
        <div className="space-y-2">
          <p>Save your search criteria to quickly run the same search later.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Create complex searches once</li>
            <li>• Run saved searches with one click</li>
            <li>• Edit or delete saved searches</li>
          </ul>
        </div>
      }
      docsLink="/help#saved-searches"
    />
  );
}

/**
 * Analytics Help
 */
export function AnalyticsHelp() {
  return (
    <HelpIcon
      title="Analytics"
      content={
        <div className="space-y-2">
          <p>Visualize your job search progress and gain insights into your success rate.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Track application trends</li>
            <li>• Identify top skills in demand</li>
            <li>• Compare your success rate</li>
            <li>• Export charts as images</li>
          </ul>
        </div>
      }
      docsLink="/help#analytics"
    />
  );
}

/**
 * Resume Upload Help
 */
export function ResumeUploadHelp() {
  return (
    <HelpIcon
      title="Resume Upload"
      content={
        <div className="space-y-2">
          <p>Upload your resume to automatically extract skills and experience.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Supported formats: PDF, DOCX</li>
            <li>• Maximum file size: 10MB</li>
            <li>• AI extracts skills automatically</li>
          </ul>
        </div>
      }
      docsLink="/help#resume-upload"
    />
  );
}

/**
 * Skills Management Help
 */
export function SkillsManagementHelp() {
  return (
    <HelpIcon
      title="Skills Management"
      content={
        <div className="space-y-2">
          <p>Add and manage your skills to get better job recommendations.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Search from our skill database</li>
            <li>• Add custom skills</li>
            <li>• Set proficiency levels</li>
            <li>• Skills are used for job matching</li>
          </ul>
        </div>
      }
      docsLink="/help#skills"
    />
  );
}

/**
 * Job Preferences Help
 */
export function JobPreferencesHelp() {
  return (
    <HelpIcon
      title="Job Preferences"
      content={
        <div className="space-y-2">
          <p>Set your job preferences to receive personalized recommendations.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Preferred job titles</li>
            <li>• Desired locations</li>
            <li>• Salary expectations</li>
            <li>• Work arrangement (Remote, Hybrid, On-site)</li>
          </ul>
        </div>
      }
      docsLink="/help#job-preferences"
    />
  );
}

/**
 * Dark Mode Help
 */
export function DarkModeHelp() {
  return (
    <HelpIcon
      title="Dark Mode"
      content={
        <div className="space-y-2">
          <p>Switch between light and dark themes or follow your system preference.</p>
          <ul className="text-sm space-y-1 mt-2">
            <li>• Light - Always use light theme</li>
            <li>• Dark - Always use dark theme</li>
            <li>• System - Follow device preference</li>
          </ul>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
            Keyboard shortcut: ⌘D or Ctrl+D
          </p>
        </div>
      }
      docsLink="/help#dark-mode"
    />
  );
}

/**
 * Keyboard Shortcuts Help
 */
export function KeyboardShortcutsHelp() {
  return (
    <HelpIcon
      title="Keyboard Shortcuts"
      content={
        <div className="space-y-2">
          <p>Use keyboard shortcuts to navigate faster.</p>
          <div className="mt-2 space-y-1 text-xs">
            <div className="flex justify-between">
              <span>Command Palette</span>
              <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-600">
                ⌘K
              </kbd>
            </div>
            <div className="flex justify-between">
              <span>Toggle Dark Mode</span>
              <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-600">
                ⌘D
              </kbd>
            </div>
            <div className="flex justify-between">
              <span>Search</span>
              <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded border border-neutral-300 dark:border-neutral-600">
                /
              </kbd>
            </div>
          </div>
        </div>
      }
      docsLink="/help#keyboard-shortcuts"
    />
  );
}

/**
 * Form Field Help Components
 * These are inline help texts for form fields
 */

export function EmailFieldHelp() {
  return (
    <InlineHelp>
      We'll use this email for notifications and account recovery. We never share your email.
    </InlineHelp>
  );
}

export function PasswordFieldHelp() {
  return (
    <InlineHelp>
      Use at least 8 characters with a mix of letters, numbers, and symbols.
    </InlineHelp>
  );
}

export function SalaryRangeHelp() {
  return (
    <InlineHelp>
      Set your expected salary range. This helps us show you relevant opportunities.
    </InlineHelp>
  );
}

export function LocationFieldHelp() {
  return (
    <InlineHelp>
      Enter cities, states, or "Remote" for remote positions. You can add multiple locations.
    </InlineHelp>
  );
}

export function JobTitleFieldHelp() {
  return (
    <InlineHelp>
      Add job titles you're interested in. We'll use these to find matching opportunities.
    </InlineHelp>
  );
}

export function ExperienceFieldHelp() {
  return (
    <InlineHelp>
      Select your years of professional experience. This helps match you with appropriate roles.
    </InlineHelp>
  );
}

export function BioFieldHelp() {
  return (
    <InlineHelp>
      Write a brief summary about yourself and your career goals (optional).
    </InlineHelp>
  );
}

export function NotificationPreferencesHelp() {
  return (
    <InlineHelp>
      Choose how and when you want to receive notifications. You can change these anytime.
    </InlineHelp>
  );
}

/**
 * Input Placeholder Examples
 * These are example placeholders that provide contextual help
 */

export const helpfulPlaceholders = {
  email: 'you@example.com',
  password: 'At least 8 characters',
  jobTitle: 'e.g., Software Engineer, Product Manager',
  location: 'e.g., San Francisco, CA or Remote',
  company: 'e.g., Google, Microsoft',
  salary: 'e.g., $80,000 - $120,000',
  skills: 'Search for skills or add custom ones',
  bio: 'Tell us about yourself and your career goals...',
  searchJobs: 'Search by title, company, or keywords...',
  searchApplications: 'Search by company, position, or status...',
  notes: 'Add notes about this application...',
  website: 'https://example.com',
  phone: '(555) 123-4567',
  linkedin: 'https://linkedin.com/in/yourprofile',
  github: 'https://github.com/yourusername',
};

/**
 * Tooltip Messages
 * Short tooltip messages for buttons and icons
 */

export const tooltipMessages = {
  save: 'Save changes',
  cancel: 'Cancel and discard changes',
  delete: 'Delete permanently',
  edit: 'Edit this item',
  archive: 'Move to archive',
  restore: 'Restore from archive',
  export: 'Export data',
  import: 'Import data',
  refresh: 'Refresh data',
  filter: 'Filter results',
  sort: 'Sort results',
  search: 'Search',
  settings: 'Open settings',
  help: 'Get help',
  notifications: 'View notifications',
  profile: 'View profile',
  logout: 'Log out',
  darkMode: 'Toggle dark mode',
  fullscreen: 'Toggle fullscreen',
  copy: 'Copy to clipboard',
  share: 'Share',
  download: 'Download',
  upload: 'Upload file',
  close: 'Close',
  minimize: 'Minimize',
  maximize: 'Maximize',
  back: 'Go back',
  forward: 'Go forward',
  home: 'Go to home',
  menu: 'Open menu',
  more: 'More options',
};

/**
 * Error Messages with Help
 * User-friendly error messages with suggestions
 */

export const errorMessagesWithHelp = {
  networkError: {
    title: 'Connection Lost',
    message: 'Unable to connect to the server. Please check your internet connection.',
    help: 'Try refreshing the page or check your network settings.',
  },
  authError: {
    title: 'Session Expired',
    message: 'Your session has expired. Please log in again.',
    help: 'For security, sessions expire after 24 hours of inactivity.',
  },
  notFoundError: {
    title: 'Not Found',
    message: 'The item you're looking for doesn't exist or has been deleted.',
    help: 'Try searching for it or check if you have the correct link.',
  },
  serverError: {
    title: 'Server Error',
    message: 'Something went wrong on our end. Please try again later.',
    help: 'If the problem persists, contact support with the error details.',
  },
  validationError: {
    title: 'Invalid Input',
    message: 'Please check your input and try again.',
    help: 'Make sure all required fields are filled correctly.',
  },
  uploadError: {
    title: 'Upload Failed',
    message: 'Unable to upload the file. Please try again.',
    help: 'Make sure the file is under 10MB and in a supported format (PDF, DOCX).',
  },
};
