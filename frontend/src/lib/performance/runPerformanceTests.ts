/**
 * Performance Test Runner
 * 
 * Orchestrates comprehensive performance testing for all virtualized components.
 * Run this in the browser console or as part of a test suite.
 */

import { logger } from '@/lib/logger';

import {
  runBenchmarkSuite,
  comparePerformance,
  generatePerformanceReport,
  exportResults,
  saveResults,
  DEVICE_PROFILES,
  type BenchmarkResult,
  type ComparisonResult,
} from './performanceTesting';


/**
 * Test configuration
 */
export interface TestConfig {
  name: string;
  itemCounts: number[];
  testVirtualized: boolean;
  testNonVirtualized: boolean;
  devices: string[]; // Keys from DEVICE_PROFILES
  renderFn: (count: number) => void | Promise<void>;
  getScrollElement: () => HTMLElement | null;
}

/**
 * Run all performance tests
 */
export async function runAllPerformanceTests(
  configs: TestConfig[],
): Promise<{
  results: BenchmarkResult[];
  comparisons: ComparisonResult[];
  report: string;
}> {
  logger.info('🚀 Starting comprehensive performance tests...\n');

  const allResults: BenchmarkResult[] = [];
  const allComparisons: ComparisonResult[] = [];

  for (const config of configs) {
    logger.info(`\n📊 Testing: ${config.name}`);
    logger.info('─'.repeat(60));

    const devices = config.devices.map(key => DEVICE_PROFILES[key]);

    // Test virtualized version
    let virtualizedResults: BenchmarkResult[] = [];
    if (config.testVirtualized) {
      logger.info('\n✨ Testing virtualized implementation...');
      virtualizedResults = await runBenchmarkSuite(
        config.name,
        config.itemCounts,
        true,
        config.renderFn,
        config.getScrollElement,
        devices,
      );
      allResults.push(...virtualizedResults);
    }

    // Test non-virtualized version (only for smaller datasets)
    let nonVirtualizedResults: BenchmarkResult[] = [];
    if (config.testNonVirtualized) {
      const smallItemCounts = config.itemCounts.filter(count => count <= 500);
      if (smallItemCounts.length > 0) {
        logger.info('\n📦 Testing non-virtualized implementation...');
        nonVirtualizedResults = await runBenchmarkSuite(
          config.name,
          smallItemCounts,
          false,
          config.renderFn,
          config.getScrollElement,
          devices,
        );
        allResults.push(...nonVirtualizedResults);
      }
    }

    // Compare results
    if (virtualizedResults.length > 0 && nonVirtualizedResults.length > 0) {
      logger.info('\n🔍 Comparing virtualized vs non-virtualized...');

      for (const virtResult of virtualizedResults) {
        const nonVirtResult = nonVirtualizedResults.find(
          r => r.itemCount === virtResult.itemCount && r.device === virtResult.device,
        );

        if (nonVirtResult) {
          const comparison = comparePerformance(virtResult, nonVirtResult);
          allComparisons.push(comparison);
        }
      }
    }

    logger.info(`\n✅ Completed testing: ${config.name}`);
  }

  // Generate comprehensive report
  logger.info('\n📝 Generating performance report...');
  const report = generatePerformanceReport(allResults, allComparisons);

  logger.info(`\n${report}`);

  // Save results
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  saveResults(`performance-test-${timestamp}`, allResults);

  logger.info('\n✨ Performance testing complete!');

  return {
    results: allResults,
    comparisons: allComparisons,
    report,
  };
}

/**
 * Export test results to file
 */
export function exportTestResults(
  results: BenchmarkResult[],
  report: string,
): void {
  // Export JSON results
  exportResults(results, `performance-results-${Date.now()}.json`);

  // Export markdown report
  const blob = new Blob([report], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `performance-report-${Date.now()}.md`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  logger.info('📁 Results exported successfully!');
}

/**
 * Quick test for a single component
 */
export async function quickTest(
  name: string,
  itemCount: number,
  renderFn: () => void | Promise<void>,
  getScrollElement: () => HTMLElement | null,
): Promise<void> {
  const config: TestConfig = {
    name,
    itemCounts: [itemCount],
    testVirtualized: true,
    testNonVirtualized: false,
    devices: ['desktop'],
    renderFn: () => renderFn(),
    getScrollElement,
  };

  const { report } = await runAllPerformanceTests([config]);
  logger.info(report);
}

/**
 * Example usage in browser console:
 * 
 * ```javascript
 * import { runAllPerformanceTests } from './runPerformanceTests';
 * 
 * const configs = [
 *   {
 *     name: 'VirtualJobList',
 *     itemCounts: [100, 500, 1000, 5000],
 *     testVirtualized: true,
 *     testNonVirtualized: true,
 *     devices: ['desktop', 'mobile'],
 *     renderFn: (count) => {
 *       // Render component with count items
 *     },
 *     getScrollElement: () => document.querySelector('.virtual-list'),
 *   },
 * ];
 * 
 * const { results, report } = await runAllPerformanceTests(configs);
 * logger.info(report);
 * ```
 */
