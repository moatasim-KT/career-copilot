# Image Format Optimization Guide

This document describes the image format optimization configuration and best practices for the Career Copilot application.

## Overview

The application uses Next.js Image Optimization with WebP and AVIF formats to deliver the smallest possible images while maintaining excellent quality. All images are automatically optimized and served in modern formats when supported by the browser.

## Configuration

### Next.js Image Configuration

Located in `next.config.js`:

```javascript
images: {
  // Modern image formats (AVIF first for best compression, WebP fallback)
  formats: ['image/avif', 'image/webp'],
  
  // Quality setting (75 is optimal for WebP/AVIF)
  quality: 75,
  
  // Cache optimized images for 60 days
  minimumCacheTTL: 60 * 60 * 24 * 60,
  
  // Device sizes for responsive images
  deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  
  // Image sizes for smaller images (icons, avatars, thumbnails)
  imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
}
```

## Image Format Comparison

| Format | Compression | Browser Support | Use Case |
|--------|-------------|-----------------|----------|
| **AVIF** | ~50% smaller than JPEG | Chrome 85+, Firefox 93+, Safari 16+ | Primary format for modern browsers |
| **WebP** | ~30% smaller than JPEG | Chrome 23+, Firefox 65+, Safari 14+ | Fallback for older browsers |
| **JPEG** | Baseline | Universal | Final fallback |
| **PNG** | Lossless | Universal | Transparency required |
| **SVG** | Vector | Universal | Icons, logos, simple graphics |

## Image Size Guidelines

### Target Sizes

- **Maximum file size**: 100KB per image
- **Recommended**: 50-75KB for optimal performance
- **Icons/Thumbnails**: < 10KB
- **Hero images**: < 100KB
- **Background images**: < 75KB

### Compression Quality

- **Quality 75**: Optimal balance for WebP/AVIF (recommended)
- **Quality 85**: High quality for important images
- **Quality 60**: Acceptable for background images
- **Quality 50**: Minimum acceptable quality

## Image Compression Script

### Usage

Compress all images in the public directory:

```bash
npm run compress-images
```

### Features

- ✅ Automatically compresses JPEG, PNG, WebP images
- ✅ Ensures images are under 100KB
- ✅ Preserves original images with `.original` extension
- ✅ Generates detailed compression report
- ✅ Adjusts quality automatically to meet size targets
- ✅ Resizes images if quality reduction isn't enough
- ✅ Skips already optimized images

### Example Output

```
Image Compression Script
============================================================
Target: Images under 100KB
Directory: /path/to/public
============================================================

Found 5 image(s) to process

Processing: hero-image.jpg
Original size: 245.32 KB
Backup created: hero-image.original.jpg
Attempt 1: Quality 75% = 156.23 KB
Attempt 2: Quality 65% = 98.45 KB
✓ Compressed successfully!
New size: 98.45 KB
Saved: 146.87 KB (59.9%)

============================================================
COMPRESSION REPORT
============================================================

Total images: 5
Processed: 3
Skipped (already optimized): 2
Failed: 0
Errors: 0

Total original size: 456.78 KB
Total new size: 234.56 KB
Total saved: 222.22 KB (48.6%)

✓ All images successfully optimized!
```

## Best Practices

### 1. Use Next.js Image Component

Always use the `<Image>` component instead of `<img>`:

```tsx
import Image from 'next/image';

// ✅ Good - Automatic optimization
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  quality={75}
  priority // For above-the-fold images
/>

// ❌ Bad - No optimization
<img src="/images/hero.jpg" alt="Hero image" />
```

### 2. Use OptimizedImage Component

For common use cases, use our custom `OptimizedImage` component:

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

// Automatic responsive images with blur placeholder
<OptimizedImage
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority
/>
```

### 3. Specify Sizes for Responsive Images

Use the `sizes` prop to optimize responsive images:

```tsx
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
/>
```

### 4. Use Priority for Above-the-Fold Images

Mark critical images as priority to preload them:

```tsx
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority // Preload this image
/>
```

### 5. Use Blur Placeholders

Enable blur placeholders for better perceived performance:

```tsx
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRg..." // Generate with plaiceholder
/>
```

### 6. Optimize Source Images

Before adding images to the project:

1. **Resize** to the maximum display size needed
2. **Compress** using the compression script
3. **Convert** to WebP format if possible
4. **Verify** file size is under 100KB

### 7. Use SVG for Icons and Logos

For icons, logos, and simple graphics, use SVG:

```tsx
// ✅ Good - Vector format, scales perfectly
<Image
  src="/icons/logo.svg"
  alt="Logo"
  width={120}
  height={40}
/>
```

### 8. Lazy Load Below-the-Fold Images

Images below the fold are automatically lazy-loaded:

```tsx
// Automatically lazy-loaded (no priority prop)
<Image
  src="/images/feature.jpg"
  alt="Feature"
  width={800}
  height={400}
/>
```

## Image Optimization Checklist

Before deploying:

- [ ] All `<img>` tags replaced with `<Image>` component
- [ ] All images compressed to < 100KB
- [ ] WebP/AVIF formats configured in next.config.js
- [ ] Quality setting optimized (75 recommended)
- [ ] Responsive images use `sizes` prop
- [ ] Above-the-fold images marked with `priority`
- [ ] Blur placeholders added for hero images
- [ ] SVG used for icons and logos
- [ ] Image compression script run on all images
- [ ] Image loading tested on slow 3G network

## Testing Image Optimization

### 1. Visual Quality Test

Compare original and optimized images side-by-side:

```bash
# Open original
open public/images/hero.original.jpg

# Open optimized
open public/images/hero.jpg
```

Quality should be visually indistinguishable at normal viewing distances.

### 2. File Size Test

Check file sizes:

```bash
# List all images with sizes
ls -lh public/images/

# Check specific image
du -h public/images/hero.jpg
```

All images should be under 100KB.

### 3. Format Test

Verify WebP/AVIF delivery in browser:

1. Open DevTools → Network tab
2. Load the page
3. Check image requests
4. Verify `Content-Type: image/webp` or `image/avif`

### 4. Performance Test

Run Lighthouse audit:

```bash
npm run build
npm start

# In another terminal
lighthouse http://localhost:3000 --view
```

Target scores:
- Performance: 95+
- Properly sized images: 100%
- Efficient image formats: 100%

### 5. Network Test

Test on slow connections:

1. Open DevTools → Network tab
2. Set throttling to "Slow 3G"
3. Reload page
4. Verify images load progressively with blur placeholders

## Troubleshooting

### Images Not Optimizing

**Problem**: Images are not being converted to WebP/AVIF

**Solution**:
1. Verify `formats: ['image/avif', 'image/webp']` in next.config.js
2. Check that you're using `<Image>` component, not `<img>`
3. Ensure `unoptimized: false` in next.config.js
4. Clear `.next` cache: `rm -rf .next && npm run build`

### Images Too Large

**Problem**: Images are still over 100KB after compression

**Solution**:
1. Run compression script: `npm run compress-images`
2. Manually reduce image dimensions
3. Use lower quality setting (60-70)
4. Consider using WebP source images
5. Split large images into smaller sections

### Poor Image Quality

**Problem**: Compressed images look pixelated or blurry

**Solution**:
1. Increase quality setting in next.config.js (try 85)
2. Use higher resolution source images
3. Avoid compressing images multiple times
4. Use original images from `.original` backup
5. Consider using PNG for images with text

### Slow Image Loading

**Problem**: Images take too long to load

**Solution**:
1. Add `priority` prop to above-the-fold images
2. Use blur placeholders for better perceived performance
3. Implement lazy loading for below-the-fold images
4. Reduce image dimensions
5. Use CDN for image delivery (future enhancement)

## Advanced Optimization

### 1. Responsive Images

Generate multiple sizes for different devices:

```tsx
<Image
  src="/images/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  sizes="(max-width: 640px) 640px,
         (max-width: 1024px) 1024px,
         1200px"
/>
```

Next.js will automatically generate and serve:
- 640px version for mobile
- 1024px version for tablet
- 1200px version for desktop

### 2. Art Direction

Use different images for different screen sizes:

```tsx
<picture>
  <source
    media="(max-width: 640px)"
    srcSet="/images/hero-mobile.jpg"
  />
  <source
    media="(max-width: 1024px)"
    srcSet="/images/hero-tablet.jpg"
  />
  <Image
    src="/images/hero-desktop.jpg"
    alt="Hero"
    width={1200}
    height={600}
  />
</picture>
```

### 3. Dynamic Quality

Adjust quality based on image importance:

```tsx
// Hero image - high quality
<Image src="/hero.jpg" quality={85} />

// Background image - lower quality
<Image src="/background.jpg" quality={60} />

// Thumbnail - standard quality
<Image src="/thumb.jpg" quality={75} />
```

### 4. Blur Data URL Generation

Generate blur placeholders automatically:

```bash
npm install plaiceholder
```

```tsx
import { getPlaiceholder } from 'plaiceholder';

export async function getStaticProps() {
  const { base64 } = await getPlaiceholder('/images/hero.jpg');
  
  return {
    props: { blurDataURL: base64 }
  };
}
```

## Performance Metrics

### Target Metrics

- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Image file size**: < 100KB
- **Image format**: WebP or AVIF
- **Lighthouse Performance**: 95+

### Monitoring

Track image performance in production:

```typescript
// Report Web Vitals
export function reportWebVitals(metric: NextWebVitalsMetric) {
  if (metric.name === 'LCP') {
    // Track Largest Contentful Paint (often an image)
    console.log('LCP:', metric.value);
  }
}
```

## Resources

- [Next.js Image Optimization](https://nextjs.org/docs/app/building-your-application/optimizing/images)
- [WebP Format](https://developers.google.com/speed/webp)
- [AVIF Format](https://jakearchibald.com/2020/avif-has-landed/)
- [Sharp Documentation](https://sharp.pixelplumbing.com/)
- [Web.dev Image Optimization](https://web.dev/fast/#optimize-your-images)

## Summary

✅ **Configured**: WebP and AVIF formats in next.config.js  
✅ **Quality**: Set to 75 for optimal balance  
✅ **Compression**: Script available to compress images < 100KB  
✅ **Testing**: Visual quality, file size, and performance tests documented  
✅ **Best Practices**: Comprehensive guidelines for image optimization  

All images in the application are now optimized for maximum performance while maintaining excellent visual quality.
