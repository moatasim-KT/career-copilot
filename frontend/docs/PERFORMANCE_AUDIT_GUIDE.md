# Performance Audit Guide

This guide provides comprehensive instructions for conducting performance audits on the Career Copilot application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Automated Testing](#automated-testing)
- [Manual Testing](#manual-testing)
- [Core Web Vitals](#core-web-vitals)
- [Network Throttling](#network-throttling)
- [CPU Throttling](#cpu-throttling)
- [Performance Targets](#performance-targets)
- [Common Issues](#common-issues)
- [Optimization Strategies](#optimization-strategies)

## Overview

Performance audits ensure the application meets the following targets:

- **Lighthouse Performance Score:** > 95
- **Lighthouse Accessibility Score:** > 95
- **Lighthouse Best Practices Score:** > 95
- **Lighthouse SEO Score:** > 90
- **Bundle Size:** < 250KB gzipped
- **Core Web Vitals:** All metrics in "Good" range

## Prerequisites

Before running performance audits, ensure you have:

1. Node.js 18+ installed
2. All dependencies installed (`npm install`)
3. Production build created (`npm run build`)
4. Chrome browser (for manual testing)

## Quick Start

Run the automated performance audit:

```bash
cd frontend
npm run performance:audit
```

This script will:
1. Build the application for production
2. Analyze bundle sizes
3. Run Lighthouse audits on all main pages
4. Generate a comprehensive report

## Automated Testing

### Lighthouse CI

Lighthouse CI is configured to run audits on the following pages:

- Home page (`/`)
- Dashboard (`/dashboard`)
- Jobs page (`/jobs`)
- Applications page (`/applications`)

**Run Lighthouse CI:**

```bash
npm run lighthouse
```

**Configuration:** `lighthouserc.json`

The configuration includes:
- 3 runs per page (median score used)
- Desktop preset (1920x1080)
- Performance, Accessibility, Best Practices, and SEO audits
- Core Web Vitals measurement

### Bundle Size Analysis

**Analyze bundle sizes:**

```bash
npm run build
npm run analyze
```

This generates an interactive bundle visualization showing:
- Total bundle size
- Individual chunk sizes
- Dependencies and their sizes
- Opportunities for optimization

**Target bundle sizes:**
- Initial bundle: < 150KB gzipped
- Route bundles: < 50KB gzipped each
- Total JS: < 250KB gzipped

## Manual Testing

### Chrome DevTools Performance Panel

1. Open Chrome DevTools (F12)
2. Go to the Performance tab
3. Click the record button
4. Interact with the application
5. Stop recording
6. Analyze the flame chart for:
   - Long tasks (> 50ms)
   - Layout thrashing
   - Excessive re-renders
   - Memory leaks

### Chrome DevTools Lighthouse

1. Open Chrome DevTools (F12)
2. Go to the Lighthouse tab
3. Select categories: Performance, Accessibility, Best Practices, SEO
4. Choose device: Desktop or Mobile
5. Click "Analyze page load"
6. Review the report and recommendations

### Performance Monitor

1. Open Chrome DevTools (F12)
2. Press Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows)
3. Type "Show Performance Monitor"
4. Monitor real-time metrics:
   - CPU usage
   - JS heap size
   - DOM nodes
   - JS event listeners
   - Layouts/sec
   - Style recalcs/sec

## Core Web Vitals

### First Contentful Paint (FCP)

**Target:** < 1.5 seconds

**What it measures:** Time until the first text or image is painted.

**How to improve:**
- Reduce server response time
- Eliminate render-blocking resources
- Minimize CSS and JavaScript
- Use font-display: swap

**Test manually:**
1. Open Chrome DevTools
2. Go to Network tab
3. Throttle to "Fast 3G"
4. Reload page
5. Check FCP in Performance tab

### Largest Contentful Paint (LCP)

**Target:** < 2.5 seconds

**What it measures:** Time until the largest content element is painted.

**How to improve:**
- Optimize images (use Next.js Image)
- Preload critical resources
- Reduce server response time
- Use CDN for static assets

**Test manually:**
1. Open Chrome DevTools
2. Go to Performance tab
3. Record page load
4. Look for LCP marker in timeline

### Cumulative Layout Shift (CLS)

**Target:** < 0.1

**What it measures:** Visual stability - unexpected layout shifts.

**How to improve:**
- Set explicit dimensions for images and videos
- Reserve space for ads and embeds
- Avoid inserting content above existing content
- Use CSS transforms instead of layout-triggering properties

**Test manually:**
1. Open Chrome DevTools
2. Go to Performance tab
3. Enable "Layout Shift Regions" in rendering settings
4. Interact with the page
5. Look for blue highlights indicating shifts

### First Input Delay (FID)

**Target:** < 100 milliseconds

**What it measures:** Time from user interaction to browser response.

**How to improve:**
- Break up long tasks
- Optimize JavaScript execution
- Use web workers for heavy computations
- Defer non-critical JavaScript

**Test manually:**
1. Open Chrome DevTools
2. Go to Performance tab
3. Record interaction
4. Look for long tasks (> 50ms)

### Total Blocking Time (TBT)

**Target:** < 200 milliseconds

**What it measures:** Total time the main thread is blocked.

**How to improve:**
- Code splitting
- Lazy loading
- Optimize third-party scripts
- Use React.memo and useMemo

## Network Throttling

### Slow 3G Simulation

**Settings:**
- Download: 400 Kbps
- Upload: 400 Kbps
- RTT: 400ms

**Test with Chrome DevTools:**

1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Select "Slow 3G" from throttling dropdown
4. Reload page
5. Verify:
   - Page loads within acceptable time
   - Critical content appears first
   - Loading states are shown
   - Images lazy load properly

**Test with Lighthouse:**

```bash
npx lighthouse http://localhost:3000 \
  --throttling-method=simulate \
  --throttling.rttMs=400 \
  --throttling.throughputKbps=400 \
  --view
```

### Fast 3G Simulation

**Settings:**
- Download: 1.6 Mbps
- Upload: 750 Kbps
- RTT: 150ms

**Use for:** Testing typical mobile network conditions.

### Offline Mode

**Test offline functionality:**

1. Open Chrome DevTools
2. Go to Network tab
3. Select "Offline"
4. Verify:
   - Offline banner appears
   - Cached data is shown
   - Actions are queued
   - Helpful error messages

## CPU Throttling

### 4x Slowdown

Simulates low-end devices (e.g., budget Android phones).

**Test with Chrome DevTools:**

1. Open Chrome DevTools (F12)
2. Go to Performance tab
3. Click the gear icon
4. Select "4x slowdown"
5. Record page load and interactions
6. Verify:
   - Page remains responsive
   - Animations are smooth (or gracefully degraded)
   - No long tasks block the UI

### 6x Slowdown

Simulates very low-end devices.

**Use for:** Stress testing and identifying performance bottlenecks.

## Performance Targets

### Lighthouse Scores

| Category | Target | Minimum |
|----------|--------|---------|
| Performance | > 95 | 90 |
| Accessibility | > 95 | 95 |
| Best Practices | > 95 | 95 |
| SEO | > 90 | 85 |

### Core Web Vitals

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| FCP | < 1.5s | 1.5s - 3.0s | > 3.0s |
| LCP | < 2.5s | 2.5s - 4.0s | > 4.0s |
| CLS | < 0.1 | 0.1 - 0.25 | > 0.25 |
| FID | < 100ms | 100ms - 300ms | > 300ms |
| TBT | < 200ms | 200ms - 600ms | > 600ms |

### Bundle Sizes

| Bundle | Target | Maximum |
|--------|--------|---------|
| Initial | < 150KB | 200KB |
| Route | < 50KB | 100KB |
| Total | < 250KB | 300KB |

### Frame Rate

| Scenario | Target | Minimum |
|----------|--------|---------|
| Scrolling | 60 FPS | 50 FPS |
| Animations | 60 FPS | 50 FPS |
| Interactions | 60 FPS | 50 FPS |

## Common Issues

### Issue: Large Bundle Size

**Symptoms:**
- Initial load is slow
- Lighthouse flags "Reduce JavaScript execution time"

**Solutions:**
1. Use dynamic imports for heavy components
2. Lazy load routes
3. Remove unused dependencies
4. Use tree shaking
5. Split vendor bundles

**Example:**

```typescript
// Before
import HeavyChart from './HeavyChart';

// After
const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false
});
```

### Issue: Slow First Contentful Paint

**Symptoms:**
- White screen for > 1.5s
- Lighthouse flags "Eliminate render-blocking resources"

**Solutions:**
1. Inline critical CSS
2. Defer non-critical CSS
3. Preload critical fonts
4. Optimize server response time
5. Use CDN

### Issue: Layout Shifts

**Symptoms:**
- Content jumps during load
- High CLS score
- Lighthouse flags "Avoid large layout shifts"

**Solutions:**
1. Set explicit width/height on images
2. Reserve space for dynamic content
3. Use CSS aspect-ratio
4. Avoid inserting content above existing content

**Example:**

```tsx
// Before
<img src="/image.jpg" alt="..." />

// After
<Image 
  src="/image.jpg" 
  alt="..." 
  width={800} 
  height={600}
  placeholder="blur"
/>
```

### Issue: Long Tasks

**Symptoms:**
- UI freezes during interactions
- High TBT score
- Lighthouse flags "Avoid long main-thread tasks"

**Solutions:**
1. Break up long tasks with setTimeout
2. Use web workers for heavy computations
3. Optimize React re-renders with memo
4. Use virtualization for long lists
5. Defer non-critical work

**Example:**

```typescript
// Before
const result = heavyComputation(data);

// After
const result = await new Promise(resolve => {
  setTimeout(() => {
    resolve(heavyComputation(data));
  }, 0);
});
```

### Issue: Slow List Rendering

**Symptoms:**
- Scrolling is janky
- Page freezes with many items
- Low FPS

**Solutions:**
1. Use @tanstack/react-virtual
2. Implement pagination
3. Reduce DOM nodes
4. Optimize re-renders

**Example:**

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const virtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 80,
  overscan: 5
});
```

## Optimization Strategies

### Code Splitting

**Strategy:** Split code by route and feature.

**Implementation:**
- Use Next.js automatic code splitting
- Use dynamic imports for heavy components
- Lazy load modals and dialogs

**Measure:** Bundle analyzer, Lighthouse

### Image Optimization

**Strategy:** Optimize all images for web.

**Implementation:**
- Use Next.js Image component
- Serve WebP format
- Add blur placeholders
- Lazy load below-fold images
- Use responsive images with sizes prop

**Measure:** Lighthouse, Network tab

### Caching Strategy

**Strategy:** Cache aggressively, revalidate smartly.

**Implementation:**
- Configure React Query cache times
- Use stale-while-revalidate pattern
- Implement service worker
- Set proper HTTP cache headers

**Measure:** Network tab, React Query DevTools

### List Virtualization

**Strategy:** Render only visible items.

**Implementation:**
- Use @tanstack/react-virtual
- Set appropriate overscan
- Optimize item rendering

**Measure:** Performance tab, FPS meter

### Font Optimization

**Strategy:** Load fonts efficiently.

**Implementation:**
- Use font-display: swap
- Preload critical fonts
- Subset fonts
- Use system fonts as fallback

**Measure:** Lighthouse, Network tab

### Third-Party Scripts

**Strategy:** Load third-party scripts efficiently.

**Implementation:**
- Use Next.js Script component
- Load analytics asynchronously
- Defer non-critical scripts
- Use facades for heavy embeds

**Measure:** Lighthouse, Network tab

## Testing Workflow

### Pre-Deployment Checklist

1. **Build and Analyze**
   ```bash
   npm run build
   npm run analyze
   ```
   - Verify bundle sizes are within targets
   - Check for unexpected large dependencies

2. **Run Lighthouse CI**
   ```bash
   npm run lighthouse
   ```
   - Verify all scores meet targets
   - Review and address any warnings

3. **Manual Testing**
   - Test on slow 3G network
   - Test with 4x CPU throttling
   - Test on low-end device
   - Verify Core Web Vitals

4. **Cross-Browser Testing**
   - Test on Chrome, Firefox, Safari, Edge
   - Verify performance is consistent

5. **Mobile Testing**
   - Test on real mobile devices
   - Verify touch interactions
   - Check mobile-specific performance

### Continuous Monitoring

1. **Set up Lighthouse CI in GitHub Actions**
   - Run on every PR
   - Fail build if scores drop below thresholds
   - Post results as PR comment

2. **Monitor Real User Metrics (RUM)**
   - Use Sentry Performance Monitoring
   - Track Core Web Vitals
   - Set up alerts for regressions

3. **Regular Audits**
   - Run full performance audit monthly
   - Review and update optimization strategies
   - Document performance improvements

## Resources

- [Web.dev Performance](https://web.dev/performance/)
- [Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [Core Web Vitals](https://web.dev/vitals/)
- [Next.js Performance](https://nextjs.org/docs/advanced-features/measuring-performance)
- [React Performance](https://react.dev/learn/render-and-commit)

## Support

For performance-related questions or issues:
1. Check this guide first
2. Review Lighthouse recommendations
3. Consult the development team
4. File a performance issue on GitHub
