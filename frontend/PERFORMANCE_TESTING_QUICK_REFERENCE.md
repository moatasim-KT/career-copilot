# Performance Testing Quick Reference

Quick reference for running performance tests on virtualized components.

## Quick Test (Browser Console)

```javascript
import { quickTest } from '@/lib/performance/runPerformanceTests';

// Test with 1000 items
await quickTest(
  'VirtualJobList',
  1000,
  () => {
    // Your render logic
  },
  () => document.querySelector('[data-testid="virtual-job-list"]')
);
```

## Run All Tests

```javascript
import { runAllPerformanceTests } from '@/lib/performance/runPerformanceTests';

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

const { results, report } = await runAllPerformanceTests(configs);
console.log(report);
```

## Automated Tests

```bash
# Run performance tests
npm run test -- src/__tests__/performance/virtualization.performance.test.ts

# Run specific test
npm run test -- src/__tests__/performance/virtualization.performance.test.ts -t "VirtualJobList"
```

## Device Profiles

```javascript
import { DEVICE_PROFILES } from '@/lib/performance/performanceTesting';

// Available profiles:
DEVICE_PROFILES.desktop  // 1x CPU (no throttling)
DEVICE_PROFILES.laptop   // 2x CPU throttling
DEVICE_PROFILES.tablet   // 3x CPU throttling
DEVICE_PROFILES.mobile   // 4x CPU throttling
```

## Performance Targets

| Metric | Target | Maximum |
|--------|--------|---------|
| Render Time | < 200ms | < 500ms |
| Average FPS | 60 | 55 minimum |
| Jank | < 5% | < 10% |
| Memory | < 80% heap | < 90% heap |

## Export Results

```javascript
import { exportResults } from '@/lib/performance/performanceTesting';

// Export to JSON
exportResults(results, 'my-performance-test.json');

// Export report to Markdown
import { exportTestResults } from '@/lib/performance/runPerformanceTests';
exportTestResults(results, report);
```

## Interpreting Results

### ✅ PASS Criteria
- Render time < 500ms
- Min FPS ≥ 55
- Jank < 10% of frames
- Memory < 90% of heap limit

### ❌ FAIL Indicators
- Render time > 500ms
- Min FPS < 55
- High jank (> 10%)
- Memory near limit (> 90%)

## Common Issues

### Low FPS
- Check virtualization is enabled
- Verify overscan setting (5-10)
- Optimize item rendering
- Use React.memo()

### High Render Time
- Use useMemo() for calculations
- Defer non-critical rendering
- Optimize data structures

### High Memory
- Check for memory leaks
- Reduce cache size
- Clear unused data

## More Information

See `PERFORMANCE_TESTING_GUIDE.md` for complete documentation.
