import { InputHTMLAttributes, forwardRef, useId } from 'react'
import { clsx } from 'clsx'
import { ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline'
import { useAccessibility } from '@/contexts/AccessibilityContext'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  required?: boolean
  showRequiredIndicator?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    label, 
    error, 
    helperText, 
    id, 
    required = false,
    showRequiredIndicator = true,
    'aria-describedby': ariaDescribedBy,
    ...props 
  }, ref) => {
    const { settings } = useAccessibility()
    const inputId = id || useId()
    const errorId = `${inputId}-error`
    const helperTextId = `${inputId}-helper`
    
    // Build aria-describedby
    const describedByIds = []
    if (error) describedByIds.push(errorId)
    if (helperText && !error) describedByIds.push(helperTextId)
    if (ariaDescribedBy) describedByIds.push(ariaDescribedBy)
    
    const finalAriaDescribedBy = describedByIds.length > 0 ? describedByIds.join(' ') : undefined

    // Enhanced styles for high contrast mode
    const highContrastClasses = settings.highContrast 
      ? 'border-2 focus:border-4' 
      : 'border focus:ring-1'

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            {label}
            {required && showRequiredIndicator && (
              <span className="text-red-500 ml-1" aria-label="required">
                *
              </span>
            )}
          </label>
        )}
        <div className="relative">
          <input
            ref={ref}
            id={inputId}
            required={required}
            aria-describedby={finalAriaDescribedBy}
            aria-invalid={error ? 'true' : 'false'}
            className={clsx(
              'block w-full rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm',
              'border-gray-300 dark:border-gray-600',
              'focus:border-blue-500 focus:ring-blue-500 dark:focus:border-blue-400 dark:focus:ring-blue-400',
              'placeholder:text-gray-400 dark:placeholder:text-gray-500',
              'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:text-gray-500 disabled:cursor-not-allowed',
              settings.reducedMotion ? 'transition-none' : 'transition-colors duration-200',
              highContrastClasses,
              error && 'border-red-300 dark:border-red-600 focus:border-red-500 focus:ring-red-500 pr-10',
              className
            )}
            {...props}
          />
          {error && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <ExclamationTriangleIcon 
                className="h-5 w-5 text-red-500" 
                aria-hidden="true"
              />
            </div>
          )}
        </div>
        
        {error && (
          <div 
            id={errorId}
            className="mt-1 flex items-start gap-1 text-sm text-red-600 dark:text-red-400"
            role="alert"
            aria-live="polite"
          >
            <ExclamationTriangleIcon 
              className="h-4 w-4 mt-0.5 flex-shrink-0" 
              aria-hidden="true"
            />
            <span>{error}</span>
          </div>
        )}
        
        {helperText && !error && (
          <div 
            id={helperTextId}
            className="mt-1 flex items-start gap-1 text-sm text-gray-500 dark:text-gray-400"
          >
            <InformationCircleIcon 
              className="h-4 w-4 mt-0.5 flex-shrink-0" 
              aria-hidden="true"
            />
            <span>{helperText}</span>
          </div>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'