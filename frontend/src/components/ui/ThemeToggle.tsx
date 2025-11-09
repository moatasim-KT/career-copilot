/**
 * Theme Toggle Component
 * 
 * Button to toggle between light and dark themes with smooth icon transitions.
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { useDarkMode } from '@/hooks/useDarkMode';
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  showTooltip?: boolean;
}

export function ThemeToggle({ 
  className = '', 
  showLabel = false,
  showTooltip = true 
}: ThemeToggleProps) {
  const { isDark, toggle } = useDarkMode();
  
  // Keyboard shortcut: Cmd/Ctrl + D
  useKeyboardShortcut('d', toggle, { meta: true, ctrl: true });
  
  const tooltipText = `Toggle theme (${navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}+D)`;
  
  return (
    <button
      onClick={toggle}
      className={`
        relative inline-flex items-center justify-center
        rounded-lg p-2
        text-neutral-700 dark:text-neutral-300
        hover:bg-neutral-100 dark:hover:bg-neutral-800
        focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
        dark:focus:ring-offset-neutral-900
        transition-colors duration-200
        ${className}
      `}
      aria-label="Toggle theme"
      title={showTooltip ? tooltipText : undefined}
      type="button"
    >
      <div className="relative w-5 h-5">
        <AnimatePresence mode="wait" initial={false}>
          {isDark ? (
            <motion.div
              key="moon"
              initial={{ scale: 0, rotate: -180, opacity: 0 }}
              animate={{ scale: 1, rotate: 0, opacity: 1 }}
              exit={{ scale: 0, rotate: 180, opacity: 0 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <Moon className="w-5 h-5" />
            </motion.div>
          ) : (
            <motion.div
              key="sun"
              initial={{ scale: 0, rotate: 180, opacity: 0 }}
              animate={{ scale: 1, rotate: 0, opacity: 1 }}
              exit={{ scale: 0, rotate: -180, opacity: 0 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <Sun className="w-5 h-5" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {showLabel && (
        <span className="ml-2 text-sm font-medium">
          {isDark ? 'Dark' : 'Light'}
        </span>
      )}
    </button>
  );
}

/**
 * Theme Toggle with Dropdown (for settings page)
 */
interface ThemeToggleDropdownProps {
  className?: string;
}

export function ThemeToggleDropdown({ className = '' }: ThemeToggleDropdownProps) {
  const { theme, setLight, setDark, setSystem } = useDarkMode();
  
  const options = [
    { value: 'light' as const, label: 'Light', icon: Sun },
    { value: 'dark' as const, label: 'Dark', icon: Moon },
    { value: 'system' as const, label: 'System', icon: Sun }
  ];
  
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
        Theme
      </label>
      <div className="flex gap-2">
        {options.map((option) => {
          const Icon = option.icon;
          const isActive = theme === option.value;
          
          return (
            <button
              key={option.value}
              onClick={() => {
                if (option.value === 'light') setLight();
                else if (option.value === 'dark') setDark();
                else setSystem();
              }}
              className={`
                flex-1 flex items-center justify-center gap-2 px-4 py-3
                rounded-lg border-2 transition-all duration-200
                ${isActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                  : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600'
                }
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                dark:focus:ring-offset-neutral-900
              `}
              type="button"
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{option.label}</span>
            </button>
          );
        })}
      </div>
      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        Choose your preferred theme or sync with your system settings
      </p>
    </div>
  );
}
