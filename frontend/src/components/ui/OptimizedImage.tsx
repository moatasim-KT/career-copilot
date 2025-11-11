/**
 * OptimizedImage Component
 * 
 * A wrapper around Next.js Image component with sensible defaults
 * and additional features for optimal image loading performance.
 * 
 * Features:
 * - Automatic WebP/AVIF conversion
 * - Responsive image sizing with smart defaults
 * - Lazy loading by default
 * - Blur placeholder support
 * - Error handling with fallback
 * - Accessibility built-in
 * 
 * Responsive Sizes:
 * The component automatically provides responsive sizes based on usage context.
 * You can override with custom sizes prop for specific layouts.
 */

import Image, { ImageProps } from 'next/image';
import { useState } from 'react';
import { cn } from '@/lib/utils';

/**
 * Responsive sizes presets for common layouts
 * These tell the browser which image size to load based on viewport width
 */
export const RESPONSIVE_SIZES = {
  // Full width on all screens
  full: '100vw',
  
  // Full width on mobile, half on tablet, third on desktop
  hero: '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
  
  // Full width on mobile, 50% on larger screens
  card: '(max-width: 768px) 100vw, 50vw',
  
  // Full width on mobile, 33% on tablet, 25% on desktop
  grid: '(max-width: 640px) 100vw, (max-width: 1024px) 33vw, 25vw',
  
  // Fixed small sizes for thumbnails and avatars
  thumbnail: '(max-width: 640px) 96px, 128px',
  avatar: '(max-width: 640px) 40px, 48px',
  
  // Banner images
  banner: '(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1200px',
  
  // Sidebar images
  sidebar: '(max-width: 1024px) 100vw, 300px',
  
  // Content images (in article/blog content)
  content: '(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 800px',
} as const;

/**
 * Get responsive sizes based on image context
 */
export function getResponsiveSizes(
  context: keyof typeof RESPONSIVE_SIZES | 'auto' = 'auto',
  customSizes?: string,
): string | undefined {
  if (customSizes) return customSizes;
  if (context === 'auto') return undefined;
  return RESPONSIVE_SIZES[context];
}

export interface OptimizedImageProps extends Omit<ImageProps, 'src' | 'alt'> {
  src: string;
  alt: string;
  fallbackSrc?: string;
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape' | 'auto';
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
  showPlaceholder?: boolean;
  containerClassName?: string;
  /**
   * Responsive sizes context - automatically sets appropriate sizes prop
   * Use 'auto' to let Next.js decide, or specify a preset for common layouts
   */
  responsiveContext?: keyof typeof RESPONSIVE_SIZES | 'auto';
}

const aspectRatioClasses = {
  square: 'aspect-square',
  video: 'aspect-video',
  portrait: 'aspect-[3/4]',
  landscape: 'aspect-[4/3]',
  auto: '',
};

/**
 * OptimizedImage component with automatic optimization and error handling
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <OptimizedImage
 *   src="/images/profile.jpg"
 *   alt="User profile"
 *   width={200}
 *   height={200}
 * />
 * 
 * // With aspect ratio and blur placeholder
 * <OptimizedImage
 *   src="/images/hero.jpg"
 *   alt="Hero image"
 *   width={1200}
 *   height={600}
 *   aspectRatio="video"
 *   placeholder="blur"
 *   blurDataURL="data:image/jpeg;base64,..."
 * />
 * 
 * // With fallback
 * <OptimizedImage
 *   src="/images/user-avatar.jpg"
 *   alt="User avatar"
 *   width={100}
 *   height={100}
 *   fallbackSrc="/images/default-avatar.png"
 *   aspectRatio="square"
 * />
 * 
 * // Responsive with fill and automatic sizes
 * <OptimizedImage
 *   src="/images/banner.jpg"
 *   alt="Banner"
 *   fill
 *   objectFit="cover"
 *   responsiveContext="hero"
 * />
 * 
 * // Responsive with custom sizes
 * <OptimizedImage
 *   src="/images/banner.jpg"
 *   alt="Banner"
 *   fill
 *   objectFit="cover"
 *   sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
 * />
 * ```
 */
export function OptimizedImage({
  src,
  alt,
  fallbackSrc = '/images/placeholder.svg',
  aspectRatio = 'auto',
  objectFit = 'cover',
  showPlaceholder = true,
  containerClassName,
  className,
  priority = false,
  loading = 'lazy',
  quality = 85,
  responsiveContext = 'auto',
  sizes: customSizes,
  ...props
}: OptimizedImageProps) {
  const [imgSrc, setImgSrc] = useState(src);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const handleError = () => {
    setHasError(true);
    setImgSrc(fallbackSrc);
  };

  const handleLoad = () => {
    setIsLoading(false);
  };

  // Get responsive sizes based on context
  const responsiveSizes = getResponsiveSizes(responsiveContext, customSizes);

  const imageClasses = cn(
    'transition-opacity duration-300',
    isLoading && showPlaceholder ? 'opacity-0' : 'opacity-100',
    objectFit === 'contain' && 'object-contain',
    objectFit === 'cover' && 'object-cover',
    objectFit === 'fill' && 'object-fill',
    objectFit === 'none' && 'object-none',
    objectFit === 'scale-down' && 'object-scale-down',
    className,
  );

  const containerClasses = cn(
    'relative overflow-hidden',
    aspectRatio && aspectRatioClasses[aspectRatio],
    containerClassName,
  );

  // If using fill prop, wrap in container
  if (props.fill) {
    return (
      <div className={containerClasses}>
        {isLoading && showPlaceholder && (
          <div className="absolute inset-0 bg-neutral-200 dark:bg-neutral-800 animate-pulse" />
        )}
        <Image
          src={imgSrc}
          alt={alt}
          fill
          className={imageClasses}
          onError={handleError}
          onLoad={handleLoad}
          priority={priority}
          loading={loading}
          quality={quality}
          sizes={responsiveSizes}
          {...props}
        />
        {hasError && (
          <div className="absolute inset-0 flex items-center justify-center bg-neutral-100 dark:bg-neutral-900">
            <span className="text-sm text-neutral-500">Image unavailable</span>
          </div>
        )}
      </div>
    );
  }

  // Standard usage with width and height
  return (
    <div className={cn('relative', containerClassName)}>
      {isLoading && showPlaceholder && (
        <div
          className="absolute inset-0 bg-neutral-200 dark:bg-neutral-800 animate-pulse rounded"
          style={{
            width: props.width,
            height: props.height,
          }}
        />
      )}
      <Image
        src={imgSrc}
        alt={alt}
        className={imageClasses}
        onError={handleError}
        onLoad={handleLoad}
        priority={priority}
        loading={loading}
        quality={quality}
        sizes={responsiveSizes}
        {...props}
      />
      {hasError && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-neutral-100 dark:bg-neutral-900 rounded"
          style={{
            width: props.width,
            height: props.height,
          }}
        >
          <span className="text-sm text-neutral-500">Image unavailable</span>
        </div>
      )}
    </div>
  );
}

/**
 * Avatar component optimized for profile images
 * 
 * @example
 * ```tsx
 * <OptimizedAvatar
 *   src="/images/user.jpg"
 *   alt="John Doe"
 *   size={48}
 * />
 * ```
 */
export function OptimizedAvatar({
  src,
  alt,
  size = 40,
  fallbackSrc = '/images/default-avatar.svg',
  className,
  ...props
}: Omit<OptimizedImageProps, 'width' | 'height' | 'aspectRatio' | 'responsiveContext'> & {
  size?: number;
}) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      aspectRatio="square"
      fallbackSrc={fallbackSrc}
      responsiveContext="avatar"
      className={cn('rounded-full', className)}
      {...props}
    />
  );
}

/**
 * Logo component optimized for brand logos
 * 
 * @example
 * ```tsx
 * <OptimizedLogo
 *   src="/images/logo.svg"
 *   alt="Company Name"
 *   width={150}
 *   height={50}
 * />
 * ```
 */
export function OptimizedLogo({
  src,
  alt,
  width = 120,
  height = 40,
  priority = true,
  className,
  ...props
}: Omit<OptimizedImageProps, 'aspectRatio' | 'objectFit' | 'responsiveContext'>) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={width}
      height={height}
      objectFit="contain"
      priority={priority}
      responsiveContext="auto"
      className={className}
      {...props}
    />
  );
}

/**
 * Thumbnail component for image previews
 * 
 * @example
 * ```tsx
 * <OptimizedThumbnail
 *   src="/images/document.jpg"
 *   alt="Document preview"
 *   size={120}
 *   aspectRatio="video"
 * />
 * ```
 */
export function OptimizedThumbnail({
  src,
  alt,
  size = 80,
  aspectRatio = 'square',
  className,
  ...props
}: Omit<OptimizedImageProps, 'width' | 'height' | 'responsiveContext'> & {
  size?: number;
}) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      aspectRatio={aspectRatio}
      responsiveContext="thumbnail"
      className={cn('rounded-lg', className)}
      {...props}
    />
  );
}
