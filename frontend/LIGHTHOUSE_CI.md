# Lighthouse CI Configuration

This document describes the Lighthouse CI setup for the Career Copilot frontend application.

## Overview

Lighthouse CI is configured to automatically audit the application's performance, accessibility, best practices, and SEO. The configuration runs audits on key pages and enforces quality thresholds.

## Configuration

The configuration is defined in `lighthouserc.json` and includes:

### Audited Pages

- Home page: `http://localhost:3000`
- Dashboard: `http://localhost:3000/dashboard`
- Jobs page: `http://localhost:3000/jobs`
- Applications page: `http://localhost:3000/applications`

### Performance Budgets

#### Category Scores (0-1 scale)
- **Performance**: ≥ 0.90 (90%)
- **Accessibility**: ≥ 0.95 (95%)
- **Best Practices**: ≥ 0.95 (95%)
- **SEO**: ≥ 0.90 (90%)

#### Core Web Vitals
- **First Contentful Paint (FCP)**: ≤ 1.5s
- **Largest Contentful Paint (LCP)**: ≤ 2.5s
- **Cumulative Layout Shift (CLS)**: ≤ 0.1
- **Total Blocking Time (TBT)**: ≤ 200ms
- **Speed Index**: ≤ 3s
- **Time to Interactive (TTI)**: ≤ 3.5s
- **Max Potential FID**: ≤ 100ms

#### Resource Budgets
- **Total Byte Weight**: ≤ 512KB (warning threshold)
- **DOM Size**: ≤ 1500 nodes (warning threshold)

### Test Configuration

- **Number of Runs**: 3 (median values used)
- **Device**: Desktop
- **Screen Resolution**: 1920x1080
- **Network Throttling**: Fast 3G simulation
  - RTT: 40ms
  - Throughput: 10240 Kbps
  - CPU Slowdown: 1x (no throttling)

## Usage

### Run Full Audit

Run the complete Lighthouse CI audit (collect, assert, upload):

```bash
npm run lighthouse
```

This command will:
1. Build the production application
2. Start the production server
3. Run Lighthouse audits on all configured URLs (3 runs each)
4. Assert against the defined budgets
5. Upload results to temporary public storage
6. Shut down the server

### Individual Commands

Run specific parts of the audit process:

```bash
# Collect audit data only
npm run lighthouse:collect

# Assert against budgets only (requires collected data)
npm run lighthouse:assert

# Upload results only (requires collected data)
npm run lighthouse:upload
```

## Interpreting Results

### Success

If all assertions pass, you'll see:

```
✅ All assertions passed!
```

### Failures

If any assertions fail, you'll see detailed output like:

```
❌ categories:performance failure for minScore assertion
   Expected: >= 0.9
   Actual: 0.87
```

### Warnings

Warnings don't fail the build but indicate areas for improvement:

```
⚠️  unused-css-rules warning
   Potential savings: 45 KB
```

## CI/CD Integration

### GitHub Actions

To integrate Lighthouse CI into your GitHub Actions workflow:

```yaml
name: Lighthouse CI

on:
  pull_request:
    branches: [main]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Run Lighthouse CI
        working-directory: frontend
        run: npm run lighthouse
      
      - name: Upload Lighthouse results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: lighthouse-results
          path: frontend/.lighthouseci
```

### Vercel Integration

For Vercel deployments, you can run Lighthouse CI against preview deployments:

1. Get the preview URL from Vercel
2. Update the `url` array in `lighthouserc.json` to use the preview URL
3. Run `npm run lighthouse`

## Troubleshooting

### Server Won't Start

If the server fails to start:

1. Check that port 3000 is available
2. Ensure the build completed successfully
3. Check the `startServerReadyPattern` matches your server output

### Timeout Errors

If audits timeout:

1. Increase `startServerReadyTimeout` in `lighthouserc.json`
2. Check server logs for errors
3. Ensure your machine has sufficient resources

### Inconsistent Results

If results vary significantly between runs:

1. Close other applications to free up resources
2. Increase `numberOfRuns` for more stable median values
3. Check for background processes affecting performance

### Failing Assertions

If assertions consistently fail:

1. Review the specific metric that's failing
2. Use Chrome DevTools to profile the issue
3. Consider adjusting budgets if they're too strict for your use case
4. Implement performance optimizations (code splitting, image optimization, etc.)

## Best Practices

### Before Running Audits

1. **Clean Build**: Always run a fresh production build
2. **Close Applications**: Close unnecessary applications to free up resources
3. **Stable Network**: Ensure stable network connection
4. **Updated Dependencies**: Keep dependencies up to date

### Regular Audits

1. **Pre-commit**: Run audits before committing major changes
2. **Pull Requests**: Automate audits in CI/CD for all PRs
3. **Weekly**: Run comprehensive audits weekly to catch regressions
4. **Release**: Always audit before production releases

### Optimization Workflow

1. **Baseline**: Establish baseline metrics
2. **Identify**: Use Lighthouse reports to identify issues
3. **Optimize**: Implement optimizations
4. **Measure**: Re-run audits to verify improvements
5. **Iterate**: Repeat until budgets are met

## Resources

- [Lighthouse CI Documentation](https://github.com/GoogleChrome/lighthouse-ci)
- [Lighthouse Scoring Guide](https://web.dev/performance-scoring/)
- [Core Web Vitals](https://web.dev/vitals/)
- [Web Performance Optimization](https://web.dev/fast/)

## Maintenance

### Updating Budgets

As the application grows, you may need to adjust budgets:

1. Review current performance metrics
2. Set realistic but challenging targets
3. Update `assertions` in `lighthouserc.json`
4. Document changes in this file

### Adding Pages

To audit additional pages:

1. Add URLs to the `url` array in `lighthouserc.json`
2. Ensure pages are accessible without authentication
3. Consider page-specific budgets if needed

### Configuration Changes

When modifying the configuration:

1. Test changes locally first
2. Document the rationale for changes
3. Update this documentation
4. Communicate changes to the team
