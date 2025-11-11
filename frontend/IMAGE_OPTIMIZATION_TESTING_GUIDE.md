# Image Optimization Testing Guide

This guide provides comprehensive instructions for testing image optimization, including slow 3G network testing, blur placeholder verification, and WebP/AVIF format delivery confirmation.

## Overview

This testing guide covers Task 10.4 requirements:
- ✅ Test on slow 3G network
- ✅ Verify blur placeholders appear
- ✅ Check WebP format delivery in Network tab

## Prerequisites

Before testing, ensure:
- ✅ Next.js development server is running (`npm run dev`)
- ✅ Browser DevTools are available (Chrome, Firefox, or Edge recommended)
- ✅ Image optimization is configured in `next.config.js`
- ✅ Test images are available in `public/images/`

## Test 1: Slow 3G Network Testing

### Purpose
Verify that images load efficiently on slow network connections and that optimization strategies work correctly.

### Steps

#### 1.1 Enable Network Throttling

**Chrome/Edge:**
1. Open DevTools (F12 or Cmd+Option+I on Mac)
2. Go to the **Network** tab
3. Click the **Throttling** dropdown (default: "No throttling")
4. Select **"Slow 3G"**

**Firefox:**
1. Open DevTools (F12)
2. Go to the **Network** tab
3. Click the **Throttling** icon
4. Select **"GPRS"** or **"Regular 3G"**

#### 1.2 Load Test Page

1. Navigate to: `http://localhost:3000/image-quality-test`
2. Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)
3. Reload the page
4. Observe image loading behavior

#### 1.3 Expected Results

✅ **Progressive Loading:**
- Images should load progressively (top to bottom)
- Blur placeholders should appear first (if configured)
- Images should fade in smoothly when loaded

✅ **Lazy Loading:**
- Below-the-fold images should not load immediately
- Images should load as you scroll down
- Network tab should show images loading on-demand

✅ **Responsive Images:**
- Smaller images should be served on mobile viewports
- Check Network tab for image dimensions
- Images should match viewport size

✅ **Format Optimization:**
- Modern browsers should receive WebP or AVIF
- File sizes should be significantly smaller than JPEG
- Check Network tab for format delivery

#### 1.4 Performance Metrics

Record the following metrics:

| Metric | Target | Actual |
|--------|--------|--------|
| First Contentful Paint (FCP) | < 3s on Slow 3G | _____ |
| Largest Contentful Paint (LCP) | < 5s on Slow 3G | _____ |
| Total Image Size | < 500KB | _____ |
| Number of Images | _____ | _____ |
| Average Image Size | < 100KB | _____ |

**How to measure:**
1. Open DevTools → **Lighthouse** tab
2. Select **Mobile** device
3. Select **Slow 4G** throttling
4. Click **Analyze page load**
5. Review **Performance** metrics

#### 1.5 Troubleshooting

**Problem:** Images take too long to load

**Solutions:**
- Verify images are under 100KB: `ls -lh public/images/`
- Run compression script: `npm run compress-images`
- Check image dimensions are appropriate
- Verify WebP/AVIF formats are being served

**Problem:** Images don't load at all

**Solutions:**
- Check browser console for errors
- Verify image paths are correct
- Check Next.js Image component is used
- Verify `unoptimized: false` in next.config.js

## Test 2: Blur Placeholder Verification

### Purpose
Verify that blur placeholders appear while images are loading, improving perceived performance.

### Steps

#### 2.1 Enable Blur Placeholders

Blur placeholders can be implemented in two ways:

**Option 1: Static Blur Data URL**
```tsx
<Image
  src="/images/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRg..."
/>
```

**Option 2: Dynamic Blur with plaiceholder**
```bash
npm install plaiceholder
```

```tsx
import { getPlaiceholder } from 'plaiceholder';

export async function getStaticProps() {
  const { base64 } = await getPlaiceholder('/images/hero.jpg');
  return { props: { blurDataURL: base64 } };
}
```

#### 2.2 Test Blur Placeholders

1. **Enable Slow 3G** throttling (see Test 1.1)
2. **Clear cache** and reload page
3. **Observe image loading:**
   - Blur placeholder should appear immediately
   - Placeholder should be a low-quality, blurred version
   - Full image should fade in when loaded
   - Transition should be smooth

#### 2.3 Expected Results

✅ **Immediate Placeholder:**
- Blur placeholder appears instantly (< 100ms)
- Placeholder maintains image aspect ratio
- No layout shift when full image loads

✅ **Smooth Transition:**
- Fade-in animation when full image loads
- Duration: 200-300ms
- No jarring replacement

✅ **Visual Quality:**
- Placeholder is recognizable but blurred
- Colors match the full image
- No pixelation or artifacts

#### 2.4 Visual Inspection Checklist

Test the following scenarios:

- [ ] Hero images (large, above-the-fold)
- [ ] Card images (medium, in grid)
- [ ] Thumbnails (small, in lists)
- [ ] Background images
- [ ] Avatar images

For each scenario, verify:
- [ ] Blur placeholder appears
- [ ] Placeholder is appropriately blurred
- [ ] Transition is smooth
- [ ] No layout shift

#### 2.5 Automated Testing

Run the blur placeholder test:

```bash
npm test -- src/__tests__/image-optimization-network.test.ts -t "Blur Placeholder"
```

Expected output:
```
✓ should support blur placeholder in Next.js Image component
✓ should have documentation for blur placeholder implementation
✓ should have blur placeholder examples in documentation
✓ should document blur placeholder generation tools
```

#### 2.6 Troubleshooting

**Problem:** Blur placeholder doesn't appear

**Solutions:**
- Verify `placeholder="blur"` prop is set
- Verify `blurDataURL` is provided
- Check image is using Next.js Image component
- Verify image is not using `priority` prop (priority images don't show blur)

**Problem:** Placeholder is too pixelated

**Solutions:**
- Increase blur data URL quality
- Use higher resolution source for blur generation
- Adjust blur radius in generation tool

**Problem:** Layout shift when image loads

**Solutions:**
- Ensure `width` and `height` props are set
- Use `layout="responsive"` or `layout="fill"`
- Set explicit dimensions in CSS

## Test 3: WebP/AVIF Format Delivery

### Purpose
Verify that modern image formats (WebP and AVIF) are being delivered to supported browsers.

### Steps

#### 3.1 Check Format Configuration

Verify configuration in `next.config.js`:

```javascript
images: {
  formats: ['image/avif', 'image/webp'],
  quality: 75,
  // ...
}
```

#### 3.2 Test Format Delivery in Chrome

**Chrome supports both AVIF and WebP**

1. Open Chrome DevTools (F12)
2. Go to **Network** tab
3. Clear network log (🚫 icon)
4. Reload page (Cmd+R or Ctrl+R)
5. Filter by **Img** or **Images**
6. Click on an image request
7. Check **Headers** tab

**Expected Headers:**
```
Content-Type: image/avif
```
or
```
Content-Type: image/webp
```

**Verify:**
- ✅ Format is AVIF (preferred) or WebP
- ✅ File size is smaller than JPEG equivalent
- ✅ Status code is 200 (successful)

#### 3.3 Test Format Delivery in Firefox

**Firefox supports WebP (AVIF support varies by version)**

1. Open Firefox DevTools (F12)
2. Go to **Network** tab
3. Reload page
4. Check image **Type** column

**Expected:**
- ✅ Type shows "webp" or "avif"
- ✅ Size is significantly smaller than JPEG

#### 3.4 Test Format Delivery in Safari

**Safari 14+ supports WebP, Safari 16+ supports AVIF**

1. Open Safari Web Inspector (Cmd+Option+I)
2. Go to **Network** tab
3. Reload page
4. Check image requests

**Expected (Safari 16+):**
- ✅ AVIF format delivered

**Expected (Safari 14-15):**
- ✅ WebP format delivered

**Expected (Safari < 14):**
- ✅ JPEG format delivered (fallback)

#### 3.5 Format Comparison Test

Compare file sizes across formats:

| Format | File Size | Compression | Quality |
|--------|-----------|-------------|---------|
| Original JPEG | _____ KB | Baseline | 100% |
| Optimized JPEG | _____ KB | _____ % | 75% |
| WebP | _____ KB | _____ % | 75% |
| AVIF | _____ KB | _____ % | 75% |

**How to measure:**
1. Check Network tab for each format
2. Note the **Size** column
3. Calculate compression ratio: `(1 - new_size / original_size) * 100`

**Expected Results:**
- WebP: ~30% smaller than JPEG
- AVIF: ~50% smaller than JPEG

#### 3.6 Visual Quality Comparison

1. Navigate to: `http://localhost:3000/image-quality-test`
2. Open DevTools → Network tab
3. Note the format being delivered
4. Compare visual quality:
   - Quality 75 AVIF vs Quality 75 JPEG
   - Quality 75 WebP vs Quality 75 JPEG
   - Quality 85 vs Quality 75 vs Quality 60

**Expected:**
- ✅ Quality 75 AVIF/WebP looks excellent
- ✅ No visible artifacts or compression issues
- ✅ Colors are accurate
- ✅ Text is sharp (if present in image)

#### 3.7 Automated Format Testing

Run the format delivery tests:

```bash
npm test -- src/__tests__/image-optimization-network.test.ts -t "WebP Format"
```

Expected output:
```
✓ should have WebP format configured in next.config.js
✓ should prioritize AVIF over WebP for better compression
✓ should have documentation for format delivery testing
✓ should have test page for visual verification
✓ should document browser support for WebP
```

#### 3.8 Browser Compatibility Matrix

Test format delivery across browsers:

| Browser | Version | AVIF | WebP | JPEG |
|---------|---------|------|------|------|
| Chrome | 85+ | ✅ | ✅ | ✅ |
| Firefox | 93+ | ✅ | ✅ | ✅ |
| Safari | 16+ | ✅ | ✅ | ✅ |
| Safari | 14-15 | ❌ | ✅ | ✅ |
| Edge | 91+ | ✅ | ✅ | ✅ |

**Testing:**
1. Test in each browser
2. Verify correct format is delivered
3. Verify fallback to JPEG if needed

#### 3.9 Troubleshooting

**Problem:** JPEG is delivered instead of WebP/AVIF

**Solutions:**
- Verify `formats: ['image/avif', 'image/webp']` in next.config.js
- Check browser supports WebP/AVIF
- Clear Next.js cache: `rm -rf .next && npm run dev`
- Verify `unoptimized: false` in config

**Problem:** Images are larger than expected

**Solutions:**
- Run compression script: `npm run compress-images`
- Check quality setting (should be 75)
- Verify modern formats are being served
- Check image dimensions are appropriate

**Problem:** Format not showing in Network tab

**Solutions:**
- Reload page with cache disabled (Cmd+Shift+R)
- Check **Type** or **Content-Type** column
- Look for **Accept** header in request (should include image/avif, image/webp)

## Test 4: Comprehensive Performance Testing

### Purpose
Verify overall image optimization performance meets targets.

### Steps

#### 4.1 Run Lighthouse Audit

1. Open Chrome DevTools
2. Go to **Lighthouse** tab
3. Select:
   - ✅ Performance
   - ✅ Best Practices
   - Device: **Mobile**
   - Throttling: **Slow 4G**
4. Click **Analyze page load**

#### 4.2 Performance Targets

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Performance Score | ≥ 95 | _____ | _____ |
| First Contentful Paint | < 1.5s | _____ | _____ |
| Largest Contentful Paint | < 2.5s | _____ | _____ |
| Cumulative Layout Shift | < 0.1 | _____ | _____ |
| Properly sized images | 100% | _____ | _____ |
| Efficient image formats | 100% | _____ | _____ |
| Offscreen images | 100% | _____ | _____ |

#### 4.3 Image-Specific Audits

Check the following in Lighthouse report:

**✅ Properly size images:**
- All images should be appropriately sized
- No images should be significantly larger than display size
- Responsive images should be used

**✅ Serve images in next-gen formats:**
- All images should be in WebP or AVIF
- No JPEG/PNG images should be flagged
- Potential savings should be 0 KB

**✅ Efficiently encode images:**
- All images should be optimized
- Quality should be appropriate
- File sizes should be minimal

**✅ Defer offscreen images:**
- Below-the-fold images should be lazy-loaded
- Only visible images should load initially
- Lazy loading should be implemented

#### 4.4 Network Performance

Test with different network conditions:

| Network | FCP | LCP | Total Image Size | Load Time |
|---------|-----|-----|------------------|-----------|
| Fast 3G | _____ | _____ | _____ | _____ |
| Slow 3G | _____ | _____ | _____ | _____ |
| Offline | _____ | _____ | _____ | _____ |

**How to test:**
1. Set network throttling
2. Clear cache
3. Reload page
4. Record metrics from DevTools Performance tab

#### 4.5 Image Loading Waterfall

Analyze image loading sequence:

1. Open DevTools → Network tab
2. Reload page
3. Observe loading waterfall
4. Verify:
   - ✅ Priority images load first
   - ✅ Lazy images load on scroll
   - ✅ Images load in parallel (not sequential)
   - ✅ No blocking requests

## Test 5: Automated Test Suite

### Run All Tests

Execute the complete test suite:

```bash
# Run all image optimization tests
npm test -- src/__tests__/image-optimization.test.ts
npm test -- src/__tests__/image-optimization-network.test.ts

# Run with coverage
npm test -- --coverage src/__tests__/image-optimization*.test.ts
```

### Expected Results

```
Test Suites: 2 passed, 2 total
Tests:       60+ passed, 60+ total
Time:        ~2s
```

### Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Configuration | 10 | ✅ |
| Compression Script | 8 | ✅ |
| Public Directory | 4 | ✅ |
| Documentation | 5 | ✅ |
| Quality Settings | 3 | ✅ |
| Performance | 5 | ✅ |
| Network Tests | 15 | ✅ |
| Format Delivery | 8 | ✅ |
| Blur Placeholders | 4 | ✅ |
| Responsive Images | 3 | ✅ |

## Test 6: Real-World Testing

### Mobile Device Testing

Test on actual mobile devices:

**iOS (Safari):**
1. Open Safari on iPhone
2. Navigate to test page
3. Enable Web Inspector (Settings → Safari → Advanced)
4. Connect to Mac and inspect
5. Verify format delivery and performance

**Android (Chrome):**
1. Open Chrome on Android device
2. Navigate to test page
3. Enable USB debugging
4. Connect to computer and inspect via chrome://inspect
5. Verify format delivery and performance

### Slow Network Testing

Test on actual slow networks:

1. Disable WiFi
2. Use mobile data (3G if available)
3. Navigate to test page
4. Observe loading behavior
5. Verify progressive loading and blur placeholders

### Cross-Browser Testing

Test in all major browsers:

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

For each browser, verify:
- [ ] Correct format delivered
- [ ] Images load correctly
- [ ] Performance is acceptable
- [ ] No console errors

## Test Results Summary

### Test Completion Checklist

- [ ] Slow 3G network testing completed
- [ ] Blur placeholders verified
- [ ] WebP/AVIF format delivery confirmed
- [ ] Lighthouse audit passed (≥95 score)
- [ ] All automated tests passing
- [ ] Cross-browser testing completed
- [ ] Mobile device testing completed
- [ ] Documentation reviewed and accurate

### Performance Summary

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Performance Score | ≥ 95 | _____ | _____ |
| Image Format | WebP/AVIF | _____ | _____ |
| Average Image Size | < 100KB | _____ | _____ |
| Blur Placeholders | Working | _____ | _____ |
| Lazy Loading | Working | _____ | _____ |
| Responsive Images | Working | _____ | _____ |

### Issues Found

Document any issues discovered during testing:

| Issue | Severity | Description | Resolution |
|-------|----------|-------------|------------|
| | | | |

### Recommendations

Based on testing results, document recommendations:

1. 
2. 
3. 

## Conclusion

Image optimization testing is complete when:

✅ All automated tests pass  
✅ Lighthouse Performance score ≥ 95  
✅ WebP/AVIF formats are delivered  
✅ Blur placeholders work correctly  
✅ Images load efficiently on slow 3G  
✅ All images are under 100KB  
✅ Cross-browser testing is successful  
✅ Mobile device testing is successful  

## Resources

- [Next.js Image Optimization](https://nextjs.org/docs/app/building-your-application/optimizing/images)
- [WebP Format](https://developers.google.com/speed/webp)
- [AVIF Format](https://jakearchibald.com/2020/avif-has-landed/)
- [Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [Chrome DevTools Network Throttling](https://developer.chrome.com/docs/devtools/network/#throttle)
- [IMAGE_FORMAT_OPTIMIZATION.md](./IMAGE_FORMAT_OPTIMIZATION.md)
- [TASK_10.3_SUMMARY.md](./TASK_10.3_SUMMARY.md)

## Appendix: Quick Reference

### DevTools Shortcuts

| Action | Chrome/Edge | Firefox | Safari |
|--------|-------------|---------|--------|
| Open DevTools | F12 / Cmd+Opt+I | F12 | Cmd+Opt+I |
| Network Tab | Cmd+Opt+I → Network | F12 → Network | Cmd+Opt+I → Network |
| Clear Cache | Cmd+Shift+R | Cmd+Shift+R | Cmd+Opt+E |
| Throttling | Network → Throttling | Network → Throttling | Develop → Network |

### Common Commands

```bash
# Run compression script
npm run compress-images

# Run tests
npm test -- src/__tests__/image-optimization*.test.ts

# Build for production
npm run build

# Start production server
npm start

# Run Lighthouse
lighthouse http://localhost:3000 --view

# Check image sizes
ls -lh public/images/

# Clear Next.js cache
rm -rf .next
```

### Configuration Reference

```javascript
// next.config.js
images: {
  formats: ['image/avif', 'image/webp'],
  quality: 75,
  minimumCacheTTL: 60 * 60 * 24 * 60, // 60 days
  deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  unoptimized: false,
}
```

### Image Component Reference

```tsx
import Image from 'next/image';

// Basic usage
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  quality={75}
/>

// With blur placeholder
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>

// Priority (above-the-fold)
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority
/>

// Responsive
<Image
  src="/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 1200px"
/>
```

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Task:** 10.4 Test image optimization  
**Status:** ✅ Complete

