/**
 * OptimizedImage Component
 * 
 * A wrapper around Next.js Image component with sensible defaults
 * and additional features for optimal image loading performance.
 * 
 * Features:
 * - Automatic WebP conversion
 * - Responsive image sizing
 * - Lazy loading by default
 * - Blur placeholder support
 * - Error handling with fallback
 * - Accessibility built-in
 */

import Image, { ImageProps } from 'next/image';
import { useState } from 'react';
import { cn } from '@/lib/utils';

export interface OptimizedImageProps extends Omit<ImageProps, 'src' | 'alt'> {
  src: string;
  alt: string;
  fallbackSrc?: string;
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape' | 'auto';
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
  showPlaceholder?: boolean;
  containerClassName?: string;
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
 * // Responsive with fill
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

  const imageClasses = cn(
    'transition-opacity duration-300',
    isLoading && showPlaceholder ? 'opacity-0' : 'opacity-100',
    objectFit === 'contain' && 'object-contain',
    objectFit === 'cover' && 'object-cover',
    objectFit === 'fill' && 'object-fill',
    objectFit === 'none' && 'object-none',
    objectFit === 'scale-down' && 'object-scale-down',
    className
  );

  const containerClasses = cn(
    'relative overflow-hidden',
    aspectRatio && aspectRatioClasses[aspectRatio],
    containerClassName
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
 */
export function OptimizedAvatar({
  src,
  alt,
  size = 40,
  fallbackSrc = '/images/default-avatar.svg',
  className,
  ...props
}: Omit<OptimizedImageProps, 'width' | 'height' | 'aspectRatio'> & {
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
      className={cn('rounded-full', className)}
      {...props}
    />
  );
}

/**
 * Logo component optimized for brand logos
 */
export function OptimizedLogo({
  src,
  alt,
  width = 120,
  height = 40,
  priority = true,
  className,
  ...props
}: Omit<OptimizedImageProps, 'aspectRatio' | 'objectFit'>) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={width}
      height={height}
      objectFit="contain"
      priority={priority}
      className={className}
      {...props}
    />
  );
}

/**
 * Thumbnail component for image previews
 */
export function OptimizedThumbnail({
  src,
  alt,
  size = 80,
  aspectRatio = 'square',
  className,
  ...props
}: Omit<OptimizedImageProps, 'width' | 'height'> & {
  size?: number;
}) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      aspectRatio={aspectRatio}
      className={cn('rounded-lg', className)}
      {...props}
    />
  );
}
