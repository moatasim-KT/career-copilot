import { dataVizPalette } from '@/lib/designTokens';
import { logger } from '@/lib/logger';

/**
 * Chart Utilities
 * 
 * Comprehensive utilities for chart interactivity, export, and data manipulation
 */

// Note: html2canvas would need to be installed for PNG export
// import html2canvas from 'html2canvas';

/**
 * Export chart data to CSV format
 */
export function exportToCSV(
  data: any[],
  columns: { key: string; label: string }[],
  filename: string,
): void {
  try {
    // Create CSV header
    const header = columns.map(col => col.label).join(',');

    // Create CSV rows
    const rows = data.map(row =>
      columns.map(col => {
        const value = row[col.key];
        // Escape values that contain commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(','),
    );

    // Combine header and rows
    const csvContent = [header, ...rows].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    logger.error('Error exporting to CSV:', error);
    throw new Error('Failed to export CSV');
  }
}

/**
 * Export chart as PNG image
 * Note: Requires html2canvas library to be installed
 */
export async function exportToPNG(
  elementId: string,
  filename: string,
): Promise<void> {
  try {
    // This would require html2canvas library
    // For now, we'll throw an error with instructions
    throw new Error(
      `PNG export for element "${elementId}" requires html2canvas. Install with: npm install html2canvas to enable saving as ${filename}`,
    );

    /* Uncomment when html2canvas is installed:
    const html2canvas = (await import('html2canvas')).default;
    const element = document.getElementById(elementId);
    if (!element) {
      throw new Error('Chart element not found');
    }
    
    const canvas = await html2canvas(element, {
      backgroundColor: '#ffffff',
      scale: 2, // Higher quality
    });
    
    // Convert to blob and download
    canvas.toBlob((blob: Blob | null) => {
      if (!blob) {
        throw new Error('Failed to create image blob');
      }
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${filename}-${new Date().toISOString().split('T')[0]}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    });
    */
  } catch (error) {
    logger.error('Error exporting to PNG:', error);
    throw new Error('Failed to export PNG');
  }
}

/**
 * Format number with abbreviations (K, M, B)
 */
export function formatNumber(num: number): string {
  if (num >= 1000000000) {
    return `${(num / 1000000000).toFixed(1)}B`;
  }
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * Format currency
 */
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format percentage
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Calculate percentage change
 */
export function calculatePercentageChange(current: number, previous: number): number {
  if (previous === 0) {
    return current > 0 ? 100 : 0;
  }
  return ((current - previous) / previous) * 100;
}

/**
 * Generate color palette for charts
 */
export function generateColorPalette(count: number, isDark: boolean = false): string[] {
  const palette = isDark ? dataVizPalette.dark : dataVizPalette.light;

  return Array.from({ length: count }, (_, index) => palette[index % palette.length]);
}

/**
 * Debounce function for chart interactions
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function for chart interactions
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number,
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

/**
 * Calculate moving average for trend lines
 */
export function calculateMovingAverage(
  data: number[],
  windowSize: number,
): number[] {
  const result: number[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - windowSize + 1);
    const window = data.slice(start, i + 1);
    const average = window.reduce((sum, val) => sum + val, 0) / window.length;
    result.push(average);
  }

  return result;
}

/**
 * Calculate linear regression for trend lines
 */
export function calculateLinearRegression(
  data: { x: number; y: number }[],
): { slope: number; intercept: number; predict: (x: number) => number } {
  const n = data.length;

  if (n === 0) {
    return { slope: 0, intercept: 0, predict: () => 0 };
  }

  const sumX = data.reduce((sum, point) => sum + point.x, 0);
  const sumY = data.reduce((sum, point) => sum + point.y, 0);
  const sumXY = data.reduce((sum, point) => sum + point.x * point.y, 0);
  const sumXX = data.reduce((sum, point) => sum + point.x * point.x, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  return {
    slope,
    intercept,
    predict: (x: number) => slope * x + intercept,
  };
}

/**
 * Group data by time period
 */
export function groupByTimePeriod(
  data: { date: Date; value: number }[],
  period: 'day' | 'week' | 'month' | 'year',
): { date: string; value: number }[] {
  const grouped = new Map<string, number>();

  data.forEach((item) => {
    let key: string;
    const date = new Date(item.date);

    switch (period) {
      case 'day': {
        key = date.toISOString().split('T')[0];
        break;
      }
      case 'week': {
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = weekStart.toISOString().split('T')[0];
        break;
      }
      case 'month': {
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        break;
      }
      case 'year': {
        key = date.getFullYear().toString();
        break;
      }
    }

    grouped.set(key, (grouped.get(key) || 0) + item.value);
  });

  return Array.from(grouped.entries())
    .map(([date, value]) => ({ date, value }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

/**
 * Detect chart theme (light/dark)
 */
export function detectChartTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') {
    return 'light';
  }

  return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

/**
 * Get responsive chart dimensions
 */
export function getResponsiveChartDimensions(
  containerWidth: number,
): { width: number; height: number } {
  // Mobile
  if (containerWidth < 640) {
    return { width: containerWidth, height: 250 };
  }

  // Tablet
  if (containerWidth < 1024) {
    return { width: containerWidth, height: 300 };
  }

  // Desktop
  return { width: containerWidth, height: 350 };
}

/**
 * Format axis label based on value range
 */
export function formatAxisLabel(value: number, maxValue: number): string {
  if (maxValue >= 1000000) {
    return formatNumber(value);
  }

  if (maxValue >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }

  return value.toString();
}

/**
 * Calculate chart statistics
 */
export function calculateChartStats(data: number[]): {
  min: number;
  max: number;
  mean: number;
  median: number;
  sum: number;
  stdDev: number;
} {
  if (data.length === 0) {
    return { min: 0, max: 0, mean: 0, median: 0, sum: 0, stdDev: 0 };
  }

  const sorted = [...data].sort((a, b) => a - b);
  const sum = data.reduce((acc, val) => acc + val, 0);
  const mean = sum / data.length;

  const median = data.length % 2 === 0
    ? (sorted[data.length / 2 - 1] + sorted[data.length / 2]) / 2
    : sorted[Math.floor(data.length / 2)];

  const variance = data.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / data.length;
  const stdDev = Math.sqrt(variance);

  return {
    min: sorted[0],
    max: sorted[sorted.length - 1],
    mean,
    median,
    sum,
    stdDev,
  };
}

/**
 * Animate chart value changes
 */
export function animateValue(
  start: number,
  end: number,
  duration: number,
  callback: (value: number) => void,
): void {
  const startTime = Date.now();
  const difference = end - start;

  const step = () => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Easing function (ease-out)
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + difference * eased;

    callback(current);

    if (progress < 1) {
      requestAnimationFrame(step);
    }
  };

  requestAnimationFrame(step);
}

/**
 * Check if chart data is valid
 */
export function isValidChartData(data: any[]): boolean {
  if (!Array.isArray(data) || data.length === 0) {
    return false;
  }

  // Check if all items have required properties
  return data.every(item => item !== null && typeof item === 'object');
}

/**
 * Sanitize chart data
 */
export function sanitizeChartData<T extends Record<string, any>>(
  data: T[],
  requiredKeys: string[],
): T[] {
  return data.filter(item => {
    // Check if all required keys exist
    return requiredKeys.every(key => key in item && item[key] !== null && item[key] !== undefined);
  });
}
