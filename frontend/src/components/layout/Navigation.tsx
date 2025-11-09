'use client';

import {
  BarChart3,
  Briefcase,
  FileText,
  Sparkles,
  TrendingUp,
  Menu,
  X,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import { ThemeToggle } from '@/components/ui/ThemeToggle';

const navigationItems = [
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/jobs', label: 'Jobs', icon: Briefcase },
  { href: '/applications', label: 'Applications', icon: FileText },
  { href: '/recommendations', label: 'Recommendations', icon: Sparkles },
  { href: '/analytics', label: 'Analytics', icon: TrendingUp },
  { href: '/advanced-features', label: 'AI Tools', icon: Sparkles },
];

 
export default function Navigation() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <nav className="bg-white dark:bg-neutral-900 shadow-sm border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-2 flex-shrink-0">
            <Briefcase className="h-8 w-8 text-primary-600 dark:text-primary-400" />
            <Link href="/dashboard" className="text-xl font-bold text-neutral-900 dark:text-neutral-100 hidden sm:block">
              Career Copilot
            </Link>
            <Link href="/dashboard" className="text-lg font-bold text-neutral-900 dark:text-neutral-100 sm:hidden">
              CC
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 border-b-2 border-primary-600 dark:border-primary-400'
                    : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                    }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
            
            {/* Theme Toggle */}
            <div className="ml-2 pl-2 border-l border-neutral-200 dark:border-neutral-700">
              <ThemeToggle />
            </div>
          </div>

          {/* Mobile menu button and theme toggle */}
          <div className="md:hidden flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-md text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 bg-white dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-800">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-3 w-full px-3 py-3 rounded-md text-base font-medium transition-colors ${isActive
                      ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                      : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                      }`}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}