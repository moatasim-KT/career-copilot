import { ReactNode, FormEvent } from 'react'
import { useResponsive, useResponsiveSpacing } from '@/hooks/useResponsive'
import { ResponsiveContainer, ResponsiveStack, ResponsiveGrid } from './ResponsiveContainer'
import { Button } from './ui/Button'
import { cn } from '@/utils/helpers'

interface ResponsiveFormProps {
  children: ReactNode
  onSubmit?: (e: FormEvent<HTMLFormElement>) => void
  className?: string
  layout?: 'vertical' | 'horizontal' | 'grid' | 'responsive'
  columns?: {
    mobile?: number
    tablet?: number
    desktop?: number
  }
  spacing?: 'sm' | 'md' | 'lg'
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
}

/**
 * Responsive form container with adaptive layouts
 */
export function ResponsiveForm({
  children,
  onSubmit,
  className,
  layout = 'responsive',
  columns = { mobile: 1, tablet: 2, desktop: 2 },
  spacing = 'md',
  maxWidth = 'lg'
}: ResponsiveFormProps) {
  const { isMobile } = useResponsive()
  const { sectionSpacing } = useResponsiveSpacing()

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    onSubmit?.(e)
  }

  const renderContent = () => {
    switch (layout) {
      case 'grid':
        return (
          <ResponsiveGrid columns={columns} gap={spacing}>
            {children}
          </ResponsiveGrid>
        )
      
      case 'horizontal':
        return (
          <ResponsiveStack direction="horizontal" spacing={spacing} wrap>
            {children}
          </ResponsiveStack>
        )
      
      case 'vertical':
        return (
          <ResponsiveStack direction="vertical" spacing={spacing}>
            {children}
          </ResponsiveStack>
        )
      
      case 'responsive':
      default:
        return isMobile ? (
          <ResponsiveStack direction="vertical" spacing={spacing}>
            {children}
          </ResponsiveStack>
        ) : (
          <ResponsiveGrid columns={columns} gap={spacing}>
            {children}
          </ResponsiveGrid>
        )
    }
  }

  return (
    <ResponsiveContainer maxWidth={maxWidth} className={className}>
      <form onSubmit={handleSubmit} className={sectionSpacing}>
        {renderContent()}
      </form>
    </ResponsiveContainer>
  )
}

interface ResponsiveFieldGroupProps {
  children: ReactNode
  label?: string
  description?: string
  required?: boolean
  error?: string
  className?: string
  fullWidth?: boolean
}

/**
 * Responsive field group with label and validation
 */
export function ResponsiveFieldGroup({
  children,
  label,
  description,
  required,
  error,
  className,
  fullWidth = false
}: ResponsiveFieldGroupProps) {
  const { isMobile } = useResponsive()

  return (
    <div className={cn(
      'space-y-2',
      fullWidth && 'col-span-full',
      className
    )}>
      {label && (
        <label className={cn(
          'block font-medium text-gray-900 dark:text-white',
          isMobile ? 'text-sm' : 'text-base'
        )}>
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      {description && (
        <p className={cn(
          'text-gray-600 dark:text-gray-400',
          isMobile ? 'text-xs' : 'text-sm'
        )}>
          {description}
        </p>
      )}
      
      <div className="space-y-1">
        {children}
        
        {error && (
          <p className={cn(
            'text-red-600 dark:text-red-400',
            isMobile ? 'text-xs' : 'text-sm'
          )}>
            {error}
          </p>
        )}
      </div>
    </div>
  )
}

interface ResponsiveFormActionsProps {
  children: ReactNode
  align?: 'left' | 'center' | 'right' | 'between'
  className?: string
  sticky?: boolean
}

/**
 * Responsive form actions with adaptive positioning
 */
export function ResponsiveFormActions({
  children,
  align = 'right',
  className,
  sticky = false
}: ResponsiveFormActionsProps) {
  const { isMobile } = useResponsive()

  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between'
  }

  return (
    <div className={cn(
      'flex gap-3 pt-6 border-t border-gray-200 dark:border-gray-700',
      isMobile ? 'flex-col' : 'flex-row',
      !isMobile && alignClasses[align],
      sticky && 'sticky bottom-0 bg-white dark:bg-gray-800 z-10 -mx-6 px-6 pb-6',
      className
    )}>
      {children}
    </div>
  )
}

interface ResponsiveInputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  disabled?: boolean
  required?: boolean
  className?: string
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
}

/**
 * Responsive input component with touch-friendly sizing
 */
export function ResponsiveInput({
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled,
  required,
  className,
  size = 'md',
  fullWidth = true
}: ResponsiveInputProps) {
  const { isMobile } = useResponsive()

  const sizeClasses = {
    sm: isMobile ? 'px-3 py-3 text-sm' : 'px-3 py-2 text-sm',
    md: isMobile ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm',
    lg: isMobile ? 'px-4 py-4 text-lg' : 'px-4 py-3 text-base'
  }

  return (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      required={required}
      className={cn(
        'block border border-gray-300 dark:border-gray-600 rounded-md shadow-sm',
        'bg-white dark:bg-gray-800 text-gray-900 dark:text-white',
        'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
        'disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed',
        'transition-colors duration-200',
        sizeClasses[size],
        fullWidth ? 'w-full' : 'w-auto',
        isMobile && 'touch-friendly',
        className
      )}
    />
  )
}

interface ResponsiveTextareaProps {
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  disabled?: boolean
  required?: boolean
  rows?: number
  className?: string
  resize?: boolean
  fullWidth?: boolean
}

/**
 * Responsive textarea component
 */
export function ResponsiveTextarea({
  placeholder,
  value,
  onChange,
  disabled,
  required,
  rows = 4,
  className,
  resize = true,
  fullWidth = true
}: ResponsiveTextareaProps) {
  const { isMobile } = useResponsive()

  return (
    <textarea
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      required={required}
      rows={isMobile ? Math.max(rows - 1, 3) : rows}
      className={cn(
        'block border border-gray-300 dark:border-gray-600 rounded-md shadow-sm',
        'bg-white dark:bg-gray-800 text-gray-900 dark:text-white',
        'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
        'disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed',
        'transition-colors duration-200',
        isMobile ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm',
        fullWidth ? 'w-full' : 'w-auto',
        !resize && 'resize-none',
        isMobile && 'touch-friendly',
        className
      )}
    />
  )
}

interface ResponsiveSelectProps {
  options: { value: string; label: string }[]
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  disabled?: boolean
  required?: boolean
  className?: string
  fullWidth?: boolean
}

/**
 * Responsive select component
 */
export function ResponsiveSelect({
  options,
  value,
  onChange,
  placeholder,
  disabled,
  required,
  className,
  fullWidth = true
}: ResponsiveSelectProps) {
  const { isMobile } = useResponsive()

  return (
    <select
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      required={required}
      className={cn(
        'block border border-gray-300 dark:border-gray-600 rounded-md shadow-sm',
        'bg-white dark:bg-gray-800 text-gray-900 dark:text-white',
        'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
        'disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed',
        'transition-colors duration-200',
        isMobile ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm',
        fullWidth ? 'w-full' : 'w-auto',
        isMobile && 'touch-friendly',
        className
      )}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )
}

interface ResponsiveCheckboxProps {
  checked?: boolean
  onChange?: (checked: boolean) => void
  label?: string
  description?: string
  disabled?: boolean
  required?: boolean
  className?: string
}

/**
 * Responsive checkbox component
 */
export function ResponsiveCheckbox({
  checked,
  onChange,
  label,
  description,
  disabled,
  required,
  className
}: ResponsiveCheckboxProps) {
  const { isMobile } = useResponsive()

  return (
    <div className={cn('flex items-start', className)}>
      <div className="flex items-center h-5">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange?.(e.target.checked)}
          disabled={disabled}
          required={required}
          className={cn(
            'rounded border-gray-300 dark:border-gray-600',
            'text-blue-600 focus:ring-blue-500',
            'disabled:cursor-not-allowed',
            isMobile ? 'h-5 w-5' : 'h-4 w-4',
            isMobile && 'touch-friendly'
          )}
        />
      </div>
      
      {(label || description) && (
        <div className="ml-3">
          {label && (
            <label className={cn(
              'font-medium text-gray-900 dark:text-white',
              isMobile ? 'text-base' : 'text-sm'
            )}>
              {label}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          
          {description && (
            <p className={cn(
              'text-gray-600 dark:text-gray-400',
              isMobile ? 'text-sm' : 'text-xs'
            )}>
              {description}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

interface ResponsiveRadioGroupProps {
  options: { value: string; label: string; description?: string }[]
  value?: string
  onChange?: (value: string) => void
  name: string
  disabled?: boolean
  required?: boolean
  className?: string
  layout?: 'vertical' | 'horizontal' | 'grid'
}

/**
 * Responsive radio group component
 */
export function ResponsiveRadioGroup({
  options,
  value,
  onChange,
  name,
  disabled,
  required,
  className,
  layout = 'vertical'
}: ResponsiveRadioGroupProps) {
  const { isMobile } = useResponsive()

  const layoutClasses = {
    vertical: 'space-y-3',
    horizontal: isMobile ? 'space-y-3' : 'flex flex-wrap gap-6',
    grid: isMobile ? 'space-y-3' : 'grid grid-cols-2 gap-4'
  }

  return (
    <div className={cn(layoutClasses[layout], className)}>
      {options.map((option) => (
        <div key={option.value} className="flex items-start">
          <div className="flex items-center h-5">
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={(e) => onChange?.(e.target.value)}
              disabled={disabled}
              required={required}
              className={cn(
                'border-gray-300 dark:border-gray-600',
                'text-blue-600 focus:ring-blue-500',
                'disabled:cursor-not-allowed',
                isMobile ? 'h-5 w-5' : 'h-4 w-4',
                isMobile && 'touch-friendly'
              )}
            />
          </div>
          
          <div className="ml-3">
            <label className={cn(
              'font-medium text-gray-900 dark:text-white cursor-pointer',
              isMobile ? 'text-base' : 'text-sm'
            )}>
              {option.label}
            </label>
            
            {option.description && (
              <p className={cn(
                'text-gray-600 dark:text-gray-400',
                isMobile ? 'text-sm' : 'text-xs'
              )}>
                {option.description}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}