import { useEffect, useCallback, useRef } from 'react'
import { KeyboardKeys, FocusManager } from '@/utils/accessibility'
import { useAccessibility } from '@/contexts/AccessibilityContext'

interface KeyboardNavigationOptions {
  // Enable arrow key navigation
  enableArrowKeys?: boolean
  // Enable home/end navigation
  enableHomeEnd?: boolean
  // Enable escape key handling
  enableEscape?: boolean
  // Custom key handlers
  onEscape?: () => void
  onEnter?: () => void
  onSpace?: () => void
  // Focus trap for modals
  trapFocus?: boolean
  // Auto-focus first element
  autoFocus?: boolean
}

export function useKeyboardNavigation(
  containerRef: React.RefObject<HTMLElement>,
  options: KeyboardNavigationOptions = {}
) {
  const { settings, announceToScreenReader } = useAccessibility()
  const previousActiveElement = useRef<Element | null>(null)

  const {
    enableArrowKeys = false,
    enableHomeEnd = false,
    enableEscape = false,
    onEscape,
    onEnter,
    onSpace,
    trapFocus = false,
    autoFocus = false
  } = options

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!settings.keyboardNavigation || !containerRef.current) return

    const { key, target } = event
    const container = containerRef.current
    const activeElement = target as HTMLElement

    // Focus trap for modals
    if (trapFocus) {
      FocusManager.trapFocus(container, event)
    }

    switch (key) {
      case KeyboardKeys.ESCAPE:
        if (enableEscape && onEscape) {
          event.preventDefault()
          onEscape()
          announceToScreenReader('Dialog closed')
        }
        break

      case KeyboardKeys.ENTER:
        if (onEnter && (activeElement.tagName === 'BUTTON' || activeElement.getAttribute('role') === 'button')) {
          event.preventDefault()
          onEnter()
        }
        break

      case KeyboardKeys.SPACE:
        if (onSpace && (activeElement.tagName === 'BUTTON' || activeElement.getAttribute('role') === 'button')) {
          event.preventDefault()
          onSpace()
        }
        break

      case KeyboardKeys.ARROW_UP:
      case KeyboardKeys.ARROW_DOWN:
        if (enableArrowKeys) {
          event.preventDefault()
          const direction = key === KeyboardKeys.ARROW_UP ? 'previous' : 'next'
          const nextElement = FocusManager.getNextFocusableElement(activeElement, direction)
          if (nextElement && container.contains(nextElement)) {
            nextElement.focus()
            announceToScreenReader(`Focused ${nextElement.getAttribute('aria-label') || nextElement.textContent || 'element'}`)
          }
        }
        break

      case KeyboardKeys.ARROW_LEFT:
      case KeyboardKeys.ARROW_RIGHT:
        if (enableArrowKeys) {
          event.preventDefault()
          const direction = key === KeyboardKeys.ARROW_LEFT ? 'previous' : 'next'
          const nextElement = FocusManager.getNextFocusableElement(activeElement, direction)
          if (nextElement && container.contains(nextElement)) {
            nextElement.focus()
            announceToScreenReader(`Focused ${nextElement.getAttribute('aria-label') || nextElement.textContent || 'element'}`)
          }
        }
        break

      case KeyboardKeys.HOME:
        if (enableHomeEnd) {
          event.preventDefault()
          const firstFocusable = container.querySelector(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          ) as HTMLElement
          if (firstFocusable) {
            firstFocusable.focus()
            announceToScreenReader('Focused first element')
          }
        }
        break

      case KeyboardKeys.END:
        if (enableHomeEnd) {
          event.preventDefault()
          const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          ) as NodeListOf<HTMLElement>
          const lastFocusable = focusableElements[focusableElements.length - 1]
          if (lastFocusable) {
            lastFocusable.focus()
            announceToScreenReader('Focused last element')
          }
        }
        break
    }
  }, [
    settings.keyboardNavigation,
    containerRef,
    enableArrowKeys,
    enableHomeEnd,
    enableEscape,
    onEscape,
    onEnter,
    onSpace,
    trapFocus,
    announceToScreenReader
  ])

  useEffect(() => {
    const container = containerRef.current
    if (!container || !settings.keyboardNavigation) return

    // Store previous active element for focus restoration
    if (trapFocus) {
      previousActiveElement.current = document.activeElement
    }

    // Auto-focus first element if requested
    if (autoFocus) {
      const firstFocusable = container.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as HTMLElement
      if (firstFocusable) {
        firstFocusable.focus()
      }
    }

    container.addEventListener('keydown', handleKeyDown)

    return () => {
      container.removeEventListener('keydown', handleKeyDown)
      
      // Restore focus when component unmounts (useful for modals)
      if (trapFocus && previousActiveElement.current) {
        FocusManager.restoreFocus(previousActiveElement.current)
      }
    }
  }, [handleKeyDown, settings.keyboardNavigation, trapFocus, autoFocus])

  return {
    // Helper functions for manual focus management
    focusFirst: useCallback(() => {
      const container = containerRef.current
      if (!container) return

      const firstFocusable = container.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as HTMLElement
      if (firstFocusable) {
        firstFocusable.focus()
      }
    }, [containerRef]),

    focusLast: useCallback(() => {
      const container = containerRef.current
      if (!container) return

      const focusableElements = container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as NodeListOf<HTMLElement>
      const lastFocusable = focusableElements[focusableElements.length - 1]
      if (lastFocusable) {
        lastFocusable.focus()
      }
    }, [containerRef]),

    restoreFocus: useCallback(() => {
      if (previousActiveElement.current) {
        FocusManager.restoreFocus(previousActiveElement.current)
      }
    }, [])
  }
}

// Hook for managing focus within lists (like job cards)
export function useListNavigation(
  listRef: React.RefObject<HTMLElement>,
  options: {
    orientation?: 'vertical' | 'horizontal' | 'both'
    wrap?: boolean
    onItemSelect?: (index: number) => void
  } = {}
) {
  const { settings, announceToScreenReader } = useAccessibility()
  const { orientation = 'vertical', wrap = true, onItemSelect } = options

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!settings.keyboardNavigation || !listRef.current) return

    const { key, target } = event
    const list = listRef.current
    const items = Array.from(list.querySelectorAll('[role="listitem"], [data-list-item]')) as HTMLElement[]
    const currentIndex = items.indexOf(target as HTMLElement)

    if (currentIndex === -1) return

    let nextIndex = currentIndex

    switch (key) {
      case KeyboardKeys.ARROW_UP:
        if (orientation === 'vertical' || orientation === 'both') {
          event.preventDefault()
          nextIndex = currentIndex - 1
          if (nextIndex < 0 && wrap) {
            nextIndex = items.length - 1
          }
        }
        break

      case KeyboardKeys.ARROW_DOWN:
        if (orientation === 'vertical' || orientation === 'both') {
          event.preventDefault()
          nextIndex = currentIndex + 1
          if (nextIndex >= items.length && wrap) {
            nextIndex = 0
          }
        }
        break

      case KeyboardKeys.ARROW_LEFT:
        if (orientation === 'horizontal' || orientation === 'both') {
          event.preventDefault()
          nextIndex = currentIndex - 1
          if (nextIndex < 0 && wrap) {
            nextIndex = items.length - 1
          }
        }
        break

      case KeyboardKeys.ARROW_RIGHT:
        if (orientation === 'horizontal' || orientation === 'both') {
          event.preventDefault()
          nextIndex = currentIndex + 1
          if (nextIndex >= items.length && wrap) {
            nextIndex = 0
          }
        }
        break

      case KeyboardKeys.HOME:
        event.preventDefault()
        nextIndex = 0
        break

      case KeyboardKeys.END:
        event.preventDefault()
        nextIndex = items.length - 1
        break

      case KeyboardKeys.ENTER:
      case KeyboardKeys.SPACE:
        if (onItemSelect) {
          event.preventDefault()
          onItemSelect(currentIndex)
        }
        break
    }

    if (nextIndex !== currentIndex && nextIndex >= 0 && nextIndex < items.length) {
      items[nextIndex].focus()
      announceToScreenReader(`Item ${nextIndex + 1} of ${items.length}`)
    }
  }, [settings.keyboardNavigation, listRef, orientation, wrap, onItemSelect, announceToScreenReader])

  useEffect(() => {
    const list = listRef.current
    if (!list || !settings.keyboardNavigation) return

    list.addEventListener('keydown', handleKeyDown)

    return () => {
      list.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown, settings.keyboardNavigation])
}

// Hook for managing roving tabindex pattern
export function useRovingTabIndex(
  containerRef: React.RefObject<HTMLElement>,
  activeIndex: number = 0
) {
  const { settings } = useAccessibility()

  useEffect(() => {
    const container = containerRef.current
    if (!container || !settings.keyboardNavigation) return

    const items = container.querySelectorAll('[role="tab"], [role="menuitem"], [data-roving-item]') as NodeListOf<HTMLElement>
    
    items.forEach((item, index) => {
      if (index === activeIndex) {
        item.setAttribute('tabindex', '0')
        item.setAttribute('aria-selected', 'true')
      } else {
        item.setAttribute('tabindex', '-1')
        item.setAttribute('aria-selected', 'false')
      }
    })
  }, [containerRef, activeIndex, settings.keyboardNavigation])
}