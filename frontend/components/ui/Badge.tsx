import React, { forwardRef } from 'react'
import { clsx } from 'clsx'
import { useAccessibility } from '@/contexts/AccessibilityContext'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ 
    children, 
    className = '', 
    variant = 'default',
    size = 'md',
    ...props 
  }, ref) => {
    const { settings } = useAccessibility()
    
    const baseClasses = 'inline-flex items-center font-medium rounded-full'
    
    const sizeClasses = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-0.5 text-xs',
      lg: 'px-3 py-1 text-sm'
    }
    
    const variantClasses = {
      default: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      secondary: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
      destructive: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      outline: 'border border-gray-200 text-gray-800 dark:border-gray-600 dark:text-gray-300',
      success: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
      info: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/20 dark:text-cyan-400',
      danger: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
    }
    
    // Enhanced contrast for high contrast mode
    const highContrastClasses = settings.highContrast 
      ? 'border-2 border-current font-semibold' 
      : ''

    return (
      <span
        ref={ref}
        className={clsx(
          baseClasses,
          sizeClasses[size],
          variantClasses[variant],
          highContrastClasses,
          className
        )}
        {...props}
      >
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'