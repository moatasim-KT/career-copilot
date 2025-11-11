/**
 * CSV Export Utility
 * Converts data to CSV format and triggers download
 */

/**
 * Escape special characters in CSV fields
 * Handles commas, quotes, and newlines
 */
function escapeCSVField(field: any): string {
  if (field === null || field === undefined) {
    return '';
  }

  const stringValue = String(field);
  
  // Check if field contains special characters that require escaping
  const needsEscaping = stringValue.includes(',') || 
                       stringValue.includes('"') || 
                       stringValue.includes('\n') || 
                       stringValue.includes('\r');

  if (needsEscaping) {
    // Escape double quotes by doubling them
    const escaped = stringValue.replace(/"/g, '""');
    // Wrap in double quotes
    return `"${escaped}"`;
  }

  return stringValue;
}

/**
 * Convert array of objects to CSV string
 */
function convertToCSV<T extends Record<string, any>>(
  data: T[],
  columns?: Array<{ key: keyof T; header: string }>,
): string {
  if (data.length === 0) {
    return '';
  }

  // If columns not provided, use all keys from first object
  const csvColumns = columns || Object.keys(data[0]).map(key => ({
    key: key as keyof T,
    header: key,
  }));

  // Create header row
  const headers = csvColumns.map(col => escapeCSVField(col.header));
  const headerRow = headers.join(',');

  // Create data rows
  const dataRows = data.map(row => {
    const values = csvColumns.map(col => {
      const value = row[col.key];
      
      // Handle nested objects and arrays
      if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value)) {
          return escapeCSVField(value.join('; '));
        }
        return escapeCSVField(JSON.stringify(value));
      }
      
      return escapeCSVField(value);
    });
    return values.join(',');
  });

  // Combine header and data rows
  return [headerRow, ...dataRows].join('\n');
}

/**
 * Trigger download of CSV file
 */
function downloadCSV(csvContent: string, filename: string): void {
  // Add BOM for Excel compatibility with UTF-8
  const BOM = '\uFEFF';
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
  
  // Create download link
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up
  URL.revokeObjectURL(url);
}

/**
 * Export data to CSV file
 * 
 * @param data - Array of objects to export
 * @param filename - Name of the file (without extension)
 * @param columns - Optional column configuration
 * 
 * @example
 * ```typescript
 * exportToCSV(
 *   applications,
 *   'applications-export',
 *   [
 *     { key: 'id', header: 'ID' },
 *     { key: 'job_title', header: 'Job Title' },
 *     { key: 'company', header: 'Company' },
 *     { key: 'status', header: 'Status' },
 *   ]
 * );
 * ```
 */
export function exportToCSV<T extends Record<string, any>>(
  data: T[],
  filename: string,
  columns?: Array<{ key: keyof T; header: string }>,
): void {
  if (data.length === 0) {
    throw new Error('No data to export');
  }

  // Ensure filename has .csv extension
  const csvFilename = filename.endsWith('.csv') ? filename : `${filename}.csv`;
  
  // Convert data to CSV
  const csvContent = convertToCSV(data, columns);
  
  // Trigger download
  downloadCSV(csvContent, csvFilename);
}

/**
 * Export data to CSV with timestamp in filename
 */
export function exportToCSVWithTimestamp<T extends Record<string, any>>(
  data: T[],
  baseFilename: string,
  columns?: Array<{ key: keyof T; header: string }>,
): void {
  const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const filename = `${baseFilename}-${timestamp}`;
  exportToCSV(data, filename, columns);
}

/**
 * Get CSV content as string (for preview or testing)
 */
export function getCSVContent<T extends Record<string, any>>(
  data: T[],
  columns?: Array<{ key: keyof T; header: string }>,
): string {
  return convertToCSV(data, columns);
}
