'use client';

import { Upload, FileText, AlertCircle, CheckCircle, X, Download } from 'lucide-react';
import { useState, useRef } from 'react';

import Button2 from '@/components/ui/Button2';
import Card, { CardContent } from '@/components/ui/Card2';
import { logger } from '@/lib/logger';
import { m, AnimatePresence } from '@/lib/motion';

export interface DataImportColumn {
  key: string;
  label: string;
  required?: boolean;
  type?: 'string' | 'number' | 'date' | 'boolean';
}

export interface DataImportProps {
  /** Callback when import is complete */
  onImport: (data: any[]) => Promise<void>;
  /** CSV template URL for download */
  templateUrl?: string;
  /** Column definitions */
  columns: DataImportColumn[];
  /** Validation function */
  validator?: (data: any[]) => { valid: boolean; errors: string[] };
  /** Title */
  title?: string;
  /** Description */
  description?: string;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export function DataImport({
  onImport,
  templateUrl,
  columns,
  validator,
  title = 'Import Data',
  description = 'Upload a CSV file to import data',
}: DataImportProps) {
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<any[]>([]);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [importComplete, setImportComplete] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (selectedFile: File) => {
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setImportError('Please select a CSV file');
      return;
    }

    setFile(selectedFile);
    setImportError(null);

    try {
      const text = await selectedFile.text();
      const parsed = parseCSV(text);

      if (parsed.length === 0) {
        throw new Error('CSV file is empty');
      }

      setParsedData(parsed);

      // Auto-map columns if possible
      const headers = Object.keys(parsed[0]);
      const mapping: Record<string, string> = {};
      columns.forEach((col) => {
        const matchingHeader = headers.find(
          (h) => h.toLowerCase() === col.key.toLowerCase() || h.toLowerCase() === col.label.toLowerCase(),
        );
        if (matchingHeader) {
          mapping[col.key] = matchingHeader;
        }
      });
      setColumnMapping(mapping);

      // Validate data
      validateData(parsed, mapping);
    } catch (error) {
      logger.error('Failed to parse CSV', error);
      setImportError('Failed to parse CSV file. Please check the file format.');
    }
  };

  const parseCSV = (text: string): any[] => {
    const lines = text.split('\n').filter((line) => line.trim());
    if (lines.length === 0) return [];

    const headers = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''));
    const data: any[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map((v) => v.trim().replace(/^"|"$/g, ''));
      const row: any = {};
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });
      data.push(row);
    }

    return data;
  };

  const validateData = (data: any[], mapping: Record<string, string>) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check required columns are mapped
    columns.forEach((col) => {
      if (col.required && !mapping[col.key]) {
        errors.push(`Required column "${col.label}" is not mapped`);
      }
    });

    // Validate data types
    data.forEach((row, index) => {
      columns.forEach((col) => {
        const csvColumn = mapping[col.key];
        if (!csvColumn) return;

        const value = row[csvColumn];

        if (col.required && !value) {
          errors.push(`Row ${index + 1}: Missing required field "${col.label}"`);
        }

        if (value && col.type) {
          switch (col.type) {
            case 'number':
              if (isNaN(Number(value))) {
                errors.push(`Row ${index + 1}: "${col.label}" must be a number`);
              }
              break;
            case 'date':
              if (isNaN(Date.parse(value))) {
                warnings.push(`Row ${index + 1}: "${col.label}" may not be a valid date`);
              }
              break;
            case 'boolean':
              if (!['true', 'false', '1', '0', 'yes', 'no'].includes(value.toLowerCase())) {
                errors.push(`Row ${index + 1}: "${col.label}" must be a boolean value`);
              }
              break;
          }
        }
      });
    });

    // Custom validation
    if (validator) {
      const customResult = validator(data);
      if (!customResult.valid) {
        errors.push(...customResult.errors);
      }
    }

    setValidationResult({
      valid: errors.length === 0,
      errors,
      warnings,
    });
  };

  const handleImport = async () => {
    if (!parsedData.length || !validationResult?.valid) return;

    setIsImporting(true);
    setImportProgress(0);
    setImportError(null);

    try {
      // Map data to expected format
      const mappedData = parsedData.map((row) => {
        const mapped: any = {};
        columns.forEach((col) => {
          const csvColumn = columnMapping[col.key];
          if (csvColumn) {
            let value = row[csvColumn];

            // Type conversion
            if (value && col.type) {
              switch (col.type) {
                case 'number':
                  value = Number(value);
                  break;
                case 'boolean':
                  value = ['true', '1', 'yes'].includes(value.toLowerCase());
                  break;
                case 'date':
                  value = new Date(value).toISOString();
                  break;
              }
            }

            mapped[col.key] = value;
          }
        });
        return mapped;
      });

      // Simulate progress
      const progressInterval = setInterval(() => {
        setImportProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      await onImport(mappedData);

      clearInterval(progressInterval);
      setImportProgress(100);
      setImportComplete(true);

      // Reset after success
      setTimeout(() => {
        resetImport();
      }, 2000);
    } catch (error) {
      logger.error('Import failed', error);
      setImportError('Import failed. Please try again.');
    } finally {
      setIsImporting(false);
    }
  };

  const resetImport = () => {
    setFile(null);
    setParsedData([]);
    setColumnMapping({});
    setValidationResult(null);
    setImportProgress(0);
    setImportComplete(false);
    setImportError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{title}</h2>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">{description}</p>
      </div>

      {/* Template Download */}
      {templateUrl && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Download Template
                </h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                  Use this template to format your data correctly
                </p>
              </div>
              <Button2 variant="outline" size="sm" onClick={() => window.open(templateUrl, '_blank')}>
                <Download className="h-4 w-4 mr-2" />
                Download CSV Template
              </Button2>
            </div>
          </CardContent>
        </Card>
      )}

      {/* File Upload */}
      {!file && (
        <Card>
          <CardContent className="p-8">
            <div
              className="border-2 border-dashed border-neutral-300 dark:border-neutral-700 rounded-lg p-12 text-center hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                Upload CSV File
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
                Drag and drop your file here, or click to browse
              </p>
              <Button2 variant="outline" size="sm">
                <FileText className="h-4 w-4 mr-2" />
                Select File
              </Button2>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => {
                  const selectedFile = e.target.files?.[0];
                  if (selectedFile) {
                    handleFileSelect(selectedFile);
                  }
                }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* File Info and Preview */}
      {file && parsedData.length > 0 && (
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                      {file.name}
                    </p>
                    <p className="text-xs text-neutral-600 dark:text-neutral-400">
                      {parsedData.length} rows
                    </p>
                  </div>
                </div>
                <Button2 variant="ghost" size="sm" onClick={resetImport}>
                  <X className="h-4 w-4" />
                </Button2>
              </div>
            </CardContent>
          </Card>

          {/* Column Mapping */}
          <Card>
            <CardContent className="p-4">
              <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-4">
                Column Mapping
              </h3>
              <div className="space-y-3">
                {columns.map((col) => (
                  <div key={col.key} className="flex items-center space-x-3">
                    <label className="text-sm text-neutral-700 dark:text-neutral-300 w-1/3">
                      {col.label}
                      {col.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <select
                      className="flex-1 px-3 py-2 border border-neutral-300 dark:border-neutral-700 rounded-md text-sm bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100"
                      value={columnMapping[col.key] || ''}
                      onChange={(e) => {
                        const newMapping = { ...columnMapping, [col.key]: e.target.value };
                        setColumnMapping(newMapping);
                        validateData(parsedData, newMapping);
                      }}
                    >
                      <option value="">-- Select Column --</option>
                      {Object.keys(parsedData[0]).map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Validation Results */}
          {validationResult && (
            <AnimatePresence>
              {validationResult.errors.length > 0 && (
                <m.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <Card className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950">
                    <CardContent className="p-4">
                      <div className="flex items-start space-x-3">
                        <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-red-900 dark:text-red-100 mb-2">
                            Validation Errors
                          </h4>
                          <ul className="text-sm text-red-800 dark:text-red-200 space-y-1">
                            {validationResult.errors.slice(0, 5).map((error, index) => (
                              <li key={index}>• {error}</li>
                            ))}
                            {validationResult.errors.length > 5 && (
                              <li>• ... and {validationResult.errors.length - 5} more errors</li>
                            )}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </m.div>
              )}

              {validationResult.warnings.length > 0 && (
                <m.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <Card className="border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-950">
                    <CardContent className="p-4">
                      <div className="flex items-start space-x-3">
                        <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                            Warnings
                          </h4>
                          <ul className="text-sm text-yellow-800 dark:text-yellow-200 space-y-1">
                            {validationResult.warnings.slice(0, 3).map((warning, index) => (
                              <li key={index}>• {warning}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </m.div>
              )}
            </AnimatePresence>
          )}

          {/* Data Preview */}
          <Card>
            <CardContent className="p-4">
              <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-4">
                Preview (First 5 Rows)
              </h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
                  <thead>
                    <tr>
                      {columns.map((col) => (
                        <th
                          key={col.key}
                          className="px-3 py-2 text-left text-xs font-medium text-neutral-700 dark:text-neutral-300 uppercase tracking-wider"
                        >
                          {col.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
                    {parsedData.slice(0, 5).map((row, index) => (
                      <tr key={index}>
                        {columns.map((col) => {
                          const csvColumn = columnMapping[col.key];
                          const value = csvColumn ? row[csvColumn] : '';
                          return (
                            <td
                              key={col.key}
                              className="px-3 py-2 text-sm text-neutral-900 dark:text-neutral-100"
                            >
                              {value || '-'}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Import Button */}
          <div className="flex justify-end space-x-3">
            <Button2 variant="outline" onClick={resetImport} disabled={isImporting}>
              Cancel
            </Button2>
            <Button2
              onClick={handleImport}
              disabled={!validationResult?.valid || isImporting}
              loading={isImporting}
            >
              {isImporting ? `Importing... ${importProgress}%` : `Import ${parsedData.length} Rows`}
            </Button2>
          </div>
        </m.div>
      )}

      {/* Import Complete */}
      {importComplete && (
        <m.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
          <Card className="max-w-md">
            <CardContent className="p-8 text-center">
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
                Import Complete!
              </h3>
              <p className="text-neutral-600 dark:text-neutral-400">
                Successfully imported {parsedData.length} rows
              </p>
            </CardContent>
          </Card>
        </m.div>
      )}

      {/* Error Message */}
      {importError && (
        <Card className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950">
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-800 dark:text-red-200">{importError}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
