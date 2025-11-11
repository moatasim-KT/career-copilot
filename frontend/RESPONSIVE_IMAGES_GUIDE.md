# Responsive Images Guide

This guide explains how to use responsive images effectively in the Career Copilot application.

## Overview

Responsive images ensure that users download appropriately sized images for their device, improving performance and user experience. Our `OptimizedImage` component provides automatic responsive sizing through preset contexts and custom configurations.

## Why Responsive Images Matter

### Performance Benefits
- **Faster Load Times**: Smaller images load faster on mobile devices
- **Reduced Bandwidth**: Users on mobile data plans consume less data
- **Better Core Web Vitals**: Improved LCP (Largest Contentful Paint) scores

### User Experience
- **Appropriate Quality**: High-res images on desktop, optimized images on mobile
- **Faster Perceived Performance**: Pages feel snappier with optimized images
- **Better Mobile Experience**: Reduced data usage and faster loading

## Configuration

### Next.js Image Configuration

Our `next.config.js` includes optimized settings for responsive images:

```javascript
images: {
  // Automatic format conversion to WebP/AVIF
  formats: ['image/webp', 'image/avif'],
  
  // Device sizes for responsive breakpoints
  deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  
  // Image sizes for smaller images (icons, avatars, thumbnails)
  imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  
  // Default quality (1-100)
  quality: 85,
}
```

### How It Works

When you use the `sizes` prop, Next.js:
1. Generates multiple image sizes based on `deviceSizes` and `imageSizes`
2. Creates a `srcset` with all available sizes
3. Browser selects the most appropriate size based on viewport and `sizes` prop
4. Automatically serves WebP/AVIF when supported

## Using Responsive Contexts

### Available Presets

```typescript
RESPONSIVE_SIZES = {
  // Full width on all screens
  full: '100vw',
  
  // Full width on mobile, half on tablet, third on desktop
  hero: '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
  
  // Full width on mobile, 50% on larger screens
  card: '(max-width: 768px) 100vw, 50vw',
  
  // Full width on mobile, 33% on tablet, 25% on desktop
  grid: '(max-width: 640px) 100vw, (max-width: 1024px) 33vw, 25vw',
  
  // Fixed small sizes for thumbnails
  thumbnail: '(max-width: 640px) 96px, 128px',
  
  // Fixed small sizes for avatars
  avatar: '(max-width: 640px) 40px, 48px',
  
  // Banner images
  banner: '(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1200px',
  
  // Sidebar images
  sidebar: '(max-width: 1024px) 100vw, 300px',
  
  // Content images (in articles)
  content: '(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 800px',
}
```

### Basic Usage

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

// Using a preset context
<OptimizedImage
  src="/images/hero.jpg"
  alt="Hero image"
  fill
  responsiveContext="hero"
/>

// Custom sizes
<OptimizedImage
  src="/images/banner.jpg"
  alt="Banner"
  fill
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

## Common Patterns

### Hero Images

```tsx
<div className="relative w-full h-[500px]">
  <OptimizedImage
    src="/images/hero.jpg"
    alt="Welcome to Career Copilot"
    fill
    objectFit="cover"
    responsiveContext="hero"
    priority
  />
</div>
```

**Sizes Applied**: `(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw`

**Result**:
- Mobile (≤640px): Full width image
- Tablet (641-1024px): Half width image
- Desktop (>1024px): One-third width image

### Card Images

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  {items.map(item => (
    <div key={item.id} className="card">
      <div className="relative w-full h-48">
        <OptimizedImage
          src={item.image}
          alt={item.title}
          fill
          objectFit="cover"
          responsiveContext="card"
        />
      </div>
      <div className="p-4">
        <h3>{item.title}</h3>
      </div>
    </div>
  ))}
</div>
```

**Sizes Applied**: `(max-width: 768px) 100vw, 50vw`

**Result**:
- Mobile: Full width (1 column)
- Desktop: Half width (2 columns)

### Grid Images

```tsx
<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
  {images.map(image => (
    <div key={image.id} className="relative aspect-square">
      <OptimizedImage
        src={image.url}
        alt={image.title}
        fill
        objectFit="cover"
        responsiveContext="grid"
      />
    </div>
  ))}
</div>
```

**Sizes Applied**: `(max-width: 640px) 100vw, (max-width: 1024px) 33vw, 25vw`

**Result**:
- Mobile (≤640px): 2 columns, 50% width each
- Tablet (641-1024px): 3 columns, 33% width each
- Desktop (>1024px): 4 columns, 25% width each

### Banner Images

```tsx
<div className="relative w-full h-64">
  <OptimizedImage
    src="/images/banner.jpg"
    alt="Promotional banner"
    fill
    objectFit="cover"
    responsiveContext="banner"
  />
</div>
```

**Sizes Applied**: `(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1200px`

**Result**:
- Mobile: Full width
- Tablet: 80% of viewport width
- Desktop: Fixed 1200px width

### Content Images

```tsx
<article className="prose">
  <h1>Article Title</h1>
  <p>Introduction text...</p>
  
  <div className="relative w-full h-96 my-8">
    <OptimizedImage
      src="/images/article-image.jpg"
      alt="Article illustration"
      fill
      objectFit="cover"
      responsiveContext="content"
    />
  </div>
  
  <p>More content...</p>
</article>
```

**Sizes Applied**: `(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 800px`

**Result**:
- Mobile: Full width
- Tablet: 80% of viewport width
- Desktop: Fixed 800px width (typical article width)

### Avatars

```tsx
import { OptimizedAvatar } from '@/components/ui/OptimizedImage';

<OptimizedAvatar
  src={user.avatar}
  alt={user.name}
  size={48}
/>
```

**Sizes Applied**: `(max-width: 640px) 40px, 48px`

**Result**: Automatically uses appropriate size preset for avatars

### Thumbnails

```tsx
import { OptimizedThumbnail } from '@/components/ui/OptimizedImage';

<OptimizedThumbnail
  src={document.preview}
  alt={document.title}
  size={120}
/>
```

**Sizes Applied**: `(max-width: 640px) 96px, 128px`

**Result**: Automatically uses appropriate size preset for thumbnails

## Custom Responsive Sizes

### Understanding the Sizes Syntax

The `sizes` prop uses CSS media queries to tell the browser which image size to load:

```tsx
sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
```

This means:
1. **If viewport ≤ 768px**: Load image at 100% of viewport width
2. **Else if viewport ≤ 1200px**: Load image at 50% of viewport width
3. **Else**: Load image at 33% of viewport width

### Creating Custom Sizes

```tsx
// Sidebar image that's full width on mobile, fixed 300px on desktop
<OptimizedImage
  src="/images/sidebar.jpg"
  alt="Sidebar image"
  fill
  sizes="(max-width: 1024px) 100vw, 300px"
/>

// Image in a 3-column grid on desktop, 2-column on tablet, 1-column on mobile
<OptimizedImage
  src="/images/product.jpg"
  alt="Product"
  fill
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
/>

// Fixed width image that doesn't change
<OptimizedImage
  src="/images/icon.jpg"
  alt="Icon"
  fill
  sizes="64px"
/>
```

### Complex Layouts

For complex responsive layouts, calculate the actual image width:

```tsx
// Container is 90% of viewport on mobile, 80% on tablet, 1200px max on desktop
// Image takes 50% of container width
<OptimizedImage
  src="/images/complex.jpg"
  alt="Complex layout"
  fill
  sizes="(max-width: 640px) 45vw, (max-width: 1024px) 40vw, 600px"
/>
```

## Best Practices

### 1. Always Use Sizes with Fill

```tsx
// ✅ Good - Provides sizes for responsive loading
<OptimizedImage
  src="/image.jpg"
  alt="..."
  fill
  sizes="(max-width: 768px) 100vw, 50vw"
/>

// ❌ Bad - Browser doesn't know which size to load
<OptimizedImage
  src="/image.jpg"
  alt="..."
  fill
/>
```

### 2. Match Sizes to Layout

```tsx
// ✅ Good - Sizes match actual layout
<div className="w-full md:w-1/2">
  <OptimizedImage
    src="/image.jpg"
    alt="..."
    fill
    sizes="(max-width: 768px) 100vw, 50vw"
  />
</div>

// ❌ Bad - Sizes don't match layout
<div className="w-full md:w-1/2">
  <OptimizedImage
    src="/image.jpg"
    alt="..."
    fill
    sizes="100vw"  // Will load full-width image even on desktop
  />
</div>
```

### 3. Use Presets When Possible

```tsx
// ✅ Good - Uses preset for consistency
<OptimizedImage
  src="/image.jpg"
  alt="..."
  fill
  responsiveContext="card"
/>

// ❌ Less ideal - Manual sizes that might not match other cards
<OptimizedImage
  src="/image.jpg"
  alt="..."
  fill
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

### 4. Consider Container Constraints

```tsx
// ✅ Good - Accounts for max-width container
<div className="max-w-4xl mx-auto">
  <OptimizedImage
    src="/image.jpg"
    alt="..."
    fill
    sizes="(max-width: 768px) 100vw, (max-width: 1280px) 80vw, 1024px"
  />
</div>

// ❌ Bad - Might load unnecessarily large images
<div className="max-w-4xl mx-auto">
  <OptimizedImage
    src="/image.jpg"
    alt="..."
    fill
    sizes="100vw"
  />
</div>
```

### 5. Use Priority for Above-the-Fold Images

```tsx
// ✅ Good - Hero image loads immediately
<OptimizedImage
  src="/hero.jpg"
  alt="..."
  fill
  responsiveContext="hero"
  priority
/>
```

## Testing Responsive Images

### 1. Chrome DevTools

1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "Img"
4. Resize viewport
5. Reload page
6. Check which image sizes are loaded

### 2. Verify Sizes

Check the `srcset` attribute in the rendered HTML:

```html
<img
  srcset="
    /_next/image?url=/image.jpg&w=640&q=85 640w,
    /_next/image?url=/image.jpg&w=750&q=85 750w,
    /_next/image?url=/image.jpg&w=828&q=85 828w,
    ...
  "
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

### 3. Test on Real Devices

- Test on actual mobile devices
- Check network usage
- Verify image quality
- Measure load times

### 4. Lighthouse Audit

Run Lighthouse to check:
- Properly sized images
- Next-gen formats (WebP/AVIF)
- Lazy loading
- LCP performance

## Performance Metrics

### Expected Results

With proper responsive images:

- **Mobile (3G)**: Images load in < 2s
- **Desktop (Cable)**: Images load in < 1s
- **Data Savings**: 50-70% reduction on mobile
- **LCP**: < 2.5s for hero images

### Monitoring

Track these metrics:
- Image load times by device type
- Data transfer by image
- LCP scores
- User-reported performance issues

## Troubleshooting

### Images Too Large on Mobile

**Problem**: Mobile users downloading desktop-sized images

**Solution**: Check sizes prop matches actual layout
```tsx
// Before
sizes="100vw"

// After
sizes="(max-width: 768px) 100vw, 50vw"
```

### Images Too Small on Desktop

**Problem**: Desktop users seeing low-quality images

**Solution**: Ensure sizes prop includes desktop breakpoint
```tsx
// Before
sizes="(max-width: 768px) 100vw"

// After
sizes="(max-width: 768px) 100vw, 1200px"
```

### Wrong Image Size Loaded

**Problem**: Browser loading incorrect image size

**Solution**: Verify sizes prop matches container width
```tsx
// Container is 50% width on desktop
<div className="w-full md:w-1/2">
  <OptimizedImage
    fill
    sizes="(max-width: 768px) 100vw, 50vw"  // Matches container
  />
</div>
```

### Images Not Optimizing

**Problem**: Images not converting to WebP/AVIF

**Solution**: Check Next.js config and browser support
```javascript
// next.config.js
images: {
  formats: ['image/webp', 'image/avif'],
}
```

## Migration Checklist

When adding responsive images:

- [ ] Choose appropriate responsive context or create custom sizes
- [ ] Match sizes to actual layout breakpoints
- [ ] Test on multiple screen sizes
- [ ] Verify correct image sizes are loaded
- [ ] Check WebP/AVIF format delivery
- [ ] Measure performance improvement
- [ ] Test on real devices
- [ ] Run Lighthouse audit

## Resources

- [Next.js Image Documentation](https://nextjs.org/docs/app/api-reference/components/image)
- [Responsive Images Guide](https://web.dev/responsive-images/)
- [Image Optimization](https://web.dev/fast/#optimize-your-images)
- [Sizes Attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#attr-sizes)

## Examples Repository

See `frontend/src/components/ui/__stories__/OptimizedImage.stories.tsx` for interactive examples of all responsive contexts and patterns.
