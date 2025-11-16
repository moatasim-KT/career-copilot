/**
 * PDF Export Utility
 * Generates PDF documents with table layout and proper formatting
 */

import jsPDF from 'jspdf';
import autoTable, { type RowInput } from 'jspdf-autotable';

import { colors } from '@/lib/designTokens';
import { logger } from '@/lib/logger';

/**
 * PDF export options
 */
export interface PDFExportOptions {
  /** Document title */
  title?: string;
  /** Document subtitle or description */
  subtitle?: string;
  /** Include logo in header */
  includeLogo?: boolean;
  /** Logo URL or base64 data */
  logoUrl?: string;
  /** Page orientation */
  orientation?: 'portrait' | 'landscape';
  /** Include page numbers */
  includePageNumbers?: boolean;
  /** Include timestamp */
  includeTimestamp?: boolean;
  /** Custom footer text */
  footerText?: string;
  /** Table styling theme */
  theme?: 'striped' | 'grid' | 'plain';
  /** Primary color for headers (hex) */
  primaryColor?: string;
}

/**
 * Column definition for PDF export
 */
export interface PDFColumn<T> {
  /** Column key */
  key: keyof T;
  /** Column header text */
  header: string;
  /** Column width (optional, auto-calculated if not provided) */
  width?: number;
  /** Custom formatter function */
  formatter?: (value: any) => string;
}

/**
 * Default PDF options
 */
const DEFAULT_OPTIONS: Required<PDFExportOptions> = {
  title: 'Export',
  subtitle: '',
  includeLogo: false,
  logoUrl: '',
  orientation: 'portrait',
  includePageNumbers: true,
  includeTimestamp: true,
  footerText: 'Career Copilot',
  theme: 'striped',
  primaryColor: colors.primary[500],
};

/**
 * Convert hex color to RGB array
 */
function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) {
    return [59, 130, 246]; // Default blue-500
  }
  return [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16),
  ];
}

const HEADER_TEXT_COLOR = hexToRgb(colors.neutral[800]);
const MUTED_TEXT_COLOR = hexToRgb(colors.neutral[500]);
const BORDER_COLOR = hexToRgb(colors.neutral[200]);
const SURFACE_SUBTLE_COLOR = hexToRgb(colors.neutral[50]);
const SURFACE_LIGHT_COLOR = hexToRgb(colors.neutral[100]);

/**
 * Format date for display
 */
function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Add header to PDF document
 */
function addHeader(
  doc: jsPDF,
  options: Required<PDFExportOptions>,
  pageWidth: number,
): number {
  let yPosition = 20;

  // Add logo if enabled
  if (options.includeLogo && options.logoUrl) {
    try {
      // Note: Logo must be base64 or accessible URL
      doc.addImage(options.logoUrl, 'PNG', 15, yPosition, 30, 30);
      yPosition += 35;
    } catch (error) {
      logger.warn('Failed to add logo to PDF:', error);
    }
  }

  // Add title
  doc.setFontSize(20);
  doc.setTextColor(...HEADER_TEXT_COLOR);
  doc.text(options.title, pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 10;

  // Add subtitle if provided
  if (options.subtitle) {
    doc.setFontSize(12);
    doc.setTextColor(...MUTED_TEXT_COLOR);
    doc.text(options.subtitle, pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 8;
  }

  // Add timestamp if enabled
  if (options.includeTimestamp) {
    doc.setFontSize(10);
    doc.setTextColor(...MUTED_TEXT_COLOR);
    doc.text(
      `Generated on ${formatDate(new Date())}`,
      pageWidth / 2,
      yPosition,
      { align: 'center' },
    );
    yPosition += 10;
  }

  // Add separator line
  doc.setDrawColor(...BORDER_COLOR);
  doc.setLineWidth(0.5);
  doc.line(15, yPosition, pageWidth - 15, yPosition);
  yPosition += 10;

  return yPosition;
}

/**
 * Add footer to PDF document
 */
function addFooter(
  doc: jsPDF,
  options: Required<PDFExportOptions>,
  pageWidth: number,
  pageHeight: number,
  pageNumber: number,
  totalPages: number,
): void {
  const footerY = pageHeight - 15;

  doc.setFontSize(9);
  doc.setTextColor(...MUTED_TEXT_COLOR);

  // Add footer text
  if (options.footerText) {
    doc.text(options.footerText, 15, footerY);
  }

  // Add page numbers if enabled
  if (options.includePageNumbers) {
    doc.text(
      `Page ${pageNumber} of ${totalPages}`,
      pageWidth - 15,
      footerY,
      { align: 'right' },
    );
  }
}

/**
 * Prepare table data from objects
 */
function prepareTableData<T extends Record<string, any>>(
  data: T[],
  columns: PDFColumn<T>[],
): { headers: string[]; rows: RowInput[] } {
  // Extract headers
  const headers = columns.map((col) => col.header);

  // Extract and format rows
  const rows: RowInput[] = data.map((item) => {
    return columns.map((col) => {
      const value = item[col.key];

      // Use custom formatter if provided
      if (col.formatter) {
        return col.formatter(value);
      }

      // Handle null/undefined
      if (value === null || value === undefined) {
        return '';
      }

      // Handle arrays
      if (Array.isArray(value)) {
        return value.join(', ');
      }

      // Handle objects
      if (typeof value === 'object') {
        return JSON.stringify(value);
      }

      // Handle dates
      if (value && typeof value === 'object' && 'toLocaleDateString' in value) {
        return (value as Date).toLocaleDateString();
      }

      // Convert to string
      return String(value);
    });
  });

  return { headers, rows };
}

/**
 * Export data to PDF file
 *
 * @param data - Array of objects to export
 * @param columns - Column definitions
 * @param filename - Name of the file (without extension)
 * @param options - PDF export options
 *
 * @example
 * ```typescript
 * exportToPDF(
 *   applications,
 *   [
 *     { key: 'id', header: 'ID' },
 *     { key: 'job_title', header: 'Job Title' },
 *     { key: 'company', header: 'Company' },
 *     { key: 'status', header: 'Status' },
 *     {
 *       key: 'applied_date',
 *       header: 'Applied Date',
 *       formatter: (date) => new Date(date).toLocaleDateString()
 *     },
 *   ],
 *   'applications-export',
 *   {
 *     title: 'Job Applications',
 *     subtitle: 'Export of all job applications',
 *     theme: 'striped',
 *   }
 * );
 * ```
 */
export function exportToPDF<T extends Record<string, any>>(
  data: T[],
  columns: PDFColumn<T>[],
  filename: string,
  options: PDFExportOptions = {},
): void {
  if (data.length === 0) {
    throw new Error('No data to export');
  }

  // Merge with default options
  const opts: Required<PDFExportOptions> = {
    ...DEFAULT_OPTIONS,
    ...options,
  };

  // Create PDF document
  const doc = new jsPDF({
    orientation: opts.orientation,
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  // Add header
  const startY = addHeader(doc, opts, pageWidth);

  // Prepare table data
  const { headers, rows } = prepareTableData(data, columns);

  // Get primary color RGB
  const primaryRgb = hexToRgb(opts.primaryColor);

  // Configure table theme
  const tableTheme = {
    striped: {
      headStyles: {
        fillColor: primaryRgb,
        textColor: [255, 255, 255] as [number, number, number],
        fontStyle: 'bold' as const,
        halign: 'left' as const,
      },
      alternateRowStyles: {
        fillColor: SURFACE_SUBTLE_COLOR,
      },
      styles: {
        fontSize: 9,
        cellPadding: 3,
      },
    },
    grid: {
      headStyles: {
        fillColor: primaryRgb,
        textColor: [255, 255, 255] as [number, number, number],
        fontStyle: 'bold' as const,
        halign: 'left' as const,
      },
      styles: {
        fontSize: 9,
        cellPadding: 3,
        lineColor: BORDER_COLOR,
        lineWidth: 0.1,
      },
    },
    plain: {
      headStyles: {
        fillColor: SURFACE_LIGHT_COLOR,
        textColor: HEADER_TEXT_COLOR,
        fontStyle: 'bold' as const,
        halign: 'left' as const,
      },
      styles: {
        fontSize: 9,
        cellPadding: 3,
      },
    },
  };

  // Generate table
  autoTable(doc, {
    head: [headers],
    body: rows,
    startY,
    margin: { left: 15, right: 15 },
    ...tableTheme[opts.theme],
    didDrawPage: () => {
      // Add footer to each page
      const pageNumber = (doc as any).internal.getCurrentPageInfo().pageNumber;
      const totalPages = (doc as any).internal.getNumberOfPages();
      addFooter(doc, opts, pageWidth, pageHeight, pageNumber, totalPages);
    },
  });

  // Ensure filename has .pdf extension
  const pdfFilename = filename.endsWith('.pdf') ? filename : `${filename}.pdf`;

  // Save PDF
  doc.save(pdfFilename);
}

/**
 * Export data to PDF with timestamp in filename
 */
export function exportToPDFWithTimestamp<T extends Record<string, any>>(
  data: T[],
  columns: PDFColumn<T>[],
  baseFilename: string,
  options: PDFExportOptions = {},
): void {
  const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const filename = `${baseFilename}-${timestamp}`;
  exportToPDF(data, columns, filename, options);
}

/**
 * Generate PDF preview (returns blob URL for preview)
 */
export function generatePDFPreview<T extends Record<string, any>>(
  data: T[],
  columns: PDFColumn<T>[],
  options: PDFExportOptions = {},
): string {
  if (data.length === 0) {
    throw new Error('No data to export');
  }

  // Merge with default options
  const opts: Required<PDFExportOptions> = {
    ...DEFAULT_OPTIONS,
    ...options,
  };

  // Create PDF document
  const doc = new jsPDF({
    orientation: opts.orientation,
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  // Add header
  const startY = addHeader(doc, opts, pageWidth);

  // Prepare table data
  const { headers, rows } = prepareTableData(data, columns);

  // Get primary color RGB
  const primaryRgb = hexToRgb(opts.primaryColor);

  // Generate table
  autoTable(doc, {
    head: [headers],
    body: rows,
    startY,
    margin: { left: 15, right: 15 },
    headStyles: {
      fillColor: primaryRgb,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    didDrawPage: () => {
      const pageNumber = (doc as any).internal.getCurrentPageInfo().pageNumber;
      const totalPages = (doc as any).internal.getNumberOfPages();
      addFooter(doc, opts, pageWidth, pageHeight, pageNumber, totalPages);
    },
  });

  // Return blob URL for preview
  const blob = doc.output('blob');
  return URL.createObjectURL(blob);
}
