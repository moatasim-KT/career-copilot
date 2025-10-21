import React, { forwardRef } from 'react'
import { clsx } from 'clsx'
import { useAccessibility } from '@/contexts/AccessibilityContext'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
  interactive?: boolean
  as?: 'div' | 'article' | 'section'
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
}

interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode
  className?: string
  level?: 1 | 2 | 3 | 4 | 5 | 6
}

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, className = '', interactive = false, as: Component = 'div', ...props }, ref) => {
    const { settings } = useAccessibility()
    
    const baseClasses = 'bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm'
    const interactiveClasses = interactive 
      ? 'hover:shadow-md focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2 cursor-pointer' 
      : ''
    const highContrastClasses = settings.highContrast ? 'border-2' : ''
    const motionClasses = settings.reducedMotion ? 'transition-none' : 'transition-shadow duration-200'

    return (
      <Component
        ref={ref}
        className={clsx(
          baseClasses,
          interactiveClasses,
          highContrastClasses,
          motionClasses,
          className
        )}
        {...props}
      >
        {children}
      </Component>
    )
  }
)

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'px-6 py-4 border-b border-gray-200 dark:border-gray-700',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ children, className = '', level = 3, ...props }, ref) => {
    const Component = `h${level}` as keyof JSX.IntrinsicElements
    
    const levelClasses = {
      1: 'text-2xl',
      2: 'text-xl',
      3: 'text-lg',
      4: 'text-base',
      5: 'text-sm',
      6: 'text-sm'
    }

    return (
      <Component
        ref={ref}
        className={clsx(
          'font-semibold text-gray-900 dark:text-white',
          levelClasses[level],
          className
        )}
        {...props}
      >
        {children}
      </Component>
    )
  }
)

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('px-6 py-4', className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-b-lg',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'
CardHeader.displayName = 'CardHeader'
CardTitle.displayName = 'CardTitle'
CardContent.displayName = 'CardContent'
CardFooter.displayName = 'CardFooter'