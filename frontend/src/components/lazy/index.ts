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

// Modal and Dialog components (conditionally rendered)
export { default as LazyModal, LazyModalFooter } from './LazyModal';
export { default as LazyModal2 } from './LazyModal2';
export { default as LazyDrawer2 } from './LazyDrawer2';
export { default as LazyConfirmDialog } from './LazyConfirmDialog';

// Bulk operation components (conditionally rendered)
export { LazyBulkActionBar } from './LazyBulkActionBar';
export { default as LazyConfirmBulkAction } from './LazyConfirmBulkAction';
export { default as LazyBulkOperationProgress } from './LazyBulkOperationProgress';
export { default as LazyUndoToast } from './LazyUndoToast';

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
