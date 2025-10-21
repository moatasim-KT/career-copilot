import { ButtonHTMLAttributes, forwardRef } from 'react'
import { clsx } from 'clsx'
import { useAccessibility } from '@/contexts/AccessibilityContext'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  loadingText?: string
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant = 'primary', 
    size = 'md', 
    loading = false, 
    loadingText = 'Loading...', 
    disabled, 
    children, 
    'aria-label': ariaLabel,
    ...props 
  }, ref) => {
    const { settings } = useAccessibility()
    
    const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed relative'
    
    const variants = {
      primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600 focus:ring-offset-white dark:focus:ring-offset-gray-900',
      secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600 focus:ring-offset-white dark:focus:ring-offset-gray-900',
      ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500 dark:text-gray-300 dark:hover:bg-gray-800 focus:ring-offset-white dark:focus:ring-offset-gray-900',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 dark:bg-red-500 dark:hover:bg-red-600 focus:ring-offset-white dark:focus:ring-offset-gray-900'
    }
    
    const sizes = {
      sm: 'px-3 py-1.5 text-sm min-h-[2rem]',
      md: 'px-4 py-2 text-sm min-h-[2.5rem]',
      lg: 'px-6 py-3 text-base min-h-[3rem]'
    }

    // Enhanced focus styles for high contrast mode
    const highContrastClasses = settings.highContrast ? 'border-2 border-current' : ''
    
    // Reduced motion classes
    const motionClasses = settings.reducedMotion ? 'transition-none' : 'transition-colors duration-200'

    return (
      <button
        ref={ref}
        className={clsx(
          baseClasses,
          variants[variant],
          sizes[size],
          highContrastClasses,
          motionClasses,
          className
        )}
        disabled={disabled || loading}
        aria-label={loading ? loadingText : ariaLabel}
        aria-busy={loading}
        {...props}
      >
        {loading && (
          <>
            <svg
              className={clsx(
                'h-4 w-4 mr-2',
                settings.reducedMotion ? '' : 'animate-spin'
              )}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="sr-only">{loadingText}</span>
          </>
        )}
        <span className={loading ? 'opacity-0' : ''}>{children}</span>
      </button>
    )
  }
)

Button.displayName = 'Button'