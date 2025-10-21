import { useState, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { 
  Bars3Icon, 
  BellIcon, 
  UserCircleIcon,
  SunIcon,
  MoonIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { useTheme } from '@/hooks/useTheme'
import { useResponsive } from '@/hooks/useResponsive'
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation'
import { useAccessibility } from '@/contexts/AccessibilityContext'
import { Button } from './ui/Button'
import { ResponsiveContainer, ResponsiveShow, ResponsiveStack } from './ResponsiveContainer'

interface NavbarProps {
  onMenuClick?: () => void
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { theme, toggleTheme } = useTheme()
  const { announceToScreenReader } = useAccessibility()
  const { isMobile, isTablet } = useResponsive()
  const router = useRouter()
  const profileMenuRef = useRef<HTMLDivElement>(null)

  useKeyboardNavigation(profileMenuRef, {
    enableEscape: isProfileMenuOpen,
    onEscape: () => {
      setIsProfileMenuOpen(false)
      announceToScreenReader('Profile menu closed')
    }
  })

  const navigationLinks = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/jobs', label: 'Jobs' },
    { href: '/goals', label: 'Goals' },
    { href: '/analytics', label: 'Analytics' },
  ]

  const handleMobileMenuToggle = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
    if (onMenuClick) onMenuClick()
    announceToScreenReader(isMobileMenuOpen ? 'Mobile menu closed' : 'Mobile menu opened')
  }

  return (
    <nav 
      id="navigation"
      className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 transition-colors duration-200 sticky top-0 z-50"
      role="navigation"
      aria-label="Main navigation"
    >
      <ResponsiveContainer maxWidth="full" padding="responsive">
        <div className="flex h-16 justify-between items-center">
          {/* Logo and brand */}
          <div className="flex items-center flex-shrink-0">
            <Link href="/" className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">CC</span>
              </div>
              <ResponsiveShow above="sm">
                <span className="text-xl font-bold text-gray-900 dark:text-white">
                  Career Co-Pilot
                </span>
              </ResponsiveShow>
              <ResponsiveShow only="mobile">
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  Career Co-Pilot
                </span>
              </ResponsiveShow>
            </Link>
          </div>

          {/* Desktop Navigation links */}
          <ResponsiveShow above="md">
            <div className="flex items-center space-x-8">
              {navigationLinks.map((link) => (
                <Link 
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    router.pathname === link.href
                      ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                      : 'text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </ResponsiveShow>

          {/* Right side actions */}
          <ResponsiveStack direction="horizontal" spacing="sm" className="flex-shrink-0">
            {/* Theme toggle */}
            <Button
              variant="ghost"
              size={isMobile ? "sm" : "md"}
              onClick={() => {
                toggleTheme()
                announceToScreenReader(`Switched to ${theme === 'dark' ? 'light' : 'dark'} theme`)
              }}
              className={`${isMobile ? 'p-2' : 'p-2'} touch-friendly`}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            >
              {theme === 'dark' ? (
                <SunIcon className={`${isMobile ? 'h-5 w-5' : 'h-5 w-5'}`} aria-hidden="true" />
              ) : (
                <MoonIcon className={`${isMobile ? 'h-5 w-5' : 'h-5 w-5'}`} aria-hidden="true" />
              )}
            </Button>

            {/* Notifications - Hidden on mobile */}
            <ResponsiveShow above="sm">
              <Button
                variant="ghost"
                size={isMobile ? "sm" : "md"}
                className="p-2 touch-friendly"
                aria-label="Notifications"
              >
                <BellIcon className="h-5 w-5" />
              </Button>
            </ResponsiveShow>

            {/* Profile menu */}
            <div className="relative" ref={profileMenuRef}>
              <Button
                variant="ghost"
                size={isMobile ? "sm" : "md"}
                onClick={() => {
                  setIsProfileMenuOpen(!isProfileMenuOpen)
                  announceToScreenReader(isProfileMenuOpen ? 'Profile menu closed' : 'Profile menu opened')
                }}
                className="p-2 touch-friendly"
                aria-label="User menu"
                aria-expanded={isProfileMenuOpen}
                aria-haspopup="menu"
              >
                <UserCircleIcon className="h-6 w-6" aria-hidden="true" />
              </Button>

              {isProfileMenuOpen && (
                <div 
                  className={`
                    absolute right-0 mt-2 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50 border border-gray-200 dark:border-gray-700
                    ${isMobile ? 'w-56' : 'w-48'}
                  `}
                  role="menu"
                  aria-label="User menu"
                >
                  <Link
                    href="/profile"
                    className={`block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-100 dark:focus:bg-gray-700 ${isMobile ? 'touch-friendly-padding' : ''}`}
                    onClick={() => setIsProfileMenuOpen(false)}
                    role="menuitem"
                  >
                    Profile
                  </Link>
                  <Link
                    href="/settings"
                    className={`block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-100 dark:focus:bg-gray-700 ${isMobile ? 'touch-friendly-padding' : ''}`}
                    onClick={() => setIsProfileMenuOpen(false)}
                    role="menuitem"
                  >
                    Settings
                  </Link>
                  
                  {/* Mobile-only menu items */}
                  <ResponsiveShow only="mobile">
                    <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                    <Link
                      href="/notifications"
                      className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-100 dark:focus:bg-gray-700 touch-friendly-padding"
                      onClick={() => setIsProfileMenuOpen(false)}
                      role="menuitem"
                    >
                      Notifications
                    </Link>
                  </ResponsiveShow>
                  
                  <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                  <button
                    className={`block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-100 dark:focus:bg-gray-700 ${isMobile ? 'touch-friendly-padding' : ''}`}
                    onClick={() => {
                      setIsProfileMenuOpen(false)
                      announceToScreenReader('Signed out')
                      // Add logout logic here
                    }}
                    role="menuitem"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>

            {/* Mobile menu button */}
            <ResponsiveShow below="md">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMobileMenuToggle}
                className="p-2 touch-friendly"
                aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
                aria-expanded={isMobileMenuOpen}
              >
                {isMobileMenuOpen ? (
                  <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                ) : (
                  <Bars3Icon className="h-6 w-6" aria-hidden="true" />
                )}
              </Button>
            </ResponsiveShow>
          </ResponsiveStack>
        </div>

        {/* Mobile Navigation Menu */}
        <ResponsiveShow below="md">
          {isMobileMenuOpen && (
            <div className="border-t border-gray-200 dark:border-gray-700 py-4">
              <div className="space-y-2">
                {navigationLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`block px-3 py-3 rounded-md text-base font-medium transition-colors touch-friendly-padding ${
                      router.pathname === link.href
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                        : 'text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </ResponsiveShow>
      </ResponsiveContainer>
    </nav>
  )
}