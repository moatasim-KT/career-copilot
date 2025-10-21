import { useAccessibility } from '@/contexts/AccessibilityContext'

export function SkipLinks() {
  const { settings } = useAccessibility()

  if (!settings.skipLinks) return null

  const skipLinks = [
    { href: '#main-content', label: 'Skip to main content' },
    { href: '#navigation', label: 'Skip to navigation' },
    { href: '#search', label: 'Skip to search' },
    { href: '#footer', label: 'Skip to footer' }
  ]

  return (
    <div className="sr-only focus-within:not-sr-only">
      <nav aria-label="Skip navigation links" className="fixed top-0 left-0 z-50">
        <ul className="flex flex-col gap-1 p-2">
          {skipLinks.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className="skip-link bg-blue-600 text-white px-4 py-2 rounded-md font-medium text-sm hover:bg-blue-700 focus:bg-blue-700 transition-colors"
                onClick={(e) => {
                  e.preventDefault()
                  const target = document.querySelector(link.href)
                  if (target) {
                    target.scrollIntoView({ behavior: 'smooth' })
                    // Focus the target element if it's focusable
                    if (target instanceof HTMLElement && target.tabIndex >= 0) {
                      target.focus()
                    } else {
                      // Find the first focusable element within the target
                      const focusable = target.querySelector(
                        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                      ) as HTMLElement
                      if (focusable) {
                        focusable.focus()
                      }
                    }
                  }
                }}
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}