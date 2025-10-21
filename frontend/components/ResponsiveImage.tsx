import { useState, useRef, useEffect } from 'react'
import Image from 'next/image'
import { useProgressiveImage, useIntersectionObserver } from '@/utils/progressive-loading'
import { useResponsive } from '@/hooks/useResponsive'
import { cn } from '@/utils/helpers'

interface ResponsiveImageProps {
  src: string
  alt: string
  className?: string
  placeholder?: string
  blurDataURL?: string
  priority?: boolean
  sizes?: string
  fill?: boolean
  width?: number
  height?: number
  quality?: number
  loading?: 'lazy' | 'eager'
  onLoad?: () => void
  onError?: () => void
  responsive?: {
    mobile?: { width: number; height: number }
    tablet?: { width: number; height: number }
    desktop?: { width: number; height: number }
  }
}

/**
 * Responsive image component with progressive loading
 */
export function ResponsiveImage({
  src,
  alt,
  className,
  placeholder,
  blurDataURL,
  priority = false,
  sizes,
  fill = false,
  width,
  height,
  quality = 75,
  loading = 'lazy',
  onLoad,
  onError,
  responsive
}: ResponsiveImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const { isMobile, isTablet, isDesktop } = useResponsive()
  const [ref, isVisible] = useIntersectionObserver({ threshold: 0.1 })

  // Get responsive dimensions
  const getDimensions = () => {
    if (responsive) {
      if (isMobile && responsive.mobile) return responsive.mobile
      if (isTablet && responsive.tablet) return responsive.tablet
      if (isDesktop && responsive.desktop) return responsive.desktop
    }
    return { width, height }
  }

  const dimensions = getDimensions()

  // Progressive image loading
  const { src: progressiveSrc, loading: progressiveLoading, error: progressiveError } = 
    useProgressiveImage(src, placeholder)

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  // Don't render until visible (unless priority)
  if (!priority && !isVisible) {
    return (
      <div 
        ref={ref}
        className={cn(
          'bg-gray-200 dark:bg-gray-700 animate-pulse',
          className
        )}
        style={{ 
          width: dimensions.width, 
          height: dimensions.height 
        }}
      />
    )
  }

  // Error state
  if (hasError || progressiveError) {
    return (
      <div 
        className={cn(
          'bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-500 dark:text-gray-400',
          className
        )}
        style={{ 
          width: dimensions.width, 
          height: dimensions.height 
        }}
      >
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
    )
  }

  return (
    <div 
      className={cn(
        'relative overflow-hidden',
        className
      )}
      style={!fill ? { 
        width: dimensions.width, 
        height: dimensions.height 
      } : undefined}
    >
      {/* Loading placeholder */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse" />
      )}

      <Image
        src={progressiveSrc || src}
        alt={alt}
        fill={fill}
        width={!fill ? dimensions.width : undefined}
        height={!fill ? dimensions.height : undefined}
        sizes={sizes || (responsive ? 
          '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw' : 
          undefined
        )}
        quality={quality}
        priority={priority}
        loading={loading}
        placeholder={blurDataURL ? 'blur' : 'empty'}
        blurDataURL={blurDataURL}
        onLoad={handleLoad}
        onError={handleError}
        className={cn(
          'transition-opacity duration-300',
          isLoaded ? 'opacity-100' : 'opacity-0',
          fill ? 'object-cover' : ''
        )}
      />
    </div>
  )
}

interface ResponsiveAvatarProps {
  src?: string
  alt: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  className?: string
  fallback?: string
  priority?: boolean
}

/**
 * Responsive avatar component
 */
export function ResponsiveAvatar({
  src,
  alt,
  size = 'md',
  className,
  fallback,
  priority = false
}: ResponsiveAvatarProps) {
  const { isMobile } = useResponsive()
  
  const sizeClasses = {
    xs: isMobile ? 'w-6 h-6' : 'w-8 h-8',
    sm: isMobile ? 'w-8 h-8' : 'w-10 h-10',
    md: isMobile ? 'w-10 h-10' : 'w-12 h-12',
    lg: isMobile ? 'w-12 h-12' : 'w-16 h-16',
    xl: isMobile ? 'w-16 h-16' : 'w-20 h-20',
    '2xl': isMobile ? 'w-20 h-20' : 'w-24 h-24',
  }

  const textSizeClasses = {
    xs: isMobile ? 'text-xs' : 'text-sm',
    sm: isMobile ? 'text-sm' : 'text-base',
    md: isMobile ? 'text-base' : 'text-lg',
    lg: isMobile ? 'text-lg' : 'text-xl',
    xl: isMobile ? 'text-xl' : 'text-2xl',
    '2xl': isMobile ? 'text-2xl' : 'text-3xl',
  }

  if (!src) {
    return (
      <div 
        className={cn(
          'rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 font-medium',
          sizeClasses[size],
          textSizeClasses[size],
          className
        )}
      >
        {fallback || alt.charAt(0).toUpperCase()}
      </div>
    )
  }

  return (
    <div className={cn('rounded-full overflow-hidden', sizeClasses[size], className)}>
      <ResponsiveImage
        src={src}
        alt={alt}
        fill
        priority={priority}
        className="rounded-full"
      />
    </div>
  )
}

interface ResponsiveIconProps {
  icon: React.ComponentType<{ className?: string }>
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

/**
 * Responsive icon component that scales with screen size
 */
export function ResponsiveIcon({ 
  icon: Icon, 
  size = 'md', 
  className 
}: ResponsiveIconProps) {
  const { isMobile } = useResponsive()
  
  const sizeClasses = {
    xs: isMobile ? 'w-3 h-3' : 'w-4 h-4',
    sm: isMobile ? 'w-4 h-4' : 'w-5 h-5',
    md: isMobile ? 'w-5 h-5' : 'w-6 h-6',
    lg: isMobile ? 'w-6 h-6' : 'w-8 h-8',
    xl: isMobile ? 'w-8 h-8' : 'w-10 h-10',
  }

  return <Icon className={cn(sizeClasses[size], className)} />
}

interface LazyImageProps extends ResponsiveImageProps {
  threshold?: number
  rootMargin?: string
}

/**
 * Lazy loading image component
 */
export function LazyImage({
  threshold = 0.1,
  rootMargin = '50px',
  ...props
}: LazyImageProps) {
  const [ref, isVisible] = useIntersectionObserver({
    threshold,
    rootMargin,
  })

  if (!isVisible) {
    return (
      <div 
        ref={ref}
        className={cn(
          'bg-gray-200 dark:bg-gray-700 animate-pulse',
          props.className
        )}
        style={{ 
          width: props.width, 
          height: props.height 
        }}
      />
    )
  }

  return <ResponsiveImage {...props} />
}