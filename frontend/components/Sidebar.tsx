import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  HomeIcon,
  BriefcaseIcon,
  ChartBarIcon,
  DocumentTextIcon,
  UserIcon,
  CogIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { useResponsive } from '@/hooks/useResponsive'
import { useAccessibility } from '@/contexts/AccessibilityContext'
import { Button } from './ui/Button'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Jobs', href: '/jobs', icon: BriefcaseIcon },
  { name: 'Profile', href: '/profile', icon: UserIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Documents', href: '/documents', icon: DocumentTextIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
]

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
  isMobile?: boolean
}

export function Sidebar({ isOpen = true, onClose, isMobile = false }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const router = useRouter()
  const { announceToScreenReader } = useAccessibility()

  // Auto-collapse on tablet
  useEffect(() => {
    if (!isMobile && window.innerWidth < 1024) {
      setIsCollapsed(true)
    }
  }, [isMobile])

  const handleToggleCollapse = () => {
    setIsCollapsed(!isCollapsed)
    announceToScreenReader(isCollapsed ? 'Sidebar expanded' : 'Sidebar collapsed')
  }

  const handleNavClick = () => {
    if (isMobile && onClose) {
      onClose()
    }
  }

  return (
    <div 
      className={`
        bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300
        ${isMobile ? 'w-64' : isCollapsed ? 'w-16' : 'w-64'}
        ${isMobile ? 'h-full' : 'min-h-screen'}
        flex flex-col
      `}
      role="navigation"
      aria-label="Sidebar navigation"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        {/* Collapse toggle for desktop */}
        {!isMobile && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggleCollapse}
            className="p-1 touch-friendly"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRightIcon className="h-5 w-5" />
            ) : (
              <ChevronLeftIcon className="h-5 w-5" />
            )}
          </Button>
        )}

        {/* Close button for mobile */}
        {isMobile && onClose && (
          <div className="flex items-center justify-between w-full">
            <span className="text-lg font-semibold text-gray-900 dark:text-white">
              Navigation
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="p-1 touch-friendly"
              aria-label="Close sidebar"
            >
              <XMarkIcon className="h-5 w-5" />
            </Button>
          </div>
        )}

        {/* Spacer for desktop collapsed state */}
        {!isMobile && isCollapsed && <div />}
      </div>

      {/* Quick actions */}
      {(!isCollapsed || isMobile) && (
        <div className="p-4">
          <Link
            href="/jobs/new"
            onClick={handleNavClick}
            className={`
              flex items-center justify-center w-full px-4 py-3 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors
              ${isMobile ? 'touch-friendly-padding' : ''}
            `}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Job
          </Link>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = router.pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={handleNavClick}
              className={`
                group flex items-center px-3 py-3 text-sm font-medium rounded-md transition-colors
                ${isMobile ? 'touch-friendly-padding' : 'py-2'}
                ${isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                }
              `}
              title={isCollapsed && !isMobile ? item.name : undefined}
              aria-label={`Navigate to ${item.name}`}
            >
              <item.icon
                className={`
                  flex-shrink-0 h-5 w-5
                  ${isActive
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                  }
                  ${isCollapsed && !isMobile ? 'mx-auto' : 'mr-3'}
                `}
                aria-hidden="true"
              />
              {(!isCollapsed || isMobile) && (
                <span className="truncate">{item.name}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      {(!isCollapsed || isMobile) && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 mt-auto">
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            <p className="font-medium">Career Co-Pilot v1.0</p>
            <p className="mt-1">© 2024 All rights reserved</p>
          </div>
        </div>
      )}

      {/* Collapsed state indicator */}
      {isCollapsed && !isMobile && (
        <div className="p-2 border-t border-gray-200 dark:border-gray-700">
          <div className="w-8 h-1 bg-gray-300 dark:bg-gray-600 rounded mx-auto" />
        </div>
      )}
    </div>
  )
}