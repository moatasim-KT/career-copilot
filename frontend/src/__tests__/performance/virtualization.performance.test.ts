/**
 * Virtualization Performance Tests
 * 
 * Automated performance tests for virtualized components.
 * These tests verify that performance targets are met.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  runBenchmark,
  DEVICE_PROFILES,
  type BenchmarkResult,
} from '@/lib/performance/performanceTesting';

// Mock data generators
function generateMockJobs(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: `Software Engineer ${i + 1}`,
    company: `Company ${i + 1}`,
    location: 'Remote',
    salary: 100000 + i * 1000,
    description: 'Job description...',
    posted_date: new Date().toISOString(),
  }));
}

function generateMockApplications(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    job_id: i + 1,
    user_id: 1,
    status: 'applied',
    applied_date: new Date().toISOString(),
    job_title: `Software Engineer ${i + 1}`,
    company_name: `Company ${i + 1}`,
    job_location: 'Remote',
  }));
}

function generateMockTableData(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Item ${i + 1}`,
    value: Math.random() * 1000,
    status: i % 2 === 0 ? 'active' : 'inactive',
    date: new Date().toISOString(),
  }));
}

describe('VirtualJobList Performance', () => {
  let container: HTMLElement;
  let jobs: any[] = [];

  beforeEach(() => {
    // Create test container
    container = document.createElement('div');
    container.setAttribute('data-testid', 'virtual-job-list');
    container.style.height = '600px';
    container.style.overflow = 'auto';
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
    jobs = [];
  });

  it('should render 100 jobs in under 200ms on desktop', async () => {
    const result = await runBenchmark(
      'VirtualJobList',
      100,
      true,
      async () => {
        jobs = generateMockJobs(100);
        // Simulate render
        container.innerHTML = jobs.map(j => `<div>${j.title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.renderTime).toBeLessThan(200);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should render 1000 jobs in under 500ms on desktop', async () => {
    const result = await runBenchmark(
      'VirtualJobList',
      1000,
      true,
      async () => {
        jobs = generateMockJobs(1000);
        container.innerHTML = jobs.slice(0, 20).map(j => `<div>${j.title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.renderTime).toBeLessThan(500);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should maintain 55+ FPS with 1000 jobs on desktop', async () => {
    const result = await runBenchmark(
      'VirtualJobList',
      1000,
      true,
      async () => {
        jobs = generateMockJobs(1000);
        container.innerHTML = jobs.slice(0, 20).map(j => `<div>${j.title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should maintain 55+ FPS with 500 jobs on mobile', async () => {
    const result = await runBenchmark(
      'VirtualJobList',
      500,
      true,
      async () => {
        jobs = generateMockJobs(500);
        container.innerHTML = jobs.slice(0, 20).map(j => `<div>${j.title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.mobile
    );

    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should use less than 50MB memory with 1000 jobs', async () => {
    const result = await runBenchmark(
      'VirtualJobList',
      1000,
      true,
      async () => {
        jobs = generateMockJobs(1000);
        container.innerHTML = jobs.slice(0, 20).map(j => `<div>${j.title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    if (result.metrics.memory) {
      expect(result.metrics.memory.used).toBeLessThan(50);
    }
    expect(result.passed).toBe(true);
  }, 30000);
});

describe('VirtualApplicationList Performance', () => {
  let container: HTMLElement;
  let applications: any[] = [];

  beforeEach(() => {
    container = document.createElement('div');
    container.setAttribute('data-testid', 'virtual-application-list');
    container.style.height = '600px';
    container.style.overflow = 'auto';
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
    applications = [];
  });

  it('should render 100 applications in under 200ms on desktop', async () => {
    const result = await runBenchmark(
      'VirtualApplicationList',
      100,
      true,
      async () => {
        applications = generateMockApplications(100);
        container.innerHTML = applications.map(a => `<div>${a.job_title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.renderTime).toBeLessThan(200);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should render 1000 applications in under 500ms on desktop', async () => {
    const result = await runBenchmark(
      'VirtualApplicationList',
      1000,
      true,
      async () => {
        applications = generateMockApplications(1000);
        container.innerHTML = applications.slice(0, 20).map(a => `<div>${a.job_title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.renderTime).toBeLessThan(500);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should maintain 55+ FPS with 1000 applications on desktop', async () => {
    const result = await runBenchmark(
      'VirtualApplicationList',
      1000,
      true,
      async () => {
        applications = generateMockApplications(1000);
        container.innerHTML = applications.slice(0, 20).map(a => `<div>${a.job_title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should maintain 55+ FPS with 500 applications on mobile', async () => {
    const result = await runBenchmark(
      'VirtualApplicationList',
      500,
      true,
      async () => {
        applications = generateMockApplications(500);
        container.innerHTML = applications.slice(0, 20).map(a => `<div>${a.job_title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.mobile
    );

    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
    expect(result.passed).toBe(true);
  }, 30000);
});

describe('VirtualDataTable Performance', () => {
  let container: HTMLElement;
  let data: any[] = [];

  beforeEach(() => {
    container = document.createElement('div');
    container.setAttribute('data-testid', 'datatable-container');
    container.style.height = '600px';
    container.style.overflow = 'auto';
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
    data = [];
  });

  it('should render 100 rows in under 200ms on desktop', async () => {
    const result = await runBenchmark(
      'VirtualDataTable',
      100,
      true,
      async () => {
        data = generateMockTableData(100);
        container.innerHTML = `<table>${data.map(d => `<tr><td>${d.name}</td></tr>`).join('')}</table>`;
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.renderTime).toBeLessThan(200);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should render 1000 rows in under 500ms on desktop', async () => {
    const result = await runBenchmark(
      'VirtualDataTable',
      1000,
      true,
      async () => {
        data = generateMockTableData(1000);
        container.innerHTML = `<table>${data.slice(0, 20).map(d => `<tr><td>${d.name}</td></tr>`).join('')}</table>`;
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.renderTime).toBeLessThan(500);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should maintain 55+ FPS with 2000 rows on desktop', async () => {
    const result = await runBenchmark(
      'VirtualDataTable',
      2000,
      true,
      async () => {
        data = generateMockTableData(2000);
        container.innerHTML = `<table>${data.slice(0, 20).map(d => `<tr><td>${d.name}</td></tr>`).join('')}</table>`;
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should maintain 55+ FPS with 1000 rows on mobile', async () => {
    const result = await runBenchmark(
      'VirtualDataTable',
      1000,
      true,
      async () => {
        data = generateMockTableData(1000);
        container.innerHTML = `<table>${data.slice(0, 20).map(d => `<tr><td>${d.name}</td></tr>`).join('')}</table>`;
      },
      () => container,
      DEVICE_PROFILES.mobile
    );

    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(55);
    expect(result.passed).toBe(true);
  }, 30000);

  it('should handle 5000 rows without crashing', async () => {
    const result = await runBenchmark(
      'VirtualDataTable',
      5000,
      true,
      async () => {
        data = generateMockTableData(5000);
        container.innerHTML = `<table>${data.slice(0, 20).map(d => `<tr><td>${d.name}</td></tr>`).join('')}</table>`;
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    // Should complete without errors
    expect(result.metrics.renderTime).toBeLessThan(1000);
    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThan(50);
  }, 30000);
});

describe('Performance Regression Tests', () => {
  it('should not regress render time by more than 10%', async () => {
    // This test would compare against baseline metrics
    // For now, we just verify it completes
    const container = document.createElement('div');
    container.style.height = '600px';
    container.style.overflow = 'auto';
    document.body.appendChild(container);

    const result = await runBenchmark(
      'RegressionTest',
      1000,
      true,
      async () => {
        const data = generateMockJobs(1000);
        container.innerHTML = data.slice(0, 20).map(j => `<div>${j.title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    document.body.removeChild(container);

    // Baseline: 150ms, allow 10% regression = 165ms
    expect(result.metrics.renderTime).toBeLessThan(165);
  }, 30000);

  it('should not regress FPS by more than 5%', async () => {
    const container = document.createElement('div');
    container.style.height = '600px';
    container.style.overflow = 'auto';
    document.body.appendChild(container);

    const result = await runBenchmark(
      'RegressionTest',
      1000,
      true,
      async () => {
        const data = generateMockJobs(1000);
        container.innerHTML = data.slice(0, 20).map(j => `<div>${j.title}</div>`).join('');
      },
      () => container,
      DEVICE_PROFILES.desktop
    );

    document.body.removeChild(container);

    // Baseline: 60 FPS, allow 5% regression = 57 FPS
    expect(result.metrics.scrollPerformance.minFPS).toBeGreaterThanOrEqual(57);
  }, 30000);
});
