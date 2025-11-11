# Image Optimization Guide

This guide covers best practices for using images in the Career Copilot frontend application.

## Overview

All images in this application should use Next.js Image component for automatic optimization. We've created wrapper components that provide additional features and sensible defaults.

## Components

### OptimizedImage

The main component for displaying images with automatic optimization.

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

<OptimizedImage
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority
/>
```

**Props:**
- `src` (required): Image source URL
- `alt` (required): Alternative text for accessibility
- `width` & `height` (required unless using `fill`): Image dimensions
- `fill`: Fill the parent container (responsive)
- `priority`: Load image with high priority (above the fold)
- `loading`: 'lazy' (default) or 'eager'
- `quality`: 1-100, default 85
- `aspectRatio`: 'square' | 'video' | 'portrait' | 'landscape' | 'auto'
- `objectFit`: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down'
- `fallbackSrc`: Fallback image if main image fails
- `showPlaceholder`: Show loading placeholder (default true)

### OptimizedAvatar

Specialized component for user avatars.

```tsx
import { OptimizedAvatar } from '@/components/ui/OptimizedImage';

<OptimizedAvatar
  src="/images/user-avatar.jpg"
  alt="John Doe"
  size={40}
/>
```

**Props:**
- `src` (required): Avatar image URL
- `alt` (required): User name or description
- `size`: Avatar size in pixels (default 40)
- `fallbackSrc`: Fallback avatar (default: default-avatar.svg)

### OptimizedLogo

Specialized component for brand logos.

```tsx
import { OptimizedLogo } from '@/components/ui/OptimizedImage';

<OptimizedLogo
  src="/images/company-logo.png"
  alt="Company Name"
  width={120}
  height={40}
  priority
/>
```

**Props:**
- `src` (required): Logo image URL
- `alt` (required): Company or brand name
- `width`: Logo width (default 120)
- `height`: Logo height (default 40)
- `priority`: Always true by default for logos

### OptimizedThumbnail

Specialized component for image thumbnails.

```tsx
import { OptimizedThumbnail } from '@/components/ui/OptimizedImage';

<OptimizedThumbnail
  src="/images/document-preview.jpg"
  alt="Document preview"
  size={80}
  aspectRatio="square"
/>
```

**Props:**
- `src` (required): Thumbnail image URL
- `alt` (required): Image description
- `size`: Thumbnail size in pixels (default 80)
- `aspectRatio`: Aspect ratio (default 'square')

## Usage Examples

### Basic Image

```tsx
<OptimizedImage
  src="/images/profile.jpg"
  alt="User profile"
  width={200}
  height={200}
/>
```

### Responsive Image (Fill Container)

```tsx
<div className="relative w-full h-64">
  <OptimizedImage
    src="/images/banner.jpg"
    alt="Banner"
    fill
    objectFit="cover"
    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
  />
</div>
```

### Image with Blur Placeholder

```tsx
<OptimizedImage
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRg..."
/>
```

### Priority Image (Above the Fold)

```tsx
<OptimizedImage
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority
/>
```

### External Image

```tsx
<OptimizedImage
  src="https://images.unsplash.com/photo-123456"
  alt="External image"
  width={800}
  height={600}
/>
```

### Image with Fallback

```tsx
<OptimizedImage
  src="/images/user-photo.jpg"
  alt="User photo"
  width={200}
  height={200}
  fallbackSrc="/images/default-avatar.svg"
/>
```

## Configuration

Image optimization is configured in `next.config.js`:

```javascript
images: {
  formats: ['image/webp', 'image/avif'],
  deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  quality: 85,
  remotePatterns: [
    // Allowed external domains
  ],
}
```

## Best Practices

### 1. Always Provide Alt Text

```tsx
// ✅ Good
<OptimizedImage src="/image.jpg" alt="Description of image" width={200} height={200} />

// ❌ Bad
<OptimizedImage src="/image.jpg" alt="" width={200} height={200} />
```

### 2. Use Appropriate Dimensions

```tsx
// ✅ Good - Exact dimensions
<OptimizedImage src="/image.jpg" alt="..." width={800} height={600} />

// ❌ Bad - Oversized
<OptimizedImage src="/image.jpg" alt="..." width={4000} height={3000} />
```

### 3. Use Priority for Above-the-Fold Images

```tsx
// ✅ Good - Hero image loads immediately
<OptimizedImage src="/hero.jpg" alt="..." width={1200} height={600} priority />

// ❌ Bad - Hero image lazy loads
<OptimizedImage src="/hero.jpg" alt="..." width={1200} height={600} />
```

### 4. Use Responsive Sizes

```tsx
// ✅ Good - Responsive sizing
<OptimizedImage
  src="/image.jpg"
  alt="..."
  fill
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
/>

// ❌ Bad - No sizes specified with fill
<OptimizedImage src="/image.jpg" alt="..." fill />
```

### 5. Optimize Source Images

- Compress images before uploading
- Target < 100KB for most images
- Use appropriate formats:
  - JPEG for photos
  - PNG for graphics with transparency
  - SVG for icons and logos
  - WebP for modern browsers (automatic)

### 6. Use Aspect Ratios

```tsx
// ✅ Good - Prevents layout shift
<OptimizedImage
  src="/image.jpg"
  alt="..."
  width={800}
  height={600}
  aspectRatio="video"
/>

// ❌ Bad - May cause layout shift
<OptimizedImage src="/image.jpg" alt="..." width={800} height={600} />
```

### 7. Provide Fallbacks

```tsx
// ✅ Good - Graceful degradation
<OptimizedImage
  src="/user-avatar.jpg"
  alt="User"
  width={100}
  height={100}
  fallbackSrc="/default-avatar.svg"
/>
```

## Image Formats

### Automatic Format Conversion

Next.js automatically serves images in WebP or AVIF format when supported by the browser, falling back to the original format.

### Supported Formats

- **JPEG**: Photos, complex images
- **PNG**: Graphics with transparency
- **WebP**: Modern format, smaller file sizes
- **AVIF**: Next-gen format, best compression
- **SVG**: Vector graphics, icons, logos
- **GIF**: Animations (use sparingly)

## Performance Optimization

### Lazy Loading

By default, all images are lazy-loaded except those marked with `priority`.

```tsx
// Lazy loaded (default)
<OptimizedImage src="/image.jpg" alt="..." width={200} height={200} />

// Eager loaded
<OptimizedImage src="/image.jpg" alt="..." width={200} height={200} priority />
```

### Blur Placeholders

Generate blur placeholders for better perceived performance:

```bash
# Using plaiceholder
npm install plaiceholder sharp
```

```tsx
import { getPlaiceholder } from 'plaiceholder';

const { base64 } = await getPlaiceholder('/path/to/image.jpg');

<OptimizedImage
  src="/image.jpg"
  alt="..."
  width={800}
  height={600}
  placeholder="blur"
  blurDataURL={base64}
/>
```

### Image Sizing

Use the `sizes` prop to tell the browser which image size to load:

```tsx
<OptimizedImage
  src="/image.jpg"
  alt="..."
  fill
  sizes="(max-width: 640px) 100vw,
         (max-width: 1024px) 50vw,
         33vw"
/>
```

## Accessibility

### Alt Text Guidelines

- **Descriptive**: Describe what's in the image
- **Concise**: Keep it under 125 characters
- **Contextual**: Consider the surrounding content
- **Decorative**: Use empty alt="" for decorative images

```tsx
// ✅ Good alt text
<OptimizedImage
  src="/chart.jpg"
  alt="Bar chart showing 50% increase in applications over 6 months"
  width={600}
  height={400}
/>

// ❌ Bad alt text
<OptimizedImage
  src="/chart.jpg"
  alt="chart"
  width={600}
  height={400}
/>
```

### ARIA Labels

For complex images, consider using `aria-describedby`:

```tsx
<div>
  <OptimizedImage
    src="/complex-chart.jpg"
    alt="Application trends chart"
    width={800}
    height={600}
    aria-describedby="chart-description"
  />
  <div id="chart-description" className="sr-only">
    Detailed description of the chart data...
  </div>
</div>
```

## Common Patterns

### Hero Images

```tsx
<div className="relative w-full h-[500px]">
  <OptimizedImage
    src="/hero.jpg"
    alt="Career opportunities"
    fill
    objectFit="cover"
    priority
    sizes="100vw"
  />
  <div className="absolute inset-0 bg-black/40">
    <h1 className="text-white">Welcome</h1>
  </div>
</div>
```

### Avatar Grid

```tsx
<div className="flex gap-2">
  {users.map(user => (
    <OptimizedAvatar
      key={user.id}
      src={user.avatar}
      alt={user.name}
      size={40}
    />
  ))}
</div>
```

### Image Gallery

```tsx
<div className="grid grid-cols-3 gap-4">
  {images.map(image => (
    <OptimizedThumbnail
      key={image.id}
      src={image.url}
      alt={image.title}
      size={200}
      aspectRatio="square"
    />
  ))}
</div>
```

### Card with Image

```tsx
<div className="card">
  <OptimizedImage
    src="/card-image.jpg"
    alt="Card image"
    width={400}
    height={200}
    aspectRatio="video"
  />
  <div className="p-4">
    <h3>Card Title</h3>
    <p>Card content...</p>
  </div>
</div>
```

## Troubleshooting

### Image Not Loading

1. Check the image path is correct
2. Verify the image exists in `public/` directory
3. Check console for errors
4. Verify external domains are in `remotePatterns`

### Layout Shift

1. Always provide `width` and `height`
2. Use `aspectRatio` prop
3. Use `fill` with proper container sizing

### Slow Loading

1. Compress source images
2. Use appropriate image sizes
3. Enable priority for above-the-fold images
4. Use blur placeholders

### External Images Not Working

Add the domain to `remotePatterns` in `next.config.js`:

```javascript
images: {
  remotePatterns: [
    {
      protocol: 'https',
      hostname: 'example.com',
    },
  ],
}
```

## Migration Checklist

When adding images to the application:

- [ ] Use `OptimizedImage` or specialized components
- [ ] Provide descriptive alt text
- [ ] Specify width and height (or use fill)
- [ ] Use priority for above-the-fold images
- [ ] Compress source images < 100KB
- [ ] Test on different screen sizes
- [ ] Verify accessibility with screen reader
- [ ] Check performance with Lighthouse

## Resources

- [Next.js Image Documentation](https://nextjs.org/docs/app/api-reference/components/image)
- [Web.dev: Optimize Images](https://web.dev/fast/#optimize-your-images)
- [WebAIM: Alternative Text](https://webaim.org/techniques/alttext/)
- [Image Compression Tools](https://tinypng.com/)

## Support

For questions or issues with image optimization:
1. Check this documentation
2. Review Next.js Image documentation
3. Check browser console for errors
4. Consult with the team lead
