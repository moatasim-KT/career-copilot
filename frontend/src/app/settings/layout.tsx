/**
 * Settings Layout
 * 
 * Provides a sidebar navigation for settings pages.
 * Responsive: drawer on mobile, sidebar on desktop.
 */

'use client';

import {
  User,
  Palette,
  Bell,
  Shield,
  Key,
  Database,
  Keyboard,
  Menu,
  X,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import { cn } from '@/lib/utils';
import Card2 from '@/components/ui/Card2';

interface SettingsNavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const settingsNavItems: SettingsNavItem[] = [
  {
    href: '/settings/profile',
    label: 'Profile',
    icon: User,
    description: 'Manage your personal information',
  },
  {
    href: '/settings/appearance',
    label: 'Appearance',
    icon: Palette,
    description: 'Customize theme and display',
  },
  {
    href: '/settings/notifications',
    label: 'Notifications',
    icon: Bell,
    description: 'Configure notification preferences',
  },
  {
    href: '/settings/privacy',
    label: 'Privacy',
    icon: Shield,
    description: 'Control your privacy settings',
  },
  {
    href: '/settings/account',
    label: 'Account',
    icon: Key,
    description: 'Security and authentication',
  },
  {
    href: '/settings/data',
    label: 'Data',
    icon: Database,
    description: 'Export and manage your data',
  },
  {
    href: '/settings/shortcuts',
    label: 'Keyboard Shortcuts',
    icon: Keyboard,
    description: 'View and customize shortcuts',
  },
];

interface SettingsNavLinkProps {
  item: SettingsNavItem;
  isActive: boolean;
  onClick?: () => void;
  className?: string;
}

function SettingsNavLink({ item, isActive, onClick, className }: SettingsNavLinkProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      onClick={onClick}
      className={cn(
        'flex items-start gap-3 px-4 py-3 rounded-lg transition-colors relative group',
        isActive
          ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
          : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800',
        className
      )}
    >
      <Icon className={cn(
        'w-5 h-5 mt-0.5 flex-shrink-0',
        isActive
          ? 'text-primary-600 dark:text-primary-400'
          : 'text-neutral-500 dark:text-neutral-400 group-hover:text-neutral-700 dark:group-hover:text-neutral-300'
      )} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium">{item.label}</div>
        <div className="text-xs text-neutral-600 dark:text-neutral-400 mt-0.5">
          {item.description}
        </div>
      </div>
      {/* Accent border for active item */}
      {isActive && (
        <span 
          className="absolute left-0 top-0 bottom-0 w-1 bg-primary-600 dark:bg-primary-400 rounded-r-full"
          aria-hidden="true"
        />
      )}
    </Link>
  );
}

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                Settings
              </h1>
              <p className="text-neutral-600 dark:text-neutral-400 mt-1">
                Manage your account settings and preferences
              </p>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 rounded-md text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              aria-label="Toggle settings menu"
              style={{ minWidth: 44, minHeight: 44 }}
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Desktop Sidebar */}
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <Card2 className="p-2">
              <nav className="space-y-1">
                {settingsNavItems.map((item) => (
                  <SettingsNavLink
                    key={item.href}
                    item={item}
                    isActive={pathname === item.href}
                  />
                ))}
              </nav>
            </Card2>
          </aside>

          {/* Mobile Drawer */}
          <AnimatePresence>
            {isMobileMenuOpen && (
              <>
                {/* Backdrop */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="fixed inset-0 z-40 bg-black/50 lg:hidden"
                  onClick={() => setIsMobileMenuOpen(false)}
                  aria-label="Close settings menu overlay"
                />

                {/* Drawer */}
                <motion.div
                  initial={{ x: '-100%' }}
                  animate={{ x: 0 }}
                  exit={{ x: '-100%' }}
                  transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                  className="fixed top-0 left-0 z-50 h-full w-4/5 max-w-sm bg-white dark:bg-neutral-900 shadow-xl lg:hidden overflow-y-auto"
                >
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
                        Settings
                      </h2>
                      <button
                        onClick={() => setIsMobileMenuOpen(false)}
                        className="p-2 rounded-md text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                        aria-label="Close settings menu"
                        style={{ minWidth: 44, minHeight: 44 }}
                      >
                        <X className="h-6 w-6" />
                      </button>
                    </div>

                    <nav className="space-y-1">
                      {settingsNavItems.map((item) => (
                        <SettingsNavLink
                          key={item.href}
                          item={item}
                          isActive={pathname === item.href}
                          onClick={() => setIsMobileMenuOpen(false)}
                        />
                      ))}
                    </nav>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            <Card2 className="p-6 sm:p-8">
              {children}
            </Card2>
          </main>
        </div>
      </div>
    </div>
  );
}
