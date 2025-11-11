/**
 * Comprehensive Performance Testing Suite
 * 
 * Provides utilities for benchmarking virtualized components including:
 * - Render time measurement
 * - FPS monitoring during scrolling
 * - Memory usage tracking
 * - Device simulation (lower-end devices)
 * - Performance comparison and reporting
 */

export interface DeviceProfile {
  name: string;
  cpuSlowdown: number; // Multiplier for CPU throttling (1 = no throttling, 4 = 4x slower)
  memoryLimit?: number; // MB
  description: string;
}

export const DEVICE_PROFILES: Record<string, DeviceProfile> = {
  desktop: {
    name: 'Desktop (High-end)',
    cpuSlowdown: 1,
    description: 'Modern desktop with fast CPU',
  },
  laptop: {
    name: 'Laptop (Mid-range)',
    cpuSlowdown: 2,
    description: 'Average laptop with moderate CPU',
  },
  tablet: {
    name: 'Tablet',
    cpuSlowdown: 3,
    description: 'iPad or Android tablet',
  },
  mobile: {
    name: 'Mobile (Low-end)',
    cpuSlowdown: 4,
    memoryLimit: 512,
    description: 'Budget smartphone with limited resources',
  },
};

export interface PerformanceMetrics {
  renderTime: number; // milliseconds
  fps: {
    average: number;
    min: number;
    max: number;
    samples: number[];
  };
  memory: {
    used: number; // MB
    total: number; // MB
    limit: number; // MB
  } | null;
  scrollPerformance: {
    averageFPS: number;
    minFPS: number;
    maxFPS: number;
    jank: number; // Number of frames below 60fps
    samples: number[];
  };
}

export interface BenchmarkResult {
  testName: string;
  itemCount: number;
  virtualized: boolean;
  device: string;
  timestamp: Date;
  metrics: PerformanceMetrics;
  passed: boolean;
  issues: string[];
}

export interface ComparisonResult {
  itemCount: number;
  virtualizedMetrics: PerformanceMetrics;
  nonVirtualizedMetrics: PerformanceMetrics;
  improvements: {
    renderTime: number; // percentage
    fps: number; // percentage
    memory: number; // percentage
  };
}

/**
 * FPS Monitor - Tracks frames per second
 */
class FPSMonitor {
  private frameCount = 0;
  private lastTime = performance.now();
  private samples: number[] = [];
  private animationFrameId: number | null = null;
  private isRunning = false;

  start(): void {
    if (this.isRunning) return;
    
    this.frameCount = 0;
    this.lastTime = performance.now();
    this.samples = [];
    this.isRunning = true;
    this.measure();
  }

  private measure = (): void => {
    if (!this.isRunning) return;

    this.frameCount++;
    const currentTime = performance.now();
    const elapsed = currentTime - this.lastTime;

    // Sample FPS every second
    if (elapsed >= 1000) {
      const fps = Math.round((this.frameCount * 1000) / elapsed);
      this.samples.push(fps);
      this.frameCount = 0;
      this.lastTime = currentTime;
    }

    this.animationFrameId = requestAnimationFrame(this.measure);
  };

  stop(): number[] {
    this.isRunning = false;
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    return this.samples;
  }

  getMetrics() {
    if (this.samples.length === 0) {
      return { average: 0, min: 0, max: 0 };
    }
    return {
      average: Math.round(this.samples.reduce((a, b) => a + b, 0) / this.samples.length),
      min: Math.min(...this.samples),
      max: Math.max(...this.samples),
    };
  }
}

/**
 * Memory Monitor - Tracks memory usage (Chrome only)
 */
export function getMemoryUsage(): PerformanceMetrics['memory'] {
  if ('memory' in performance) {
    const memory = (performance as any).memory;
    return {
      used: memory.usedJSHeapSize / 1024 / 1024,
      total: memory.totalJSHeapSize / 1024 / 1024,
      limit: memory.jsHeapSizeLimit / 1024 / 1024,
    };
  }
  return null;
}

/**
 * Measure render time
 */
export async function measureRenderTime(
  renderFn: () => void | Promise<void>,
  iterations: number = 3
): Promise<number> {
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    // Force garbage collection if available (Chrome DevTools)
    if ('gc' in window && typeof (window as any).gc === 'function') {
      (window as any).gc();
    }

    const start = performance.now();
    await renderFn();
    const end = performance.now();
    times.push(end - start);

    // Allow browser to settle between iterations
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  // Return median time (more stable than average)
  times.sort((a, b) => a - b);
  return times[Math.floor(times.length / 2)];
}

/**
 * Measure scroll performance with FPS tracking
 */
export async function measureScrollPerformance(
  element: HTMLElement,
  duration: number = 3000
): Promise<PerformanceMetrics['scrollPerformance']> {
  const fpsMonitor = new FPSMonitor();
  const scrollHeight = element.scrollHeight - element.clientHeight;
  
  if (scrollHeight <= 0) {
    return {
      averageFPS: 60,
      minFPS: 60,
      maxFPS: 60,
      jank: 0,
      samples: [60],
    };
  }

  fpsMonitor.start();

  return new Promise((resolve) => {
    const startTime = performance.now();
    let lastFrameTime = startTime;
    const frameTimes: number[] = [];

    const scroll = () => {
      const currentTime = performance.now();
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Track frame time
      const frameTime = currentTime - lastFrameTime;
      frameTimes.push(frameTime);
      lastFrameTime = currentTime;

      // Smooth scroll with easing
      const easeInOutCubic = (t: number) =>
        t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      
      element.scrollTop = scrollHeight * easeInOutCubic(progress);

      if (progress < 1) {
        requestAnimationFrame(scroll);
      } else {
        const samples = fpsMonitor.stop();
        const metrics = fpsMonitor.getMetrics();
        
        // Calculate jank (frames that took longer than 16.67ms = below 60fps)
        const jank = frameTimes.filter(time => time > 16.67).length;

        resolve({
          averageFPS: metrics.average,
          minFPS: metrics.min,
          maxFPS: metrics.max,
          jank,
          samples,
        });
      }
    };

    requestAnimationFrame(scroll);
  });
}

/**
 * Simulate CPU throttling for device testing
 */
export function simulateCPUThrottling(slowdownFactor: number): () => void {
  if (slowdownFactor <= 1) {
    return () => {}; // No throttling needed
  }

  // Busy-wait to simulate slower CPU
  const busyWait = (ms: number) => {
    const start = performance.now();
    while (performance.now() - start < ms) {
      // Busy loop
    }
  };

  // Inject delays into requestAnimationFrame
  const originalRAF = window.requestAnimationFrame;
  window.requestAnimationFrame = (callback: FrameRequestCallback) => {
    return originalRAF((time: number) => {
      busyWait((slowdownFactor - 1) * 2); // Add delay proportional to slowdown
      callback(time);
    });
  };

  // Return cleanup function
  return () => {
    window.requestAnimationFrame = originalRAF;
  };
}

/**
 * Run comprehensive benchmark for a component
 */
export async function runBenchmark(
  testName: string,
  itemCount: number,
  virtualized: boolean,
  renderFn: () => void | Promise<void>,
  getScrollElement: () => HTMLElement | null,
  deviceProfile: DeviceProfile = DEVICE_PROFILES.desktop
): Promise<BenchmarkResult> {
  console.log(`Running benchmark: ${testName} (${itemCount} items, ${deviceProfile.name})`);

  // Apply CPU throttling
  const cleanupThrottling = simulateCPUThrottling(deviceProfile.cpuSlowdown);

  try {
    // Measure initial render
    const renderTime = await measureRenderTime(renderFn, 3);

    // Wait for render to stabilize
    await new Promise(resolve => setTimeout(resolve, 500));

    // Measure initial FPS
    const fpsMonitor = new FPSMonitor();
    fpsMonitor.start();
    await new Promise(resolve => setTimeout(resolve, 2000));
    const fpsSamples = fpsMonitor.stop();
    const fpsMetrics = fpsMonitor.getMetrics();

    // Measure scroll performance
    const scrollElement = getScrollElement();
    let scrollPerformance: PerformanceMetrics['scrollPerformance'];

    if (scrollElement) {
      scrollPerformance = await measureScrollPerformance(scrollElement, 3000);
    } else {
      scrollPerformance = {
        averageFPS: 60,
        minFPS: 60,
        maxFPS: 60,
        jank: 0,
        samples: [60],
      };
    }

    // Measure memory
    const memory = getMemoryUsage();

    // Validate performance
    const issues: string[] = [];
    let passed = true;

    if (renderTime > 500) {
      issues.push(`Render time (${renderTime.toFixed(2)}ms) exceeds 500ms threshold`);
      passed = false;
    }

    if (scrollPerformance.minFPS < 55) {
      issues.push(`Minimum FPS (${scrollPerformance.minFPS}) is below 55 target`);
      passed = false;
    }

    if (scrollPerformance.jank > scrollPerformance.samples.length * 0.1) {
      issues.push(`High jank detected: ${scrollPerformance.jank} frames dropped`);
      passed = false;
    }

    if (memory && memory.used > memory.limit * 0.9) {
      issues.push(`Memory usage (${memory.used.toFixed(2)}MB) is near limit`);
      passed = false;
    }

    return {
      testName,
      itemCount,
      virtualized,
      device: deviceProfile.name,
      timestamp: new Date(),
      metrics: {
        renderTime,
        fps: {
          average: fpsMetrics.average,
          min: fpsMetrics.min,
          max: fpsMetrics.max,
          samples: fpsSamples,
        },
        memory,
        scrollPerformance,
      },
      passed,
      issues,
    };
  } finally {
    // Cleanup CPU throttling
    cleanupThrottling();
  }
}

/**
 * Run benchmark suite across multiple item counts and devices
 */
export async function runBenchmarkSuite(
  testName: string,
  itemCounts: number[],
  virtualized: boolean,
  renderFn: (count: number) => void | Promise<void>,
  getScrollElement: () => HTMLElement | null,
  devices: DeviceProfile[] = [DEVICE_PROFILES.desktop, DEVICE_PROFILES.mobile]
): Promise<BenchmarkResult[]> {
  const results: BenchmarkResult[] = [];

  for (const device of devices) {
    for (const count of itemCounts) {
      const result = await runBenchmark(
        testName,
        count,
        virtualized,
        () => renderFn(count),
        getScrollElement,
        device
      );
      results.push(result);

      // Pause between tests
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  return results;
}

/**
 * Compare virtualized vs non-virtualized performance
 */
export function comparePerformance(
  virtualizedResult: BenchmarkResult,
  nonVirtualizedResult: BenchmarkResult
): ComparisonResult {
  const renderTimeImprovement =
    ((nonVirtualizedResult.metrics.renderTime - virtualizedResult.metrics.renderTime) /
      nonVirtualizedResult.metrics.renderTime) * 100;

  const fpsImprovement =
    ((virtualizedResult.metrics.scrollPerformance.averageFPS -
      nonVirtualizedResult.metrics.scrollPerformance.averageFPS) /
      nonVirtualizedResult.metrics.scrollPerformance.averageFPS) * 100;

  let memoryImprovement = 0;
  if (
    virtualizedResult.metrics.memory &&
    nonVirtualizedResult.metrics.memory
  ) {
    memoryImprovement =
      ((nonVirtualizedResult.metrics.memory.used - virtualizedResult.metrics.memory.used) /
        nonVirtualizedResult.metrics.memory.used) * 100;
  }

  return {
    itemCount: virtualizedResult.itemCount,
    virtualizedMetrics: virtualizedResult.metrics,
    nonVirtualizedMetrics: nonVirtualizedResult.metrics,
    improvements: {
      renderTime: renderTimeImprovement,
      fps: fpsImprovement,
      memory: memoryImprovement,
    },
  };
}

/**
 * Format benchmark results as markdown table
 */
export function formatBenchmarkResults(results: BenchmarkResult[]): string {
  let output = '\n## Performance Benchmark Results\n\n';
  output += '| Test | Items | Device | Virtualized | Render (ms) | Avg FPS | Min FPS | Jank | Memory (MB) | Status |\n';
  output += '|------|-------|--------|-------------|-------------|---------|---------|------|-------------|--------|\n';

  for (const result of results) {
    const memoryStr = result.metrics.memory
      ? result.metrics.memory.used.toFixed(1)
      : 'N/A';
    const status = result.passed ? '✅ PASS' : '❌ FAIL';

    output += `| ${result.testName} | `;
    output += `${result.itemCount} | `;
    output += `${result.device} | `;
    output += `${result.virtualized ? 'Yes' : 'No'} | `;
    output += `${result.metrics.renderTime.toFixed(2)} | `;
    output += `${result.metrics.scrollPerformance.averageFPS} | `;
    output += `${result.metrics.scrollPerformance.minFPS} | `;
    output += `${result.metrics.scrollPerformance.jank} | `;
    output += `${memoryStr} | `;
    output += `${status} |\n`;
  }

  // Add issues section
  const failedResults = results.filter(r => !r.passed);
  if (failedResults.length > 0) {
    output += '\n### Issues Detected\n\n';
    for (const result of failedResults) {
      output += `**${result.testName} (${result.itemCount} items, ${result.device})**:\n`;
      for (const issue of result.issues) {
        output += `- ${issue}\n`;
      }
      output += '\n';
    }
  }

  return output;
}

/**
 * Format comparison results
 */
export function formatComparisonResults(comparisons: ComparisonResult[]): string {
  let output = '\n## Virtualized vs Non-Virtualized Comparison\n\n';
  output += '| Items | Render Time | FPS | Memory |\n';
  output += '|-------|-------------|-----|--------|\n';

  for (const comp of comparisons) {
    const renderSign = comp.improvements.renderTime > 0 ? '↓' : '↑';
    const fpsSign = comp.improvements.fps > 0 ? '↑' : '↓';
    const memorySign = comp.improvements.memory > 0 ? '↓' : '↑';

    output += `| ${comp.itemCount} | `;
    output += `${renderSign} ${Math.abs(comp.improvements.renderTime).toFixed(1)}% | `;
    output += `${fpsSign} ${Math.abs(comp.improvements.fps).toFixed(1)}% | `;
    output += `${memorySign} ${Math.abs(comp.improvements.memory).toFixed(1)}% |\n`;
  }

  output += '\n';
  output += '↓ = Improvement (lower is better for render time and memory)\n';
  output += '↑ = Improvement (higher is better for FPS)\n';

  return output;
}

/**
 * Generate comprehensive performance report
 */
export function generatePerformanceReport(
  results: BenchmarkResult[],
  comparisons?: ComparisonResult[]
): string {
  let report = '\n';
  report += '╔════════════════════════════════════════════════════════════╗\n';
  report += '║         Virtualization Performance Report                 ║\n';
  report += '╚════════════════════════════════════════════════════════════╝\n';
  report += '\n';
  report += `Generated: ${new Date().toLocaleString()}\n`;
  report += '\n';

  // Summary
  const passedCount = results.filter(r => r.passed).length;
  const totalCount = results.length;
  const passRate = ((passedCount / totalCount) * 100).toFixed(1);

  report += '### Summary\n\n';
  report += `- Total Tests: ${totalCount}\n`;
  report += `- Passed: ${passedCount}\n`;
  report += `- Failed: ${totalCount - passedCount}\n`;
  report += `- Pass Rate: ${passRate}%\n`;
  report += '\n';

  // Detailed results
  report += formatBenchmarkResults(results);

  // Comparisons
  if (comparisons && comparisons.length > 0) {
    report += formatComparisonResults(comparisons);
  }

  // Performance targets
  report += '\n### Performance Targets\n\n';
  report += '- Render Time: < 500ms\n';
  report += '- Minimum FPS: ≥ 55\n';
  report += '- Average FPS: ≥ 60\n';
  report += '- Jank: < 10% of frames\n';
  report += '- Memory: < 90% of heap limit\n';
  report += '\n';

  return report;
}

/**
 * Export results to JSON
 */
export function exportResults(
  results: BenchmarkResult[],
  filename: string = 'performance-benchmark-results.json'
): void {
  const json = JSON.stringify(results, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Save results to localStorage
 */
export function saveResults(key: string, results: BenchmarkResult[]): void {
  try {
    localStorage.setItem(key, JSON.stringify(results));
    console.log(`Results saved to localStorage: ${key}`);
  } catch (error) {
    console.error('Failed to save results:', error);
  }
}

/**
 * Load results from localStorage
 */
export function loadResults(key: string): BenchmarkResult[] | null {
  try {
    const data = localStorage.getItem(key);
    if (!data) return null;
    
    const results = JSON.parse(data);
    return results.map((r: any) => ({
      ...r,
      timestamp: new Date(r.timestamp),
    }));
  } catch (error) {
    console.error('Failed to load results:', error);
    return null;
  }
}
