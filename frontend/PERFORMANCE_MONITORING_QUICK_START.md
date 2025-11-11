# Performance Monitoring Quick Start Guide

## Overview

This guide provides quick commands and examples for using the performance monitoring system.

## Quick Commands

### Run Full Lighthouse Audit

```bash
npm run lighthouse
```

This will:
1. Build the production app
2. Start the server
3. Run audits on all configured pages
4. Check against performance budgets
5. Upload results

### Check Bundle Size

```bash
npm run bundle:check
```

### Analyze Bundle

```bash
npm run analyze
```

Opens an interactive bundle analyzer in your browser.

### Type Check

```bash
npm run type-check
```

## Web Vitals Tracking

### Default Setup (Console Logging)

Web Vitals are automatically tracked and logged to the console when you run the app:

```bash
npm run dev
```

Open your browser console to see metrics like:
```
✅ Web Vitals: FCP { value: '1.2s', rating: 'good', ... }
✅ Web Vitals: LCP { value: '2.1s', rating: 'good', ... }
⚠️  Web Vitals: CLS { value: '0.15', rating: 'needs-improvement', ... }
```

### Custom Analytics Provider

To send metrics to your analytics service:

```typescript
// In app/layout.tsx or a provider component
import { setAnalyticsProvider, CustomAPIProvider } from '@/lib/vitals';

// Send to custom endpoint
setAnalyticsProvider(new CustomAPIProvider('/api/analytics/vitals'));
```

### Google Analytics

```typescript
import { setAnalyticsProvider, GoogleAnalyticsProvider } from '@/lib/vitals';

setAnalyticsProvider(new GoogleAnalyticsProvider());
```

### Multiple Providers

```typescript
import { 
  setAnalyticsProvider, 
  CompositeAnalyticsProvider,
  ConsoleAnalyticsProvider,
  GoogleAnalyticsProvider,
  CustomAPIProvider 
} from '@/lib/vitals';

setAnalyticsProvider(new CompositeAnalyticsProvider([
  new ConsoleAnalyticsProvider(), // Development
  new GoogleAnalyticsProvider(),  // GA4
  new CustomAPIProvider('/api/analytics/vitals'), // Custom backend
]));
```

## Performance Budgets

### Current Budgets

| Metric | Budget |
|--------|--------|
| FCP | < 1.5s |
| LCP | < 2.5s |
| INP | < 200ms |
| CLS | < 0.1 |
| TTFB | < 800ms |
| Performance Score | ≥ 95 |
| Accessibility Score | ≥ 95 |
| Bundle Size | < 250KB |

### Check if Budgets are Met

```bash
npm run lighthouse
```

Look for:
- ✅ All assertions passed!
- ❌ categories:performance failure for minScore assertion

## CI/CD Integration

### GitHub Actions

The Lighthouse CI workflow runs automatically on:
- Pull requests to `main` or `develop`
- Pushes to `main`

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab.

### PR Comments

After the workflow runs, a comment will be posted to your PR with results:

```markdown
## 🔦 Lighthouse CI Results

| URL | Performance | Accessibility | Best Practices | SEO |
|-----|-------------|---------------|----------------|-----|
| / | 🟢 95 | 🟢 98 | 🟢 96 | 🟢 92 |
```

## Debugging Performance Issues

### 1. Identify the Issue

Run Lighthouse and check which metric is failing:

```bash
npm run lighthouse
```

### 2. Use Chrome DevTools

1. Open Chrome DevTools (F12)
2. Go to "Performance" tab
3. Click "Record" and interact with your app
4. Stop recording and analyze the flame graph

### 3. Check Bundle Size

```bash
npm run analyze
```

Look for:
- Large dependencies
- Duplicate code
- Unused code

### 4. Check Web Vitals in Real-Time

Open the console while using your app to see Web Vitals as they're measured.

## Common Optimizations

### Improve FCP (First Contentful Paint)

```typescript
// Use Next.js font optimization
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });
```

### Improve LCP (Largest Contentful Paint)

```tsx
// Use Next.js Image component
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority // Preload above-the-fold images
/>
```

### Improve INP (Interaction to Next Paint)

```typescript
// Use code splitting for heavy components
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});
```

### Reduce CLS (Cumulative Layout Shift)

```tsx
// Always specify image dimensions
<Image
  src="/image.jpg"
  alt="Description"
  width={800}
  height={600}
/>

// Reserve space for dynamic content
<div className="min-h-[200px]">
  {loading ? <Skeleton /> : <Content />}
</div>
```

### Reduce Bundle Size

```typescript
// Use tree-shakeable imports
import { Button } from '@/components/ui/Button'; // ✅ Good
import * as UI from '@/components/ui'; // ❌ Bad

// Use dynamic imports for large libraries
const Chart = dynamic(() => import('recharts').then(mod => mod.LineChart));
```

## Monitoring in Production

### View Web Vitals Data

If you've configured a custom analytics provider, you can view the data in your analytics dashboard.

### Set Up Alerts

Configure alerts in your analytics platform to notify you when metrics degrade:

- FCP > 2s
- LCP > 3s
- CLS > 0.15
- Performance Score < 90

### Regular Audits

Schedule regular Lighthouse audits:

```bash
# Weekly audit
npm run lighthouse

# Check trends over time
# Compare with previous results in .lighthouseci/
```

## Troubleshooting

### Lighthouse CI Fails Locally

**Issue**: Server won't start or audits timeout

**Solution**:
1. Check port 3000 is available: `lsof -i :3000`
2. Increase timeout in `lighthouserc.json`
3. Ensure build completed: `npm run build`

### Inconsistent Results

**Issue**: Lighthouse scores vary significantly between runs

**Solution**:
1. Close other applications
2. Increase `numberOfRuns` in `lighthouserc.json`
3. Run on a stable network
4. Disable browser extensions

### Web Vitals Not Logging

**Issue**: No Web Vitals in console

**Solution**:
1. Check `WebVitalsReporter` is in layout
2. Verify `web-vitals` package is installed
3. Check browser console for errors
4. Ensure you're in development mode

## Resources

### Documentation

- [PERFORMANCE_BUDGETS.md](./PERFORMANCE_BUDGETS.md) - Detailed budgets and strategies
- [LIGHTHOUSE_CI.md](./LIGHTHOUSE_CI.md) - Lighthouse CI configuration guide
- [src/lib/vitals.ts](./src/lib/vitals.ts) - Web Vitals implementation (see JSDoc)

### External Resources

- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Next.js Performance](https://nextjs.org/docs/advanced-features/measuring-performance)

## Quick Reference

### Metric Thresholds

```typescript
const THRESHOLDS = {
  FCP: { good: 1.8, poor: 3.0 },
  LCP: { good: 2.5, poor: 4.0 },
  INP: { good: 200, poor: 500 },
  CLS: { good: 0.1, poor: 0.25 },
  TTFB: { good: 800, poor: 1800 },
};
```

### NPM Scripts

```bash
npm run lighthouse          # Full audit
npm run lighthouse:collect  # Collect data only
npm run lighthouse:assert   # Check budgets only
npm run lighthouse:upload   # Upload results only
npm run analyze            # Bundle analyzer
npm run bundle:check       # Check bundle size
```

### File Locations

```
frontend/
├── src/
│   ├── lib/
│   │   └── vitals.ts                    # Web Vitals implementation
│   └── components/
│       └── WebVitalsReporter.tsx        # Web Vitals component
├── .github/
│   └── workflows/
│       └── lighthouse-ci.yml            # CI/CD workflow
├── lighthouserc.json                    # Lighthouse config
├── PERFORMANCE_BUDGETS.md               # Budget documentation
├── LIGHTHOUSE_CI.md                     # Lighthouse guide
└── PERFORMANCE_MONITORING_QUICK_START.md # This file
```

---

**Last Updated**: November 11, 2024
