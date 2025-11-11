# Performance Testing Guide

This guide explains how to run comprehensive performance tests for virtualized components and interpret the results.

## Overview

The performance testing suite provides:

- **Render Time Measurement**: How long it takes to initially render components
- **FPS Monitoring**: Frames per second during idle and scrolling
- **Memory Usage Tracking**: JavaScript heap usage (Chrome only)
- **Device Simulation**: Test on simulated lower-end devices with CPU throttling
- **Comparison Reports**: Virtualized vs non-virtualized performance

## Quick Start

### Running Tests in Browser Console

1. Open your application in Chrome (for memory profiling)
2. Open DevTools Console (F12)
3. Navigate to a page with virtualized components
4. Run the test:

```javascript
// Import the test utilities
import { quickTest } from '@/lib/performance/runPerformanceTests';

// Test VirtualJobList with 1000 items
await quickTest(
  'VirtualJobList',
  1000,
  () => {
    // Your render logic here
    // This should trigger a re-render with 1000 items
  },
  () => document.querySelector('[data-testid="virtual-job-list"]')
);
```

### Running Comprehensive Test Suite

```javascript
import { runAllPerformanceTests, exportTestResults } from '@/lib/performance/runPerformanceTests';

const configs = [
  {
    name: 'VirtualJobList',
    itemCounts: [100, 500, 1000, 5000],
    testVirtualized: true,
    testNonVirtualized: true, // Only tests up to 500 items
    devices: ['desktop', 'mobile'],
    renderFn: (count) => {
      // Trigger render with count items
      setJobCount(count);
    },
    getScrollElement: () => document.querySelector('[data-testid="virtual-job-list"]'),
  },
  {
    name: 'VirtualApplicationList',
    itemCounts: [100, 500, 1000, 5000],
    testVirtualized: true,
    testNonVirtualized: true,
    devices: ['desktop', 'mobile'],
    renderFn: (count) => {
      setApplicationCount(count);
    },
    getScrollElement: () => document.querySelector('[data-testid="virtual-application-list"]'),
  },
  {
    name: 'VirtualDataTable',
    itemCounts: [100, 500, 1000, 2000, 5000],
    testVirtualized: true,
    testNonVirtualized: false, // Skip non-virtualized for tables
    devices: ['desktop', 'laptop', 'mobile'],
    renderFn: (count) => {
      setTableRowCount(count);
    },
    getScrollElement: () => document.querySelector('[data-testid="datatable-container"]'),
  },
];

// Run all tests
const { results, comparisons, report } = await runAllPerformanceTests(configs);

// Export results
exportTestResults(results, report);
```

## Device Profiles

The testing suite includes several device profiles with CPU throttling:

| Profile | CPU Slowdown | Description |
|---------|--------------|-------------|
| Desktop | 1x (none) | Modern desktop with fast CPU |
| Laptop | 2x | Average laptop with moderate CPU |
| Tablet | 3x | iPad or Android tablet |
| Mobile | 4x | Budget smartphone with limited resources |

## Performance Targets

### Render Time
- **Target**: < 200ms for initial render
- **Maximum**: < 500ms
- **Measurement**: Time from render start to completion

### FPS (Frames Per Second)
- **Target**: 60 FPS
- **Minimum**: 55 FPS
- **Measurement**: Average FPS during scrolling

### Jank
- **Target**: < 5% of frames
- **Maximum**: < 10% of frames
- **Definition**: Frames that take longer than 16.67ms (below 60fps)

### Memory Usage
- **Target**: < 80% of heap limit
- **Maximum**: < 90% of heap limit
- **Measurement**: JavaScript heap size (Chrome only)

## Understanding Results

### Benchmark Results Table

```
| Test | Items | Device | Virtualized | Render (ms) | Avg FPS | Min FPS | Jank | Memory (MB) | Status |
|------|-------|--------|-------------|-------------|---------|---------|------|-------------|--------|
| VirtualJobList | 1000 | Desktop | Yes | 145.23 | 60 | 58 | 3 | 45.2 | ✅ PASS |
| VirtualJobList | 1000 | Mobile | Yes | 312.45 | 56 | 52 | 12 | 48.1 | ❌ FAIL |
```

**Columns Explained**:
- **Test**: Component being tested
- **Items**: Number of items rendered
- **Device**: Device profile used
- **Virtualized**: Whether virtualization is enabled
- **Render (ms)**: Initial render time in milliseconds
- **Avg FPS**: Average frames per second during scrolling
- **Min FPS**: Minimum FPS observed (most important metric)
- **Jank**: Number of frames that dropped below 60fps
- **Memory (MB)**: JavaScript heap usage in megabytes
- **Status**: Pass/fail based on performance targets

### Comparison Results

```
| Items | Render Time | FPS | Memory |
|-------|-------------|-----|--------|
| 100 | ↓ 15.3% | ↑ 2.1% | ↓ 45.2% |
| 500 | ↓ 42.7% | ↑ 18.5% | ↓ 78.3% |
```

**Symbols**:
- **↓**: Improvement (lower is better for render time and memory)
- **↑**: Improvement (higher is better for FPS)

**Interpretation**:
- Render Time: Virtualized version is 42.7% faster
- FPS: Virtualized version has 18.5% higher FPS
- Memory: Virtualized version uses 78.3% less memory

## Running Tests for Specific Components

### VirtualJobList

```javascript
import { runBenchmark } from '@/lib/performance/performanceTesting';
import { DEVICE_PROFILES } from '@/lib/performance/performanceTesting';

const result = await runBenchmark(
  'VirtualJobList',
  1000, // item count
  true, // virtualized
  async () => {
    // Render 1000 jobs
    const jobs = generateMockJobs(1000);
    setJobs(jobs);
  },
  () => document.querySelector('[data-testid="virtual-job-list"]'),
  DEVICE_PROFILES.mobile // Test on mobile device
);

console.log('Render Time:', result.metrics.renderTime, 'ms');
console.log('Average FPS:', result.metrics.scrollPerformance.averageFPS);
console.log('Passed:', result.passed);
```

### VirtualApplicationList

```javascript
const result = await runBenchmark(
  'VirtualApplicationList',
  5000,
  true,
  async () => {
    const applications = generateMockApplications(5000);
    setApplications(applications);
  },
  () => document.querySelector('[data-testid="virtual-application-list"]'),
  DEVICE_PROFILES.desktop
);
```

### VirtualDataTable

```javascript
const result = await runBenchmark(
  'VirtualDataTable',
  2000,
  true,
  async () => {
    const data = generateMockTableData(2000);
    setTableData(data);
  },
  () => document.querySelector('[data-testid="datatable-container"]'),
  DEVICE_PROFILES.laptop
);
```

## Automated Testing

### Integration with Test Suite

Create a test file for automated performance testing:

```typescript
// frontend/src/__tests__/performance/virtualization.performance.test.ts

import { describe, it, expect } from 'vitest';
import { runBenchmark, DEVICE_PROFILES } from '@/lib/performance/performanceTesting';

describe('Virtualization Performance', () => {
  it('should render 1000 jobs in under 500ms on desktop', async () => {
    const result = await runBenchmark(
      'VirtualJobList',
      1000,
      true,
      async () => {
        // Render logic
      },
      () => document.querySelector('[data-testid="virtual-job-list"]'),
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.renderTime).toBeLessThan(500);
    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
    expect(result.passed).toBe(true);
  });

  it('should maintain 55+ FPS on mobile with 500 items', async () => {
    const result = await runBenchmark(
      'VirtualJobList',
      500,
      true,
      async () => {
        // Render logic
      },
      () => document.querySelector('[data-testid="virtual-job-list"]'),
      DEVICE_PROFILES.mobile
    );

    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
  });
});
```

Run with:
```bash
npm run test:performance
```

## Troubleshooting

### Low FPS

**Symptoms**: FPS below 55, high jank count

**Possible Causes**:
- Too many items rendered at once (virtualization not working)
- Heavy computations in render cycle
- Large images not optimized
- Complex CSS animations

**Solutions**:
1. Verify virtualization is enabled
2. Check `overscan` setting (should be 5-10)
3. Optimize item rendering (memoization)
4. Use `React.memo()` for list items
5. Lazy load images

### High Render Time

**Symptoms**: Initial render > 500ms

**Possible Causes**:
- Synchronous data processing
- Large initial dataset
- Expensive calculations during render

**Solutions**:
1. Use `useMemo()` for expensive calculations
2. Defer non-critical rendering
3. Implement progressive rendering
4. Optimize data structures

### High Memory Usage

**Symptoms**: Memory > 90% of heap limit

**Possible Causes**:
- Memory leaks
- Too many items in memory
- Large cached data

**Solutions**:
1. Check for memory leaks (event listeners, timers)
2. Reduce cache size
3. Implement data pagination
4. Clear unused data

### Inconsistent Results

**Symptoms**: Results vary significantly between runs

**Possible Causes**:
- Background processes
- Browser extensions
- Garbage collection timing

**Solutions**:
1. Close other tabs and applications
2. Disable browser extensions
3. Run tests multiple times and average
4. Use Chrome's Performance profiler for detailed analysis

## Best Practices

### 1. Test on Real Devices

While CPU throttling simulates slower devices, always test on real devices for accurate results:
- iPhone SE (low-end iOS)
- Budget Android phone
- iPad
- Various desktop browsers

### 2. Test with Realistic Data

Use realistic data sizes and complexity:
- Actual text lengths
- Real image sizes
- Typical data structures

### 3. Test Different Scenarios

- Empty state (0 items)
- Small dataset (10-50 items)
- Medium dataset (100-500 items)
- Large dataset (1000-5000 items)
- Extreme dataset (10000+ items)

### 4. Monitor Over Time

Track performance metrics over time to detect regressions:
```javascript
import { saveResults, loadResults } from '@/lib/performance/performanceTesting';

// Save baseline
saveResults('baseline-2024-01', results);

// Compare later
const baseline = loadResults('baseline-2024-01');
const current = await runBenchmark(/* ... */);

// Compare metrics
```

### 5. Use Chrome DevTools

For detailed analysis:
1. Open DevTools > Performance tab
2. Start recording
3. Interact with component
4. Stop recording
5. Analyze flame graph

## Performance Optimization Checklist

- [ ] Virtualization enabled for lists > 100 items
- [ ] `React.memo()` used for list items
- [ ] `useMemo()` for expensive calculations
- [ ] `useCallback()` for event handlers
- [ ] Images lazy loaded and optimized
- [ ] CSS animations use `transform` and `opacity`
- [ ] No layout thrashing (batch DOM reads/writes)
- [ ] Debounced scroll handlers
- [ ] Proper cleanup in `useEffect`
- [ ] Bundle size optimized (code splitting)

## Reporting Issues

When reporting performance issues, include:

1. **Test Configuration**:
   - Component name
   - Item count
   - Device profile
   - Browser and version

2. **Results**:
   - Render time
   - FPS metrics
   - Memory usage
   - Jank count

3. **Environment**:
   - Operating system
   - Hardware specs
   - Network conditions

4. **Steps to Reproduce**:
   - Exact steps to trigger issue
   - Sample data if applicable

## Additional Resources

- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Web Vitals](https://web.dev/vitals/)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [@tanstack/react-virtual Documentation](https://tanstack.com/virtual/latest)

## Example: Complete Test Session

```javascript
// 1. Import utilities
import { runAllPerformanceTests, exportTestResults } from '@/lib/performance/runPerformanceTests';

// 2. Define test configurations
const configs = [
  {
    name: 'VirtualJobList',
    itemCounts: [100, 500, 1000, 5000],
    testVirtualized: true,
    testNonVirtualized: true,
    devices: ['desktop', 'mobile'],
    renderFn: (count) => setJobCount(count),
    getScrollElement: () => document.querySelector('[data-testid="virtual-job-list"]'),
  },
];

// 3. Run tests
console.log('Starting performance tests...');
const { results, comparisons, report } = await runAllPerformanceTests(configs);

// 4. Review results
console.log(report);

// 5. Export for documentation
exportTestResults(results, report);

// 6. Check for failures
const failures = results.filter(r => !r.passed);
if (failures.length > 0) {
  console.error('Performance tests failed:', failures);
} else {
  console.log('✅ All performance tests passed!');
}
```

## Conclusion

Regular performance testing ensures your virtualized components maintain optimal performance across devices and dataset sizes. Use this guide to establish performance baselines, detect regressions, and validate optimizations.
