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

import { LazyNotificationCenter } from '@/components/lazy';
import { NotificationBadge } from '@/components/ui/Badge';
import { ConnectionStatusCompact } from '@/components/ui/ConnectionStatus';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { useRealtimeJobs } from '@/hooks/useRealtimeJobs';
import { useRoutePrefetch } from '@/hooks/useRoutePrefetch';
import { cn } from '@/lib/utils';

const navigationItems = [
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/jobs', label: 'Jobs', icon: Briefcase },
  { href: '/applications', label: 'Applications', icon: FileText },
  { href: '/recommendations', label: 'Recommendations', icon: Sparkles },
  { href: '/analytics', label: 'Analytics', icon: TrendingUp },
  { href: '/advanced-features', label: 'AI Tools', icon: Sparkles },
];

/**
 * Navigation link with prefetching support
 */
interface NavigationLinkProps {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  isActive: boolean;
  onClick?: () => void;
  className?: string;
}

function NavigationLink({ href, label, icon: Icon, isActive, onClick, className }: NavigationLinkProps) {
  const prefetchHandlers = useRoutePrefetch(href);

  return (
    <Link
      href={href}
      onClick={onClick}
      onMouseEnter={prefetchHandlers.onMouseEnter}
      onMouseLeave={prefetchHandlers.onMouseLeave}
      onTouchStart={prefetchHandlers.onTouchStart}
      className={cn(
        'relative flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
        isActive
          ? 'bg-primary-600 text-white shadow-sm'
          : 'text-neutral-700 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800',
        className,
      )}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </Link>
  );
}

/**
 * Mobile navigation link with prefetching support
 */
function MobileNavigationLink({ href, label, icon: Icon, isActive, onClick }: NavigationLinkProps) {
  const prefetchHandlers = useRoutePrefetch(href);

  return (
    <Link
      href={href}
      onClick={onClick}
      onMouseEnter={prefetchHandlers.onMouseEnter}
      onMouseLeave={prefetchHandlers.onMouseLeave}
      onTouchStart={prefetchHandlers.onTouchStart}
      className={cn(
        'relative flex items-center gap-3 w-full px-4 py-3 rounded-lg text-base font-medium transition-all duration-200',
        isActive
          ? 'bg-primary-600 text-white shadow-sm'
          : 'text-neutral-700 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800',
      )}
      style={{ minWidth: 44 }}
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <span>{label}</span>
    </Link>
  );
}

export default function Navigation() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const pathname = usePathname();
  const { newJobsCount, clearNewJobs } = useRealtimeJobs();

  // Detect scroll to apply glass morphism effect
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  return (
    <nav className={cn(
      'sticky top-0 z-50 border-b transition-all duration-200',
      isScrolled
        ? 'glass border-neutral-200/80 dark:border-neutral-800/80 shadow-sm'
        : 'bg-white/95 dark:bg-neutral-950/95 border-neutral-200 dark:border-neutral-800 backdrop-blur-sm'
    )}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
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
          <div className="hidden md:flex items-center gap-2">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;
              const showBadge = item.href === '/jobs' && newJobsCount > 0;

              return (
                <div key={item.href} className="relative">
                  <NavigationLink
                    href={item.href}
                    label={item.label}
                    icon={item.icon}
                    isActive={isActive}
                    onClick={() => {
                      if (item.href === '/jobs') {
                        clearNewJobs();
                      }
                    }}
                  />
                  {showBadge && (
                    <NotificationBadge count={newJobsCount} className="absolute -top-1 -right-1" />
                  )}
                </div>
              );
            })}

            {/* Connection Status, Notification Center and Theme Toggle */}
            <div className="ml-4 pl-4 border-l border-neutral-300 dark:border-neutral-700 flex items-center gap-2">
              <ConnectionStatusCompact />
              <LazyNotificationCenter />
              <ThemeToggle />
            </div>
          </div>

          {/* Mobile menu button, connection status, notification center, and theme toggle */}
          <div className="md:hidden flex items-center gap-2">
            <ConnectionStatusCompact />
            <LazyNotificationCenter />
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
                  const isActive = pathname === item.href;
                  const showBadge = item.href === '/jobs' && newJobsCount > 0;

                  return (
                    <div key={item.href} className="relative">
                      <MobileNavigationLink
                        href={item.href}
                        label={item.label}
                        icon={item.icon}
                        isActive={isActive}
                        onClick={() => {
                          setIsMobileMenuOpen(false);
                          if (item.href === '/jobs') {
                            clearNewJobs();
                          }
                        }}
                      />
                      {showBadge && (
                        <NotificationBadge count={newJobsCount} className="absolute top-2 right-4" />
                      )}
                    </div>
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