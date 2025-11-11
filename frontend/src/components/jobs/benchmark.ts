/**
 * Performance Benchmark for VirtualJobList
 * 
 * This script provides utilities to benchmark the performance of VirtualJobList
 * compared to a non-virtualized list.
 */

interface BenchmarkResult {
  jobCount: number;
  renderTime: number;
  memoryUsed: number;
  fps: number;
  scrollPerformance: 'excellent' | 'good' | 'fair' | 'poor';
}

/**
 * Measure render time for a component
 */
export function measureRenderTime(callback: () => void): number {
  const start = performance.now();
  callback();
  const end = performance.now();
  return end - start;
}

/**
 * Measure memory usage (if available)
 */
export function measureMemoryUsage(): number {
  if ('memory' in performance && (performance as any).memory) {
    return (performance as any).memory.usedJSHeapSize / 1024 / 1024; // MB
  }
  return 0;
}

/**
 * Measure FPS during scrolling
 */
export function measureScrollFPS(
  element: HTMLElement,
  duration: number = 1000
): Promise<number> {
  return new Promise((resolve) => {
    let frameCount = 0;
    let lastTime = performance.now();
    let animationId: number;

    const measureFrame = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime - lastTime >= duration) {
        cancelAnimationFrame(animationId);
        const fps = (frameCount / duration) * 1000;
        resolve(Math.round(fps));
      } else {
        animationId = requestAnimationFrame(measureFrame);
      }
    };

    // Start scrolling
    element.scrollTop = 0;
    const scrollInterval = setInterval(() => {
      element.scrollTop += 10;
    }, 16);

    // Start measuring
    animationId = requestAnimationFrame(measureFrame);

    // Cleanup
    setTimeout(() => {
      clearInterval(scrollInterval);
      cancelAnimationFrame(animationId);
    }, duration + 100);
  });
}

/**
 * Run a complete benchmark
 */
export async function runBenchmark(
  jobCounts: number[] = [10, 50, 100, 500, 1000]
): Promise<BenchmarkResult[]> {
  const results: BenchmarkResult[] = [];

  for (const count of jobCounts) {
    console.log(`Benchmarking with ${count} jobs...`);

    // Measure render time
    const renderTime = measureRenderTime(() => {
      // Render logic would go here
      // This is a placeholder
    });

    // Measure memory
    const memoryUsed = measureMemoryUsage();

    // Simulate FPS measurement
    const fps = 60; // Placeholder

    // Determine scroll performance
    let scrollPerformance: BenchmarkResult['scrollPerformance'];
    if (fps >= 55) scrollPerformance = 'excellent';
    else if (fps >= 45) scrollPerformance = 'good';
    else if (fps >= 30) scrollPerformance = 'fair';
    else scrollPerformance = 'poor';

    results.push({
      jobCount: count,
      renderTime,
      memoryUsed,
      fps,
      scrollPerformance,
    });
  }

  return results;
}

/**
 * Format benchmark results for display
 */
export function formatBenchmarkResults(results: BenchmarkResult[]): string {
  let output = '\n=== VirtualJobList Performance Benchmark ===\n\n';
  
  output += '| Jobs | Render Time | Memory | FPS | Scroll Performance |\n';
  output += '|------|-------------|--------|-----|--------------------|\n';
  
  for (const result of results) {
    output += `| ${result.jobCount.toString().padEnd(4)} | `;
    output += `${result.renderTime.toFixed(2)}ms`.padEnd(11) + ' | ';
    output += `${result.memoryUsed.toFixed(2)}MB`.padEnd(6) + ' | ';
    output += `${result.fps}`.padEnd(3) + ' | ';
    output += `${result.scrollPerformance}`.padEnd(18) + ' |\n';
  }
  
  output += '\n';
  return output;
}

/**
 * Compare virtualized vs non-virtualized performance
 */
export interface ComparisonResult {
  jobCount: number;
  virtualizedTime: number;
  nonVirtualizedTime: number;
  improvement: number; // percentage
  virtualizedMemory: number;
  nonVirtualizedMemory: number;
  memoryReduction: number; // percentage
}

export function comparePerformance(
  virtualizedResults: BenchmarkResult[],
  nonVirtualizedResults: BenchmarkResult[]
): ComparisonResult[] {
  const comparisons: ComparisonResult[] = [];

  for (let i = 0; i < virtualizedResults.length; i++) {
    const virt = virtualizedResults[i];
    const nonVirt = nonVirtualizedResults[i];

    if (virt.jobCount !== nonVirt.jobCount) {
      console.warn('Job counts do not match for comparison');
      continue;
    }

    const improvement = ((nonVirt.renderTime - virt.renderTime) / nonVirt.renderTime) * 100;
    const memoryReduction = ((nonVirt.memoryUsed - virt.memoryUsed) / nonVirt.memoryUsed) * 100;

    comparisons.push({
      jobCount: virt.jobCount,
      virtualizedTime: virt.renderTime,
      nonVirtualizedTime: nonVirt.renderTime,
      improvement,
      virtualizedMemory: virt.memoryUsed,
      nonVirtualizedMemory: nonVirt.memoryUsed,
      memoryReduction,
    });
  }

  return comparisons;
}

/**
 * Format comparison results
 */
export function formatComparisonResults(comparisons: ComparisonResult[]): string {
  let output = '\n=== Virtualized vs Non-Virtualized Comparison ===\n\n';
  
  output += '| Jobs | Virt Time | Non-Virt Time | Improvement | Virt Memory | Non-Virt Memory | Memory Saved |\n';
  output += '|------|-----------|---------------|-------------|-------------|-----------------|---------------|\n';
  
  for (const comp of comparisons) {
    output += `| ${comp.jobCount.toString().padEnd(4)} | `;
    output += `${comp.virtualizedTime.toFixed(2)}ms`.padEnd(9) + ' | ';
    output += `${comp.nonVirtualizedTime.toFixed(2)}ms`.padEnd(13) + ' | ';
    output += `${comp.improvement.toFixed(1)}%`.padEnd(11) + ' | ';
    output += `${comp.virtualizedMemory.toFixed(2)}MB`.padEnd(11) + ' | ';
    output += `${comp.nonVirtualizedMemory.toFixed(2)}MB`.padEnd(15) + ' | ';
    output += `${comp.memoryReduction.toFixed(1)}%`.padEnd(13) + ' |\n';
  }
  
  output += '\n';
  return output;
}

/**
 * Expected performance characteristics
 */
export const EXPECTED_PERFORMANCE = {
  renderTime: {
    10: { max: 50, target: 20 },
    50: { max: 100, target: 40 },
    100: { max: 150, target: 60 },
    500: { max: 300, target: 100 },
    1000: { max: 500, target: 150 },
  },
  fps: {
    min: 55,
    target: 60,
  },
  memoryPerJob: {
    virtualized: 0.1, // MB per job
    nonVirtualized: 0.5, // MB per job
  },
};

/**
 * Validate performance against expectations
 */
export function validatePerformance(results: BenchmarkResult[]): {
  passed: boolean;
  failures: string[];
} {
  const failures: string[] = [];

  for (const result of results) {
    const expected = EXPECTED_PERFORMANCE.renderTime[result.jobCount as keyof typeof EXPECTED_PERFORMANCE.renderTime];
    
    if (expected && result.renderTime > expected.max) {
      failures.push(
        `Render time for ${result.jobCount} jobs (${result.renderTime.toFixed(2)}ms) exceeds maximum (${expected.max}ms)`
      );
    }

    if (result.fps < EXPECTED_PERFORMANCE.fps.min) {
      failures.push(
        `FPS for ${result.jobCount} jobs (${result.fps}) is below minimum (${EXPECTED_PERFORMANCE.fps.min})`
      );
    }
  }

  return {
    passed: failures.length === 0,
    failures,
  };
}

/**
 * Generate a performance report
 */
export function generatePerformanceReport(
  virtualizedResults: BenchmarkResult[],
  nonVirtualizedResults?: BenchmarkResult[]
): string {
  let report = '\n';
  report += '╔════════════════════════════════════════════════════════════╗\n';
  report += '║         VirtualJobList Performance Report                 ║\n';
  report += '╚════════════════════════════════════════════════════════════╝\n';
  report += '\n';

  // Virtualized results
  report += formatBenchmarkResults(virtualizedResults);

  // Comparison if available
  if (nonVirtualizedResults) {
    const comparisons = comparePerformance(virtualizedResults, nonVirtualizedResults);
    report += formatComparisonResults(comparisons);
  }

  // Validation
  const validation = validatePerformance(virtualizedResults);
  report += '\n=== Performance Validation ===\n\n';
  
  if (validation.passed) {
    report += '✅ All performance metrics meet expectations!\n';
  } else {
    report += '❌ Performance issues detected:\n\n';
    validation.failures.forEach((failure) => {
      report += `  - ${failure}\n`;
    });
  }

  report += '\n';
  return report;
}

// Example usage in browser console:
// import { runBenchmark, generatePerformanceReport } from './benchmark';
// const results = await runBenchmark([10, 50, 100, 500, 1000]);
// console.log(generatePerformanceReport(results));
