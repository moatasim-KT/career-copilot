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
import { useState, useEffect } from 'react';

import { ThemeToggle } from '@/components/ui/ThemeToggle';
import NotificationCenter from '@/components/ui/NotificationCenter';
import { cn } from '@/lib/utils';

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
  const [isScrolled, setIsScrolled] = useState(false);
  const pathname = usePathname();

  // Detect scroll to apply glass morphism effect
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`shadow-sm border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-50 transition-all duration-200 ${
      isScrolled 
        ? 'glass' 
        : 'bg-white dark:bg-neutral-900'
    }`}>
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
                  className={cn(
                    'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium accent-transition relative',
                    isActive
                      ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                      : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                  {/* Accent border for active item */}
                  {isActive && (
                    <span 
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600 dark:bg-primary-400 rounded-full"
                      aria-hidden="true"
                    />
                  )}
                </Link>
              );
            })}

            {/* Notification Center and Theme Toggle */}
            <div className="ml-2 pl-2 border-l border-neutral-200 dark:border-neutral-700 flex items-center gap-2">
              <NotificationCenter />
              <ThemeToggle />
            </div>
          </div>

          {/* Mobile menu button, notification center, and theme toggle */}
          <div className="md:hidden flex items-center gap-2">
            <NotificationCenter />
            <ThemeToggle />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-md text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              aria-label="Toggle menu"
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

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <>
            {/* Backdrop overlay with glass morphism */}
            <div
              className="fixed inset-0 z-40 glass transition-opacity md:hidden"
              onClick={() => setIsMobileMenuOpen(false)}
              aria-label="Close menu overlay"
            />
            {/* Slide-in menu */}
            <div
              className="fixed top-0 right-0 z-50 h-full w-4/5 max-w-xs bg-white dark:bg-neutral-900 shadow-lg border-l border-neutral-200 dark:border-neutral-800 transform transition-transform duration-300 md:hidden"
              style={{ minWidth: 260 }}
            >
              <div className="flex justify-end p-4">
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 rounded-md text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                  aria-label="Close menu"
                  style={{ minWidth: 44, minHeight: 44 }}
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="px-2 pt-2 pb-3 space-y-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={cn(
                        'flex items-center space-x-3 w-full px-3 py-3 rounded-md text-base font-medium accent-transition relative',
                        isActive
                          ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                          : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                      )}
                      style={{ minWidth: 44 }}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      <span>{item.label}</span>
                      {/* Accent border for active item on mobile */}
                      {isActive && (
                        <span 
                          className="absolute left-0 top-0 bottom-0 w-1 bg-primary-600 dark:bg-primary-400 rounded-r-full"
                          aria-hidden="true"
                        />
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </nav>
  );
}