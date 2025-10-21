import { ReactNode, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useResponsive } from '@/hooks/useResponsive'
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation'
import { useAccessibility } from '@/contexts/AccessibilityContext'
import { Button } from './ui/Button'
import { ResponsiveContainer, ResponsiveStack } from './ResponsiveContainer'
import { cn } from '@/utils/helpers'

interface ResponsiveModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  className?: string
  showCloseButton?: boolean
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  footer?: ReactNode
  fullScreenOnMobile?: boolean
}

/**
 * Responsive modal component that adapts to screen size
 */
export function ResponsiveModal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  className,
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  footer,
  fullScreenOnMobile = true
}: ResponsiveModalProps) {
  const { isMobile, isTablet } = useResponsive()
  const { announceToScreenReader } = useAccessibility()
  const modalRef = useRef<HTMLDivElement>(null)

  useKeyboardNavigation(modalRef, {
    enableEscape: closeOnEscape,
    onEscape: onClose,
    trapFocus: true
  })

  useEffect(() => {
    if (isOpen) {
      // Prevent body scroll
      document.body.style.overflow = 'hidden'
      announceToScreenReader(`Modal opened: ${title || 'Dialog'}`)
      
      // Focus the modal
      if (modalRef.current) {
        modalRef.current.focus()
      }
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, title, announceToScreenReader])

  if (!isOpen) return null

  const sizeClasses = {
    sm: isMobile ? 'max-w-sm' : 'max-w-md',
    md: isMobile ? 'max-w-md' : 'max-w-lg',
    lg: isMobile ? 'max-w-lg' : 'max-w-2xl',
    xl: isMobile ? 'max-w-xl' : 'max-w-4xl',
    full: 'max-w-full'
  }

  const modalContent = (
    <div 
      className={`
        fixed inset-0 z-50 flex items-center justify-center p-4
        ${isMobile && fullScreenOnMobile ? 'p-0' : ''}
      `}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={closeOnOverlayClick ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className={cn(
          'relative bg-white dark:bg-gray-800 rounded-lg shadow-xl transition-all transform',
          'max-h-[90vh] overflow-hidden flex flex-col',
          isMobile && fullScreenOnMobile ? 
            'w-full h-full rounded-none' : 
            `w-full ${sizeClasses[size]} mx-4`,
          className
        )}
        tabIndex={-1}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
            {title && (
              <h2 
                id="modal-title"
                className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white"
              >
                {title}
              </h2>
            )}
            
            {showCloseButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="p-2 touch-friendly"
                aria-label="Close modal"
              >
                <XMarkIcon className="h-5 w-5" />
              </Button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4 sm:p-6">
            {children}
          </div>
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex-shrink-0 p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            {footer}
          </div>
        )}
      </div>
    </div>
  )

  // Render in portal
  if (typeof window !== 'undefined') {
    return createPortal(modalContent, document.body)
  }

  return null
}

interface ResponsiveDrawerProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  position?: 'left' | 'right' | 'bottom'
  className?: string
  showCloseButton?: boolean
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
}

/**
 * Responsive drawer component for mobile-first design
 */
export function ResponsiveDrawer({
  isOpen,
  onClose,
  title,
  children,
  position = 'right',
  className,
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true
}: ResponsiveDrawerProps) {
  const { isMobile } = useResponsive()
  const { announceToScreenReader } = useAccessibility()
  const drawerRef = useRef<HTMLDivElement>(null)

  useKeyboardNavigation(drawerRef, {
    enableEscape: closeOnEscape,
    onEscape: onClose,
    trapFocus: true
  })

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      announceToScreenReader(`Drawer opened: ${title || 'Panel'}`)
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, title, announceToScreenReader])

  if (!isOpen) return null

  const positionClasses = {
    left: 'left-0 top-0 h-full w-80 transform -translate-x-full',
    right: 'right-0 top-0 h-full w-80 transform translate-x-full',
    bottom: 'bottom-0 left-0 right-0 h-96 transform translate-y-full'
  }

  const openClasses = {
    left: 'translate-x-0',
    right: 'translate-x-0',
    bottom: 'translate-y-0'
  }

  const drawerContent = (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={closeOnOverlayClick ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className={cn(
          'fixed bg-white dark:bg-gray-800 shadow-xl transition-transform duration-300 ease-in-out',
          isMobile && position === 'bottom' ? 
            'bottom-0 left-0 right-0 h-[80vh] rounded-t-lg' :
            isMobile ? 
              'left-0 top-0 h-full w-full' :
              positionClasses[position],
          isOpen && (isMobile && position !== 'bottom' ? '' : openClasses[position]),
          className
        )}
        tabIndex={-1}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            {title && (
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h2>
            )}
            
            {showCloseButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="p-2 touch-friendly"
                aria-label="Close drawer"
              >
                <XMarkIcon className="h-5 w-5" />
              </Button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {children}
        </div>
      </div>
    </div>
  )

  if (typeof window !== 'undefined') {
    return createPortal(drawerContent, document.body)
  }

  return null
}

interface ResponsiveBottomSheetProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  className?: string
  showCloseButton?: boolean
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  snapPoints?: string[]
  defaultSnap?: number
}

/**
 * Responsive bottom sheet component for mobile interactions
 */
export function ResponsiveBottomSheet({
  isOpen,
  onClose,
  title,
  children,
  className,
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  snapPoints = ['25%', '50%', '75%'],
  defaultSnap = 1
}: ResponsiveBottomSheetProps) {
  const { isMobile } = useResponsive()
  const { announceToScreenReader } = useAccessibility()
  const sheetRef = useRef<HTMLDivElement>(null)

  useKeyboardNavigation(sheetRef, {
    enableEscape: closeOnEscape,
    onEscape: onClose,
    trapFocus: true
  })

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      announceToScreenReader(`Bottom sheet opened: ${title || 'Panel'}`)
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, title, announceToScreenReader])

  if (!isOpen) return null

  // On desktop, render as a modal instead
  if (!isMobile) {
    return (
      <ResponsiveModal
        isOpen={isOpen}
        onClose={onClose}
        title={title}
        size="md"
        showCloseButton={showCloseButton}
        closeOnOverlayClick={closeOnOverlayClick}
        closeOnEscape={closeOnEscape}
      >
        {children}
      </ResponsiveModal>
    )
  }

  const sheetContent = (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={closeOnOverlayClick ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Bottom Sheet */}
      <div
        ref={sheetRef}
        className={cn(
          'fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 rounded-t-lg shadow-xl transform transition-transform duration-300 ease-out',
          'max-h-[90vh] flex flex-col',
          isOpen ? 'translate-y-0' : 'translate-y-full',
          className
        )}
        style={{ height: snapPoints[defaultSnap] }}
        tabIndex={-1}
      >
        {/* Handle */}
        <div className="flex justify-center p-2">
          <div className="w-12 h-1 bg-gray-300 dark:bg-gray-600 rounded-full" />
        </div>

        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between px-4 pb-2">
            {title && (
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h2>
            )}
            
            {showCloseButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="p-2 touch-friendly"
                aria-label="Close bottom sheet"
              >
                <XMarkIcon className="h-5 w-5" />
              </Button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          {children}
        </div>
      </div>
    </div>
  )

  if (typeof window !== 'undefined') {
    return createPortal(sheetContent, document.body)
  }

  return null
}