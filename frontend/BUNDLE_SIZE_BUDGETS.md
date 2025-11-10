# Bundle Size Budgets

This document describes the bundle size budget system implemented for the Career Copilot frontend application.

## Overview

Bundle size budgets help ensure optimal performance by preventing JavaScript bundles from growing too large. Large bundles increase page load times and negatively impact user experience, especially on slower networks and devices.

## Budget Thresholds

### Per-Route Budgets

- **Warning Threshold**: 200 KB per route
  - Triggers a warning in CI/CD but doesn't fail the build
  - Indicates the bundle is getting large and should be optimized
  
- **Error Threshold**: 250 KB per route
  - Fails the CI/CD build
  - Requires immediate action to reduce bundle size

### Total Bundle Budget

- **Warning**: 1 MB total JavaScript
- **Error**: 1.5 MB total JavaScript

## Configuration

### Next.js Configuration

Bundle size budgets are configured in `next.config.js`:

```javascript
webpack: (config, { isServer, webpack }) => {
  config.performance = {
    hints: process.env.NODE_ENV === 'production' ? 'error' : false,
    maxAssetSize: 250000, // 250KB error threshold
    maxEntrypointSize: 250000, // 250KB error threshold
  };
  return config;
}
```

### Size Limit Configuration

Additional checks are configured in `.size-limit.json` for specific chunks and pages.

## Checking Bundle Sizes

### Local Development

```bash
# Build and check bundle sizes
npm run build
npm run bundle:check

# Build with bundle analyzer
npm run analyze

# Check with size-limit
npm run size-limit
```

### CI/CD Pipeline

Bundle size checks run automatically on:
- Every pull request
- Every push to `main` or `develop` branches
- Changes to frontend code

The workflow:
1. Builds the application
2. Analyzes bundle sizes
3. Compares with base branch (for PRs)
4. Posts a comment on the PR with results
5. Fails the build if error thresholds are exceeded

## Understanding the Report

The bundle size check script generates a detailed report showing:

```
Bundle Size Analysis
────────────────────────────────────────────────────────────────────────────────

Route Bundles:

Route                                   Size           Status         Budget Usage
────────────────────────────────────────────────────────────────────────────────
/dashboard                              185.23 KB      ✓ OK           74.1% ████████████████░░░░
/jobs                                   192.45 KB      ✓ OK           77.0% ████████████████░░░░
/applications                           205.67 KB      ⚠ WARNING      82.3% █████████████████░░░
/analytics                              268.91 KB      ✗ ERROR        107.6% ████████████████████
────────────────────────────────────────────────────────────────────────────────

Total Bundle Size: 852.26 KB
Total Budget Status: ✓ OK
```

### Status Indicators

- ✓ **OK** (Green): Bundle is within warning threshold (< 200 KB)
- ⚠ **WARNING** (Yellow): Bundle exceeds warning threshold but is under error threshold (200-250 KB)
- ✗ **ERROR** (Red): Bundle exceeds error threshold (> 250 KB)

## Optimization Strategies

When a bundle exceeds the budget, consider these optimization strategies:

### 1. Code Splitting

Use dynamic imports to split large components:

```typescript
// Before
import HeavyComponent from './HeavyComponent';

// After
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Skeleton />,
  ssr: false
});
```

### 2. Lazy Loading

Defer loading of non-critical features:

```typescript
// Lazy load charts
const LazyCharts = lazy(() => import('./components/lazy/LazyCharts'));

// Use with Suspense
<Suspense fallback={<ChartSkeleton />}>
  <LazyCharts />
</Suspense>
```

### 3. Tree Shaking

Ensure proper tree shaking by:
- Using ES6 imports/exports
- Importing only what you need from libraries
- Avoiding default exports for large libraries

```typescript
// Bad - imports entire library
import _ from 'lodash';

// Good - imports only what's needed
import { debounce } from 'lodash-es';
```

### 4. Dependency Optimization

- Review and remove unused dependencies
- Use lighter alternatives when possible
- Configure `optimizePackageImports` in `next.config.js`

```javascript
experimental: {
  optimizePackageImports: [
    'lucide-react',
    'recharts',
    'framer-motion',
  ],
}
```

### 5. Image Optimization

- Use Next.js Image component
- Serve images in WebP format
- Implement lazy loading for images

### 6. Route-Based Splitting

Next.js automatically splits code by route. Ensure:
- Each route only imports what it needs
- Shared components are in a common chunk
- Heavy features are route-specific

## Monitoring

### GitHub Actions

The bundle size check runs in the `bundle-check.yml` workflow:
- Analyzes every build
- Compares PR changes with base branch
- Posts detailed comments on PRs
- Fails builds that exceed error thresholds

### Reports

Bundle size reports are:
- Generated on every build
- Saved to `reports/bundle-size-report.json`
- Uploaded as CI/CD artifacts
- Retained for 30 days

### Alerts

The system provides alerts at multiple levels:

1. **Build Time**: Webpack performance hints during build
2. **CI/CD**: GitHub Actions checks and PR comments
3. **Local**: Bundle check script output

## Best Practices

1. **Check Before Committing**: Run `npm run bundle:check` before pushing
2. **Monitor Trends**: Review bundle size reports regularly
3. **Optimize Early**: Address warnings before they become errors
4. **Document Changes**: Note bundle size impacts in PR descriptions
5. **Test Performance**: Verify actual load times, not just bundle sizes

## Troubleshooting

### Build Fails with Bundle Size Error

1. Run `npm run analyze` to visualize the bundle
2. Identify the largest chunks
3. Apply optimization strategies (see above)
4. Re-run `npm run bundle:check` to verify

### Warning Threshold Exceeded

1. Review the specific route causing the warning
2. Consider if optimization is needed now or can be deferred
3. Document the decision in the PR
4. Plan optimization work if deferring

### False Positives

If you believe a bundle size is justified:
1. Document the reasoning in the PR
2. Consider adjusting thresholds (requires team discussion)
3. Ensure the route provides significant value to justify the size

## Resources

- [Next.js Bundle Analyzer](https://www.npmjs.com/package/@next/bundle-analyzer)
- [Webpack Performance](https://webpack.js.org/configuration/performance/)
- [Web.dev: Optimize JavaScript](https://web.dev/fast/#optimize-your-javascript)
- [Next.js: Optimizing Performance](https://nextjs.org/docs/app/building-your-application/optimizing)

## Support

For questions or issues with bundle size budgets:
1. Check this documentation
2. Review the bundle size report
3. Consult with the team lead
4. Open an issue if you believe thresholds need adjustment
