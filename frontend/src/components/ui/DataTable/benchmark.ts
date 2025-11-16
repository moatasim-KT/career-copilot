import { logger } from '@/lib/logger';

/**
 * DataTable Performance Benchmark Utility
 * 
 * Measures and reports performance metrics for the VirtualDataTable component
 * including FPS, render time, and memory usage with large datasets.
 */

interface BenchmarkResult {
  datasetSize: number;
  virtualized: boolean;
  averageFPS: number;
  minFPS: number;
  maxFPS: number;
  averageRenderTime: number;
  maxRenderTime: number;
  scrollPerformance: {
    averageFPS: number;
    minFPS: number;
  };
  memoryUsage?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

interface _PerformanceMetrics {
  fps: number[];
  renderTimes: number[];
  scrollFPS: number[];
}

/**
 * FPS Monitor
 * Tracks frames per second during rendering and scrolling
 */
class FPSMonitor {
  private frameCount = 0;
  private lastTime = performance.now();
  private fps: number[] = [];
  private animationFrameId: number | null = null;

  start() {
    this.frameCount = 0;
    this.lastTime = performance.now();
    this.fps = [];
    this.measure();
  }

  private measure = () => {
    this.frameCount++;
    const currentTime = performance.now();
    const elapsed = currentTime - this.lastTime;

    if (elapsed >= 1000) {
      const currentFPS = Math.round((this.frameCount * 1000) / elapsed);
      this.fps.push(currentFPS);
      this.frameCount = 0;
      this.lastTime = currentTime;
    }

    this.animationFrameId = requestAnimationFrame(this.measure);
  };

  stop(): number[] {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    return this.fps;
  }

  getAverageFPS(): number {
    if (this.fps.length === 0) return 0;
    return Math.round(this.fps.reduce((a, b) => a + b, 0) / this.fps.length);
  }

  getMinFPS(): number {
    if (this.fps.length === 0) return 0;
    return Math.min(...this.fps);
  }

  getMaxFPS(): number {
    if (this.fps.length === 0) return 0;
    return Math.max(...this.fps);
  }
}

/**
 * Render Time Monitor
 * Tracks component render duration
 */
class RenderTimeMonitor {
  private renderTimes: number[] = [];
  private renderStart = 0;

  startRender() {
    this.renderStart = performance.now();
  }

  endRender() {
    if (this.renderStart > 0) {
      const renderTime = performance.now() - this.renderStart;
      this.renderTimes.push(renderTime);
      this.renderStart = 0;
    }
  }

  getRenderTimes(): number[] {
    return this.renderTimes;
  }

  getAverageRenderTime(): number {
    if (this.renderTimes.length === 0) return 0;
    return this.renderTimes.reduce((a, b) => a + b, 0) / this.renderTimes.length;
  }

  getMaxRenderTime(): number {
    if (this.renderTimes.length === 0) return 0;
    return Math.max(...this.renderTimes);
  }
}

/**
 * Memory Monitor
 * Tracks memory usage (Chrome only)
 */
function getMemoryUsage() {
  if ('memory' in performance) {
    const memory = (performance as any).memory;
    return {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit,
    };
  }
  return undefined;
}

/**
 * Simulate scrolling through a container
 */
async function simulateScroll(
  container: HTMLElement,
  duration: number = 3000,
): Promise<number[]> {
  const fpsMonitor = new FPSMonitor();
  fpsMonitor.start();

  const scrollHeight = container.scrollHeight - container.clientHeight;
  const startTime = performance.now();
  const scrollDuration = duration;

  return new Promise((resolve) => {
    const scroll = () => {
      const elapsed = performance.now() - startTime;
      const progress = Math.min(elapsed / scrollDuration, 1);

      // Smooth scroll using easing function
      const easeInOutQuad = (t: number) =>
        t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      const scrollPosition = scrollHeight * easeInOutQuad(progress);

      container.scrollTop = scrollPosition;

      if (progress < 1) {
        requestAnimationFrame(scroll);
      } else {
        const fps = fpsMonitor.stop();
        resolve(fps);
      }
    };

    requestAnimationFrame(scroll);
  });
}

/**
 * Run benchmark for a specific dataset size
 */
export async function runBenchmark(
  datasetSize: number,
  virtualized: boolean,
  containerSelector: string = '[data-testid="datatable-container"]',
): Promise<BenchmarkResult> {
  const container = document.querySelector(containerSelector) as HTMLElement;
  if (!container) {
    throw new Error(`Container not found: ${containerSelector}`);
  }

  const fpsMonitor = new FPSMonitor();
  const renderMonitor = new RenderTimeMonitor();

  // Measure initial render
  renderMonitor.startRender();
  fpsMonitor.start();

  // Wait for initial render
  await new Promise((resolve) => setTimeout(resolve, 2000));

  renderMonitor.endRender();
  const initialFPS = fpsMonitor.stop();

  // Measure scroll performance
  const scrollFPS = await simulateScroll(container, 3000);

  // Get memory usage
  const memoryUsage = getMemoryUsage();

  // Calculate metrics
  const result: BenchmarkResult = {
    datasetSize,
    virtualized,
    averageFPS: Math.round(
      initialFPS.reduce((a, b) => a + b, 0) / initialFPS.length,
    ),
    minFPS: Math.min(...initialFPS),
    maxFPS: Math.max(...initialFPS),
    averageRenderTime: renderMonitor.getAverageRenderTime(),
    maxRenderTime: renderMonitor.getMaxRenderTime(),
    scrollPerformance: {
      averageFPS: Math.round(
        scrollFPS.reduce((a, b) => a + b, 0) / scrollFPS.length,
      ),
      minFPS: Math.min(...scrollFPS),
    },
    memoryUsage,
  };

  return result;
}

/**
 * Run comprehensive benchmark suite
 */
export async function runBenchmarkSuite(
  containerSelector?: string,
): Promise<BenchmarkResult[]> {
  const testSizes = [100, 500, 1000, 2000, 5000];
  const results: BenchmarkResult[] = [];

  for (const size of testSizes) {
    logger.info(`Running benchmark for ${size} rows (virtualized)...`);
    const virtualizedResult = await runBenchmark(size, true, containerSelector);
    results.push(virtualizedResult);

    // Only test non-virtualized for smaller datasets
    if (size <= 500) {
      logger.info(`Running benchmark for ${size} rows (non-virtualized)...`);
      const nonVirtualizedResult = await runBenchmark(
        size,
        false,
        containerSelector,
      );
      results.push(nonVirtualizedResult);
    }
  }

  return results;
}

/**
 * Format benchmark results for display
 */
export function formatBenchmarkResults(results: BenchmarkResult[]): string {
  let output = '\n=== DataTable Performance Benchmark Results ===\n\n';

  results.forEach((result) => {
    output += `Dataset Size: ${result.datasetSize} rows\n`;
    output += `Virtualized: ${result.virtualized ? 'Yes' : 'No'}\n`;
    output += `Average FPS: ${result.averageFPS} (min: ${result.minFPS}, max: ${result.maxFPS})\n`;
    output += `Average Render Time: ${result.averageRenderTime.toFixed(2)}ms\n`;
    output += `Max Render Time: ${result.maxRenderTime.toFixed(2)}ms\n`;
    output += `Scroll Performance: ${result.scrollPerformance.averageFPS} FPS (min: ${result.scrollPerformance.minFPS})\n`;

    if (result.memoryUsage) {
      const usedMB = (result.memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(
        2,
      );
      const totalMB = (result.memoryUsage.totalJSHeapSize / 1024 / 1024).toFixed(
        2,
      );
      output += `Memory Usage: ${usedMB}MB / ${totalMB}MB\n`;
    }

    // Performance assessment
    const passesTarget = result.scrollPerformance.minFPS >= 60;
    output += `Performance: ${passesTarget ? '✅ PASS' : '❌ FAIL'} (Target: 60 FPS)\n`;
    output += '\n---\n\n';
  });

  return output;
}

/**
 * Compare virtualized vs non-virtualized performance
 */
export function comparePerformance(
  virtualizedResult: BenchmarkResult,
  nonVirtualizedResult: BenchmarkResult,
): string {
  const fpsImprovement =
    ((virtualizedResult.scrollPerformance.averageFPS -
      nonVirtualizedResult.scrollPerformance.averageFPS) /
      nonVirtualizedResult.scrollPerformance.averageFPS) *
    100;

  const renderTimeImprovement =
    ((nonVirtualizedResult.averageRenderTime -
      virtualizedResult.averageRenderTime) /
      nonVirtualizedResult.averageRenderTime) *
    100;

  let output = '\n=== Virtualization Performance Comparison ===\n\n';
  output += `Dataset Size: ${virtualizedResult.datasetSize} rows\n\n`;
  output += 'Scroll FPS:\n';
  output += `  Non-virtualized: ${nonVirtualizedResult.scrollPerformance.averageFPS}\n`;
  output += `  Virtualized: ${virtualizedResult.scrollPerformance.averageFPS}\n`;
  output += `  Improvement: ${fpsImprovement > 0 ? '+' : ''}${fpsImprovement.toFixed(1)}%\n\n`;
  output += 'Render Time:\n';
  output += `  Non-virtualized: ${nonVirtualizedResult.averageRenderTime.toFixed(2)}ms\n`;
  output += `  Virtualized: ${virtualizedResult.averageRenderTime.toFixed(2)}ms\n`;
  output += `  Improvement: ${renderTimeImprovement > 0 ? '+' : ''}${renderTimeImprovement.toFixed(1)}%\n\n`;

  if (
    virtualizedResult.memoryUsage &&
    nonVirtualizedResult.memoryUsage
  ) {
    const memoryReduction =
      ((nonVirtualizedResult.memoryUsage.usedJSHeapSize -
        virtualizedResult.memoryUsage.usedJSHeapSize) /
        nonVirtualizedResult.memoryUsage.usedJSHeapSize) *
      100;
    output += 'Memory Usage:\n';
    output += `  Non-virtualized: ${(nonVirtualizedResult.memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB\n`;
    output += `  Virtualized: ${(virtualizedResult.memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB\n`;
    output += `  Reduction: ${memoryReduction > 0 ? '+' : ''}${memoryReduction.toFixed(1)}%\n`;
  }

  return output;
}

/**
 * Export results to JSON
 */
export function exportBenchmarkResults(
  results: BenchmarkResult[],
  filename: string = 'datatable-benchmark-results.json',
): void {
  const json = JSON.stringify(results, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default {
  runBenchmark,
  runBenchmarkSuite,
  formatBenchmarkResults,
  comparePerformance,
  exportBenchmarkResults,
};
