'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Download, FileText, FileSpreadsheet } from 'lucide-react';
import { useState } from 'react';

import { exportToCSV } from '@/lib/export/exportToCSV';
import { exportToPDF, type PDFColumn } from '@/lib/export/exportToPDF';
import { logger } from '@/lib/logger';

import Button2 from './Button2';

export interface ExportOption {
  label: string;
  value: 'csv' | 'pdf' | 'csv-all' | 'csv-selected';
  icon: React.ReactNode;
}

interface ExportDropdownProps<T> {
  /** Data to export */
  data: T[];
  /** Selected row IDs (for selected export) */
  selectedIds?: (string | number)[];
  /** Filename base (without extension) */
  filename: string;
  /** CSV column configuration */
  csvColumns?: Array<{ key: keyof T; header: string }>;
  /** PDF column configuration */
  pdfColumns?: PDFColumn<T>[];
  /** PDF export options */
  pdfOptions?: {
    title?: string;
    subtitle?: string;
    theme?: 'striped' | 'grid' | 'plain';
  };
  /** Custom export options */
  options?: ExportOption[];
  /** Callback when export starts */
  onExportStart?: (type: string) => void;
  /** Callback when export completes */
  onExportComplete?: (type: string) => void;
  /** Callback when export fails */
  onExportError?: (error: Error) => void;
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success' | 'link' | 'gradient';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Custom className */
  className?: string;
}

const DEFAULT_OPTIONS: ExportOption[] = [
  {
    label: 'Export Current View (CSV)',
    value: 'csv',
    icon: <FileSpreadsheet className="h-4 w-4" />,
  },
  {
    label: 'Export All Data (CSV)',
    value: 'csv-all',
    icon: <FileSpreadsheet className="h-4 w-4" />,
  },
  {
    label: 'Export Selected (CSV)',
    value: 'csv-selected',
    icon: <FileSpreadsheet className="h-4 w-4" />,
  },
  {
    label: 'Export as PDF',
    value: 'pdf',
    icon: <FileText className="h-4 w-4" />,
  },
];

export function ExportDropdown<T extends Record<string, any>>({
  data,
  selectedIds = [],
  filename,
  csvColumns,
  pdfColumns,
  pdfOptions,
  options = DEFAULT_OPTIONS,
  onExportStart,
  onExportComplete,
  onExportError,
  variant = 'outline',
  size = 'md',
  className = '',
}: ExportDropdownProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (type: string) => {
    setIsOpen(false);
    setIsExporting(true);

    try {
      onExportStart?.(type);

      let exportData: T[] = [];

      // Determine which data to export
      switch (type) {
        case 'csv':
          exportData = data;
          break;
        case 'csv-all':
          exportData = data;
          break;
        case 'csv-selected':
          if (selectedIds.length === 0) {
            throw new Error('No items selected');
          }
          exportData = data.filter((item) =>
            selectedIds.includes(item.id as string | number),
          );
          break;
        case 'pdf':
          exportData = data;
          break;
        default:
          throw new Error(`Unknown export type: ${type}`);
      }

      if (exportData.length === 0) {
        throw new Error('No data to export');
      }

      // Perform export
      if (type.startsWith('csv')) {
        const timestamp = new Date().toISOString().split('T')[0];
        exportToCSV(exportData, `${filename}-${timestamp}`, csvColumns);
      } else if (type === 'pdf') {
        if (!pdfColumns) {
          throw new Error('PDF columns not configured');
        }
        exportToPDF(
          exportData,
          pdfColumns,
          `${filename}-${new Date().toISOString().split('T')[0]}`,
          {
            title: pdfOptions?.title || 'Export',
            subtitle: pdfOptions?.subtitle,
            theme: pdfOptions?.theme || 'striped',
            includeTimestamp: true,
            includePageNumbers: true,
          },
        );
      }

      onExportComplete?.(type);
      logger.log(`Export completed: ${type}`, { count: exportData.length });
    } catch (error) {
      logger.error('Export failed', error);
      onExportError?.(error as Error);
    } finally {
      setIsExporting(false);
    }
  };

  // Filter options based on context
  const availableOptions = options.filter((option) => {
    if (option.value === 'csv-selected') {
      return selectedIds.length > 0;
    }
    return true;
  });

  return (
    <div className={`relative ${className}`}>
      <Button2
        variant={variant}
        size={size}
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting || data.length === 0}
        className="flex items-center space-x-2"
      >
        <Download className={`h-4 w-4 ${isExporting ? 'animate-bounce' : ''}`} />
        <span>{isExporting ? 'Exporting...' : 'Export'}</span>
      </Button2>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown Menu */}
            <motion.div
              className="absolute right-0 mt-2 w-64 bg-white dark:bg-neutral-800 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-700 z-50 overflow-hidden"
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
            >
              <div className="py-1">
                {availableOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleExport(option.value)}
                    className="w-full px-4 py-2 text-left text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center space-x-3 transition-colors"
                    disabled={isExporting}
                  >
                    <span className="text-neutral-500 dark:text-neutral-400">
                      {option.icon}
                    </span>
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>

              {data.length > 0 && (
                <div className="px-4 py-2 text-xs text-neutral-500 dark:text-neutral-400 border-t border-neutral-200 dark:border-neutral-700">
                  {data.length} item{data.length !== 1 ? 's' : ''} available
                  {selectedIds.length > 0 && ` • ${selectedIds.length} selected`}
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
