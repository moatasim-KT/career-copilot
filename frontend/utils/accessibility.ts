/**
 * Accessibility utilities and helpers for Career Co-Pilot
 */

// ARIA live region announcer for screen readers
export class LiveAnnouncer {
  private static instance: LiveAnnouncer
  private liveRegion: HTMLElement | null = null

  private constructor() {
    if (typeof window !== 'undefined') {
      this.createLiveRegion()
    }
  }

  static getInstance(): LiveAnnouncer {
    if (!LiveAnnouncer.instance) {
      LiveAnnouncer.instance = new LiveAnnouncer()
    }
    return LiveAnnouncer.instance
  }

  private createLiveRegion() {
    if (this.liveRegion) return

    this.liveRegion = document.createElement('div')
    this.liveRegion.setAttribute('aria-live', 'polite')
    this.liveRegion.setAttribute('aria-atomic', 'true')
    this.liveRegion.setAttribute('aria-relevant', 'additions text')
    this.liveRegion.className = 'sr-only'
    document.body.appendChild(this.liveRegion)
  }

  announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
    if (!this.liveRegion) {
      this.createLiveRegion()
    }

    if (this.liveRegion) {
      this.liveRegion.setAttribute('aria-live', priority)
      this.liveRegion.textContent = message

      // Clear after announcement to allow repeated messages
      setTimeout(() => {
        if (this.liveRegion) {
          this.liveRegion.textContent = ''
        }
      }, 1000)
    }
  }
}

// Keyboard navigation utilities
export const KeyboardKeys = {
  ENTER: 'Enter',
  SPACE: ' ',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  ARROW_LEFT: 'ArrowLeft',
  ARROW_RIGHT: 'ArrowRight',
  TAB: 'Tab',
  HOME: 'Home',
  END: 'End',
  PAGE_UP: 'PageUp',
  PAGE_DOWN: 'PageDown'
} as const

export type KeyboardKey = typeof KeyboardKeys[keyof typeof KeyboardKeys]

// Focus management utilities
export class FocusManager {
  static trapFocus(element: HTMLElement, event: KeyboardEvent) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    if (event.key === KeyboardKeys.TAB) {
      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus()
          event.preventDefault()
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus()
          event.preventDefault()
        }
      }
    }
  }

  static restoreFocus(previousActiveElement: Element | null) {
    if (previousActiveElement && 'focus' in previousActiveElement) {
      (previousActiveElement as HTMLElement).focus()
    }
  }

  static getNextFocusableElement(
    currentElement: HTMLElement,
    direction: 'next' | 'previous' = 'next'
  ): HTMLElement | null {
    const focusableElements = Array.from(
      document.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
    ) as HTMLElement[]

    const currentIndex = focusableElements.indexOf(currentElement)
    if (currentIndex === -1) return null

    const nextIndex = direction === 'next' 
      ? (currentIndex + 1) % focusableElements.length
      : (currentIndex - 1 + focusableElements.length) % focusableElements.length

    return focusableElements[nextIndex]
  }
}

// Color contrast utilities
export const ColorContrast = {
  // WCAG AA compliant color combinations
  getContrastRatio(foreground: string, background: string): number {
    const getLuminance = (color: string): number => {
      // Convert hex to RGB
      const hex = color.replace('#', '')
      const r = parseInt(hex.substr(0, 2), 16) / 255
      const g = parseInt(hex.substr(2, 2), 16) / 255
      const b = parseInt(hex.substr(4, 2), 16) / 255

      // Calculate relative luminance
      const sRGB = [r, g, b].map(c => {
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
      })

      return 0.2126 * sRGB[0] + 0.7152 * sRGB[1] + 0.0722 * sRGB[2]
    }

    const l1 = getLuminance(foreground)
    const l2 = getLuminance(background)
    const lighter = Math.max(l1, l2)
    const darker = Math.min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)
  },

  meetsWCAGAA(foreground: string, background: string, isLargeText = false): boolean {
    const ratio = this.getContrastRatio(foreground, background)
    return isLargeText ? ratio >= 3 : ratio >= 4.5
  },

  meetsWCAGAAA(foreground: string, background: string, isLargeText = false): boolean {
    const ratio = this.getContrastRatio(foreground, background)
    return isLargeText ? ratio >= 4.5 : ratio >= 7
  }
}

// Screen reader utilities
export const ScreenReader = {
  // Generate descriptive text for complex UI elements
  generateJobCardDescription(job: {
    title: string
    company: string
    location?: string
    status: string
    salary_min?: number
    salary_max?: number
    currency?: string
    recommendation_score?: number
  }): string {
    let description = `Job: ${job.title} at ${job.company}`
    
    if (job.location) {
      description += `, located in ${job.location}`
    }
    
    description += `. Current status: ${job.status.replace('_', ' ')}`
    
    if (job.salary_min || job.salary_max) {
      const currency = job.currency || 'USD'
      if (job.salary_min && job.salary_max) {
        description += `. Salary range: ${job.salary_min.toLocaleString()} to ${job.salary_max.toLocaleString()} ${currency}`
      } else if (job.salary_min) {
        description += `. Minimum salary: ${job.salary_min.toLocaleString()} ${currency}`
      } else if (job.salary_max) {
        description += `. Maximum salary: ${job.salary_max.toLocaleString()} ${currency}`
      }
    }
    
    if (job.recommendation_score) {
      description += `. Match score: ${Math.round(job.recommendation_score * 100)} percent`
    }
    
    return description
  },

  // Generate status announcements
  generateStatusAnnouncement(action: string, item: string, success: boolean): string {
    const result = success ? 'successfully' : 'failed to'
    return `${action} ${item} ${result}`
  }
}

// Reduced motion utilities
export const MotionPreferences = {
  prefersReducedMotion(): boolean {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  },

  getTransitionDuration(defaultDuration: string): string {
    return this.prefersReducedMotion() ? '0ms' : defaultDuration
  },

  getAnimationClass(animationClass: string, reducedClass = ''): string {
    return this.prefersReducedMotion() ? reducedClass : animationClass
  }
}

// High contrast mode detection
export const HighContrast = {
  isHighContrastMode(): boolean {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-contrast: high)').matches
  },

  getHighContrastClass(normalClass: string, highContrastClass: string): string {
    return this.isHighContrastMode() ? highContrastClass : normalClass
  }
}

// Accessibility testing utilities (for development)
export const A11yTesting = {
  // Check for missing alt text on images
  checkImageAltText(): string[] {
    const images = document.querySelectorAll('img')
    const issues: string[] = []
    
    images.forEach((img, index) => {
      if (!img.alt && !img.getAttribute('aria-label') && !img.getAttribute('aria-labelledby')) {
        issues.push(`Image ${index + 1} is missing alt text`)
      }
    })
    
    return issues
  },

  // Check for proper heading hierarchy
  checkHeadingHierarchy(): string[] {
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6')
    const issues: string[] = []
    let previousLevel = 0
    
    headings.forEach((heading, index) => {
      const currentLevel = parseInt(heading.tagName.charAt(1))
      
      if (index === 0 && currentLevel !== 1) {
        issues.push('Page should start with an h1 heading')
      }
      
      if (currentLevel > previousLevel + 1) {
        issues.push(`Heading level jumps from h${previousLevel} to h${currentLevel}`)
      }
      
      previousLevel = currentLevel
    })
    
    return issues
  },

  // Check for proper form labels
  checkFormLabels(): string[] {
    const inputs = document.querySelectorAll('input, select, textarea')
    const issues: string[] = []
    
    inputs.forEach((input, index) => {
      const hasLabel = input.getAttribute('aria-label') || 
                      input.getAttribute('aria-labelledby') ||
                      document.querySelector(`label[for="${input.id}"]`)
      
      if (!hasLabel) {
        issues.push(`Form input ${index + 1} is missing a label`)
      }
    })
    
    return issues
  },

  // Run all accessibility checks
  runAllChecks(): { category: string; issues: string[] }[] {
    return [
      { category: 'Images', issues: this.checkImageAltText() },
      { category: 'Headings', issues: this.checkHeadingHierarchy() },
      { category: 'Forms', issues: this.checkFormLabels() }
    ]
  }
}

// Export singleton instance
export const liveAnnouncer = LiveAnnouncer.getInstance()