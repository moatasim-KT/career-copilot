import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { MotionPreferences, HighContrast } from '@/utils/accessibility'

interface AccessibilitySettings {
  // User preferences
  reducedMotion: boolean
  highContrast: boolean
  largeText: boolean
  screenReaderOptimized: boolean
  keyboardNavigation: boolean
  
  // System detection
  prefersReducedMotion: boolean
  prefersHighContrast: boolean
  
  // Focus management
  showFocusRings: boolean
  skipLinks: boolean
}

interface AccessibilityContextType {
  settings: AccessibilitySettings
  updateSetting: (key: keyof AccessibilitySettings, value: boolean) => void
  resetToDefaults: () => void
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void
}

const defaultSettings: AccessibilitySettings = {
  reducedMotion: false,
  highContrast: false,
  largeText: false,
  screenReaderOptimized: false,
  keyboardNavigation: true,
  prefersReducedMotion: false,
  prefersHighContrast: false,
  showFocusRings: true,
  skipLinks: true
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined)

interface AccessibilityProviderProps {
  children: ReactNode
}

export function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  const [settings, setSettings] = useState<AccessibilitySettings>(defaultSettings)

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('accessibility-settings')
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings)
        setSettings(prev => ({ ...prev, ...parsed }))
      } catch (error) {
        console.warn('Failed to parse accessibility settings:', error)
      }
    }

    // Detect system preferences
    const prefersReducedMotion = MotionPreferences.prefersReducedMotion()
    const prefersHighContrast = HighContrast.isHighContrastMode()

    setSettings(prev => ({
      ...prev,
      prefersReducedMotion,
      prefersHighContrast,
      // Auto-enable based on system preferences if not explicitly set
      reducedMotion: prev.reducedMotion || prefersReducedMotion,
      highContrast: prev.highContrast || prefersHighContrast
    }))

    // Listen for system preference changes
    const motionMediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const contrastMediaQuery = window.matchMedia('(prefers-contrast: high)')

    const handleMotionChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({
        ...prev,
        prefersReducedMotion: e.matches,
        reducedMotion: prev.reducedMotion || e.matches
      }))
    }

    const handleContrastChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({
        ...prev,
        prefersHighContrast: e.matches,
        highContrast: prev.highContrast || e.matches
      }))
    }

    motionMediaQuery.addEventListener('change', handleMotionChange)
    contrastMediaQuery.addEventListener('change', handleContrastChange)

    return () => {
      motionMediaQuery.removeEventListener('change', handleMotionChange)
      contrastMediaQuery.removeEventListener('change', handleContrastChange)
    }
  }, [])

  useEffect(() => {
    // Save settings to localStorage
    const settingsToSave = {
      reducedMotion: settings.reducedMotion,
      highContrast: settings.highContrast,
      largeText: settings.largeText,
      screenReaderOptimized: settings.screenReaderOptimized,
      keyboardNavigation: settings.keyboardNavigation,
      showFocusRings: settings.showFocusRings,
      skipLinks: settings.skipLinks
    }
    localStorage.setItem('accessibility-settings', JSON.stringify(settingsToSave))

    // Apply CSS classes to document
    const documentElement = document.documentElement
    
    // Reduced motion
    if (settings.reducedMotion) {
      documentElement.classList.add('reduce-motion')
    } else {
      documentElement.classList.remove('reduce-motion')
    }

    // High contrast
    if (settings.highContrast) {
      documentElement.classList.add('high-contrast')
    } else {
      documentElement.classList.remove('high-contrast')
    }

    // Large text
    if (settings.largeText) {
      documentElement.classList.add('large-text')
    } else {
      documentElement.classList.remove('large-text')
    }

    // Screen reader optimized
    if (settings.screenReaderOptimized) {
      documentElement.classList.add('screen-reader-optimized')
    } else {
      documentElement.classList.remove('screen-reader-optimized')
    }

    // Focus rings
    if (settings.showFocusRings) {
      documentElement.classList.add('show-focus-rings')
    } else {
      documentElement.classList.remove('show-focus-rings')
    }
  }, [settings])

  const updateSetting = (key: keyof AccessibilitySettings, value: boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const resetToDefaults = () => {
    setSettings(defaultSettings)
    localStorage.removeItem('accessibility-settings')
  }

  const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    // Create or update live region
    let liveRegion = document.getElementById('accessibility-live-region')
    if (!liveRegion) {
      liveRegion = document.createElement('div')
      liveRegion.id = 'accessibility-live-region'
      liveRegion.setAttribute('aria-live', priority)
      liveRegion.setAttribute('aria-atomic', 'true')
      liveRegion.className = 'sr-only'
      document.body.appendChild(liveRegion)
    }

    liveRegion.setAttribute('aria-live', priority)
    liveRegion.textContent = message

    // Clear after announcement
    setTimeout(() => {
      if (liveRegion) {
        liveRegion.textContent = ''
      }
    }, 1000)
  }

  const value: AccessibilityContextType = {
    settings,
    updateSetting,
    resetToDefaults,
    announceToScreenReader
  }

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  )
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext)
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider')
  }
  return context
}

// Hook for checking if user prefers reduced motion
export function useReducedMotion() {
  const { settings } = useAccessibility()
  return settings.reducedMotion || settings.prefersReducedMotion
}

// Hook for checking if user prefers high contrast
export function useHighContrast() {
  const { settings } = useAccessibility()
  return settings.highContrast || settings.prefersHighContrast
}

// Hook for screen reader announcements
export function useScreenReaderAnnouncements() {
  const { announceToScreenReader } = useAccessibility()
  return announceToScreenReader
}