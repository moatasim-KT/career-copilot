/**
 * VirtualApplicationList Performance Benchmark
 * 
 * Utilities for measuring and comparing performance of the virtualized application list.
 * Run benchmarks to ensure optimal performance with large datasets.
 */

import { Application } from '@/components/ui/ApplicationCard';
import { logger } from '@/lib/logger';

/**
 * Benchmark result interface
 */
export interface BenchmarkResult {
  testName: string;
  itemCount: number;
  renderTime: number;
  scrollTime: number;
  memoryUsed: number;
  fps: number;
  timestamp: Date;
}

/**
 * Generate mock application data for benchmarking
 */
export function generateBenchmarkApplications(count: number): Application[] {
  const statuses = ['interested', 'applied', 'interview', 'offer', 'rejected', 'accepted', 'declined'];
  const companies = ['TechCorp', 'InnovateLabs', 'DataSystems', 'CloudServices', 'AI Solutions', 'DevTools Inc'];
  const titles = ['Software Engineer', 'Senior Developer', 'Full Stack Engineer', 'Backend Developer', 'Frontend Developer', 'DevOps Engineer'];
  const locations = ['Remote', 'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA', 'Boston, MA'];

  return Array.from({ length: count }, (_, i) => {
    const daysAgo = Math.floor(Math.random() * 90);
    const appliedDate = new Date(Date.now() - daysAgo * 86400000);

    return {
      id: i + 1,
      user_id: 1,
      job_id: (i + 1) * 10,
      status: statuses[i % statuses.length],
      applied_date: appliedDate.toISOString(),
      response_date: Math.random() > 0.7 ? new Date(appliedDate.getTime() + 7 * 86400000).toISOString() : null,
      interview_date: Math.random() > 0.8 ? new Date(appliedDate.getTime() + 14 * 86400000).toISOString() : null,
      offer_date: Math.random() > 0.9 ? new Date(appliedDate.getTime() + 21 * 86400000).toISOString() : null,
      notes: Math.random() > 0.5 ? `Follow up with hiring manager. Application #${i + 1}` : null,
      interview_feedback: null,
      follow_up_date: Math.random() > 0.7 ? new Date(appliedDate.getTime() + 10 * 86400000).toISOString() : null,
      created_at: appliedDate.toISOString(),
      updated_at: new Date().toISOString(),
      job_title: `${titles[i % titles.length]} ${i + 1}`,
      company_name: companies[i % companies.length],
      job_location: locations[i % locations.length],
    };
  });
}

/**
 * Measure render time
 */
export async function measureRenderTime(
  renderFn: () => void,
  iterations: number = 5,
): Promise<number> {
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    renderFn();
    const end = performance.now();
    times.push(end - start);

    // Allow browser to settle
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Return average time
  return times.reduce((sum, time) => sum + time, 0) / times.length;
}

/**
 * Measure scroll performance (FPS)
 */
export async function measureScrollPerformance(
  element: HTMLElement,
  scrollDistance: number = 5000,
  duration: number = 2000,
): Promise<{ fps: number; scrollTime: number }> {
  return new Promise((resolve) => {
    const startTime = performance.now();
    let frameCount = 0;
    let lastFrameTime = startTime;

    const scroll = () => {
      const currentTime = performance.now();
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Smooth scroll
      element.scrollTop = scrollDistance * progress;

      // Count frames
      if (currentTime - lastFrameTime >= 16.67) { // ~60fps
        frameCount++;
        lastFrameTime = currentTime;
      }

      if (progress < 1) {
        requestAnimationFrame(scroll);
      } else {
        const scrollTime = currentTime - startTime;
        const fps = Math.round((frameCount / scrollTime) * 1000);
        resolve({ fps, scrollTime });
      }
    };

    requestAnimationFrame(scroll);
  });
}

/**
 * Measure memory usage
 */
export function measureMemoryUsage(): number {
  if ('memory' in performance) {
    const memory = (performance as any).memory;
    return memory.usedJSHeapSize / 1024 / 1024; // Convert to MB
  }
  return 0;
}

/**
 * Run comprehensive benchmark
 */
export async function runBenchmark(
  itemCounts: number[] = [100, 500, 1000, 5000],
  renderFn: (applications: Application[]) => void,
  getScrollElement: () => HTMLElement | null,
): Promise<BenchmarkResult[]> {
  const results: BenchmarkResult[] = [];

  for (const count of itemCounts) {
    logger.info(`Running benchmark for ${count} applications...`);

    // Generate test data
    const applications = generateBenchmarkApplications(count);

    // Measure initial memory
    const memoryBefore = measureMemoryUsage();

    // Measure render time
    const renderTime = await measureRenderTime(() => renderFn(applications), 3);

    // Wait for render to complete
    await new Promise(resolve => setTimeout(resolve, 500));

    // Measure scroll performance
    const scrollElement = getScrollElement();
    let scrollTime = 0;
    let fps = 0;

    if (scrollElement) {
      const scrollResult = await measureScrollPerformance(scrollElement, 5000, 2000);
      scrollTime = scrollResult.scrollTime;
      fps = scrollResult.fps;
    }

    // Measure memory after
    const memoryAfter = measureMemoryUsage();
    const memoryUsed = memoryAfter - memoryBefore;

    results.push({
      testName: `${count} applications`,
      itemCount: count,
      renderTime: Math.round(renderTime * 100) / 100,
      scrollTime: Math.round(scrollTime),
      memoryUsed: Math.round(memoryUsed * 100) / 100,
      fps,
      timestamp: new Date(),
    });

    logger.info(`Completed benchmark for ${count} applications`);
  }

  return results;
}

/**
 * Format benchmark results as table
 */
export function formatBenchmarkResults(results: BenchmarkResult[]): string {
  const header = '| Items | Render Time (ms) | Scroll Time (ms) | Memory (MB) | FPS |';
  const separator = '|-------|------------------|------------------|-------------|-----|';

  const rows = results.map(result =>
    `| ${result.itemCount} | ${result.renderTime} | ${result.scrollTime} | ${result.memoryUsed} | ${result.fps} |`,
  );

  return [header, separator, ...rows].join('\n');
}

/**
 * Compare two benchmark results
 */
export function compareBenchmarks(
  baseline: BenchmarkResult[],
  current: BenchmarkResult[],
): string {
  const comparisons: string[] = [];

  baseline.forEach((baselineResult, index) => {
    const currentResult = current[index];
    if (!currentResult) return;

    const renderDiff = ((currentResult.renderTime - baselineResult.renderTime) / baselineResult.renderTime) * 100;
    const scrollDiff = ((currentResult.scrollTime - baselineResult.scrollTime) / baselineResult.scrollTime) * 100;
    const memoryDiff = ((currentResult.memoryUsed - baselineResult.memoryUsed) / baselineResult.memoryUsed) * 100;
    const fpsDiff = ((currentResult.fps - baselineResult.fps) / baselineResult.fps) * 100;

    comparisons.push(`
${currentResult.itemCount} applications:
  Render Time: ${renderDiff > 0 ? '+' : ''}${renderDiff.toFixed(2)}%
  Scroll Time: ${scrollDiff > 0 ? '+' : ''}${scrollDiff.toFixed(2)}%
  Memory: ${memoryDiff > 0 ? '+' : ''}${memoryDiff.toFixed(2)}%
  FPS: ${fpsDiff > 0 ? '+' : ''}${fpsDiff.toFixed(2)}%
    `);
  });

  return comparisons.join('\n');
}

/**
 * Export benchmark results to JSON
 */
export function exportBenchmarkResults(results: BenchmarkResult[]): string {
  return JSON.stringify(results, null, 2);
}

/**
 * Save benchmark results to localStorage
 */
export function saveBenchmarkResults(key: string, results: BenchmarkResult[]): void {
  try {
    localStorage.setItem(key, exportBenchmarkResults(results));
    logger.info(`Benchmark results saved to localStorage with key: ${key}`);
  } catch (error) {
    logger.error('Failed to save benchmark results:', error);
  }
}

/**
 * Load benchmark results from localStorage
 */
export function loadBenchmarkResults(key: string): BenchmarkResult[] | null {
  try {
    const data = localStorage.getItem(key);
    if (!data) return null;

    const results = JSON.parse(data);
    // Convert timestamp strings back to Date objects
    return results.map((result: any) => ({
      ...result,
      timestamp: new Date(result.timestamp),
    }));
  } catch (error) {
    logger.error('Failed to load benchmark results:', error);
    return null;
  }
}

/**
 * Example usage:
 * 
 * ```typescript
 * import { runBenchmark, formatBenchmarkResults } from './benchmark';
 * 
 * const results = await runBenchmark(
 *   [100, 500, 1000],
 *   (applications) => {
 *     // Render function
 *     setApplications(applications);
 *   },
 *   () => document.querySelector('.virtual-list-container')
 * );
 * 
 * logger.info(formatBenchmarkResults(results));
 * ```
 */
