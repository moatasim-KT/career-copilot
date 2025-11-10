/**
 * Lazy Component Exports
 * 
 * Central export point for all lazy-loaded components.
 * These components use React.lazy() and Suspense for code splitting.
 */

// Page components
export { default as LazyAnalyticsPage } from './LazyAnalyticsPage';
export { default as LazyEnhancedDashboard } from './LazyEnhancedDashboard';

// Feature components
export { default as LazyCommandPalette } from './LazyCommandPalette';
export { default as LazyAdvancedSearch } from './LazyAdvancedSearch';
export { default as LazyNotificationCenter } from './LazyNotificationCenter';

// UI components
export { default as LazyDataTable } from './LazyDataTable';
export { default as LazyRichTextEditor } from './LazyRichTextEditor';

// Chart components
export {
  LazyPieChart,
  LazyBarChart,
  LazyLineChart,
  LazyComposedChart,
  LazyAreaChart,
  LazyRadarChart,
  LazyChartComponents,
  ChartWrapper,
} from './LazyCharts';
