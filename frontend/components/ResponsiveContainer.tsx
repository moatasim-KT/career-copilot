import { ReactNode, forwardRef } from 'react'
import { useResponsive, useResponsiveSpacing } from '@/hooks/useResponsive'
import { cn } from '@/utils/helpers'

interface ResponsiveContainerProps {
  children: ReactNode
  className?: string
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'responsive'
  center?: boolean
  as?: keyof JSX.IntrinsicElements
}

/**
 * Responsive container component that adapts to screen size
 */
export function ResponsiveContainer({ 
  children, 
  className, 
  maxWidth = 'xl', 
  padding = 'responsive',
  center = true,
  as = 'div',
  ...props 
}: ResponsiveContainerProps) {
  const { containerPadding } = useResponsiveSpacing()
  
  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-7xl',
    '2xl': 'max-w-none',
    full: 'max-w-full',
  }
  
  const paddingClasses = {
    none: '',
    sm: 'px-4',
    md: 'px-6',
    lg: 'px-8',
    responsive: containerPadding,
  }
  
  const Component = as as any
  
  return (
    <Component
      className={cn(
        'w-full',
        maxWidthClasses[maxWidth],
        paddingClasses[padding],
        center && 'mx-auto',
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
}



interface ResponsiveGridProps {
  children: ReactNode
  className?: string
  columns?: {
    mobile?: number
    tablet?: number
    desktop?: number
    largeDesktop?: number
  }
  gap?: 'sm' | 'md' | 'lg' | 'xl'
  minItemWidth?: string
}

/**
 * Responsive grid component with automatic column adjustment
 */
export function ResponsiveGrid({ 
  children, 
  className,
  columns = { mobile: 1, tablet: 2, desktop: 3, largeDesktop: 4 },
  gap = 'md',
  minItemWidth
}: ResponsiveGridProps) {
  const { isMobile, isTablet, isDesktop, isLargeDesktop } = useResponsive()
  
  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
    xl: 'gap-8',
  }
  
  let gridColumns = columns.mobile || 1
  if (isLargeDesktop && columns.largeDesktop) gridColumns = columns.largeDesktop
  else if (isDesktop && columns.desktop) gridColumns = columns.desktop
  else if (isTablet && columns.tablet) gridColumns = columns.tablet
  
  const gridStyle = minItemWidth 
    ? { gridTemplateColumns: `repeat(auto-fit, minmax(${minItemWidth}, 1fr))` }
    : { gridTemplateColumns: `repeat(${gridColumns}, 1fr)` }
  
  return (
    <div
      className={cn(
        'grid',
        gapClasses[gap],
        className
      )}
      style={gridStyle}
    >
      {children}
    </div>
  )
}

interface ResponsiveStackProps {
  children: ReactNode
  className?: string
  direction?: 'vertical' | 'horizontal' | 'responsive'
  spacing?: 'sm' | 'md' | 'lg' | 'xl'
  align?: 'start' | 'center' | 'end' | 'stretch'
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'
  wrap?: boolean
}

/**
 * Responsive stack component for flexible layouts
 */
export function ResponsiveStack({
  children,
  className,
  direction = 'responsive',
  spacing = 'md',
  align = 'start',
  justify = 'start',
  wrap = false
}: ResponsiveStackProps) {
  const { isMobile } = useResponsive()
  
  const spacingClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
    xl: 'gap-8',
  }
  
  const alignClasses = {
    start: 'items-start',
    center: 'items-center',
    end: 'items-end',
    stretch: 'items-stretch',
  }
  
  const justifyClasses = {
    start: 'justify-start',
    center: 'justify-center',
    end: 'justify-end',
    between: 'justify-between',
    around: 'justify-around',
    evenly: 'justify-evenly',
  }
  
  let flexDirection = 'flex-col'
  if (direction === 'horizontal') flexDirection = 'flex-row'
  else if (direction === 'responsive') flexDirection = isMobile ? 'flex-col' : 'flex-row'
  
  return (
    <div
      className={cn(
        'flex',
        flexDirection,
        spacingClasses[spacing],
        alignClasses[align],
        justifyClasses[justify],
        wrap && 'flex-wrap',
        className
      )}
    >
      {children}
    </div>
  )
}

interface ResponsiveShowProps {
  children: ReactNode
  above?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  below?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  only?: 'mobile' | 'tablet' | 'desktop' | 'largeDesktop'
}

/**
 * Component for conditionally showing content based on screen size
 */
export function ResponsiveShow({ children, above, below, only }: ResponsiveShowProps) {
  const { isMobile, isTablet, isDesktop, isLargeDesktop, breakpoint } = useResponsive()
  
  const breakpointOrder = ['xs', 'sm', 'md', 'lg', 'xl', '2xl']
  const currentIndex = breakpointOrder.indexOf(breakpoint)
  
  if (only) {
    const shouldShow = 
      (only === 'mobile' && isMobile) ||
      (only === 'tablet' && isTablet) ||
      (only === 'desktop' && isDesktop) ||
      (only === 'largeDesktop' && isLargeDesktop)
    
    return shouldShow ? <>{children}</> : null
  }
  
  if (above) {
    const aboveIndex = breakpointOrder.indexOf(above)
    if (currentIndex < aboveIndex) return null
  }
  
  if (below) {
    const belowIndex = breakpointOrder.indexOf(below)
    if (currentIndex > belowIndex) return null
  }
  
  return <>{children}</>
}

interface ResponsiveTextProps {
  children: ReactNode
  className?: string
  size?: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl'
  responsive?: boolean
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold'
  color?: 'primary' | 'secondary' | 'muted' | 'accent' | 'success' | 'warning' | 'error'
  as?: 'p' | 'span' | 'div' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
}

/**
 * Responsive text component with automatic size scaling
 */
export function ResponsiveText({
  children,
  className,
  size = 'base',
  responsive = true,
  weight = 'normal',
  color = 'primary',
  as: Component = 'p'
}: ResponsiveTextProps) {
  const { isMobile, isTablet } = useResponsive()
  
  const sizeClasses = {
    xs: responsive ? (isMobile ? 'text-xs' : isTablet ? 'text-sm' : 'text-base') : 'text-xs',
    sm: responsive ? (isMobile ? 'text-sm' : isTablet ? 'text-base' : 'text-lg') : 'text-sm',
    base: responsive ? (isMobile ? 'text-base' : isTablet ? 'text-lg' : 'text-xl') : 'text-base',
    lg: responsive ? (isMobile ? 'text-lg' : isTablet ? 'text-xl' : 'text-2xl') : 'text-lg',
    xl: responsive ? (isMobile ? 'text-xl' : isTablet ? 'text-2xl' : 'text-3xl') : 'text-xl',
    '2xl': responsive ? (isMobile ? 'text-2xl' : isTablet ? 'text-3xl' : 'text-4xl') : 'text-2xl',
    '3xl': responsive ? (isMobile ? 'text-3xl' : isTablet ? 'text-4xl' : 'text-5xl') : 'text-3xl',
    '4xl': responsive ? (isMobile ? 'text-4xl' : isTablet ? 'text-5xl' : 'text-6xl') : 'text-4xl',
    '5xl': responsive ? (isMobile ? 'text-5xl' : isTablet ? 'text-6xl' : 'text-7xl') : 'text-5xl',
    '6xl': responsive ? (isMobile ? 'text-6xl' : isTablet ? 'text-7xl' : 'text-8xl') : 'text-6xl',
  }
  
  const weightClasses = {
    light: 'font-light',
    normal: 'font-normal',
    medium: 'font-medium',
    semibold: 'font-semibold',
    bold: 'font-bold',
  }
  
  const colorClasses = {
    primary: 'text-gray-900 dark:text-white',
    secondary: 'text-gray-700 dark:text-gray-300',
    muted: 'text-gray-600 dark:text-gray-400',
    accent: 'text-blue-600 dark:text-blue-400',
    success: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    error: 'text-red-600 dark:text-red-400',
  }
  
  return (
    <Component
      className={cn(
        sizeClasses[size],
        weightClasses[weight],
        colorClasses[color],
        className
      )}
    >
      {children}
    </Component>
  )
}