'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Maximize, Minimize, Download, FileDown, Image as ImageIcon, AlertCircle, X } from 'lucide-react';
import { Card2 } from '@/components/ui/Card2';
import { Button2 } from '@/components/ui/Button2';
import { Tooltip } from '@/components/ui/Tooltip';
import { Modal2 } from '@/components/ui/Modal2';

interface ChartWrapperProps {
  title: string;
  description?: string;
  isLoading?: boolean;
  error?: string | null;
  children: React.ReactNode;
  onExportCSV?: () => void;
  onExportPNG?: () => void;
  actions?: React.ReactNode;
  className?: string;
}

/**
 * ChartWrapper - A comprehensive wrapper component for data visualization charts
 * 
 * Features:
 * - Consistent styling with design tokens
 * - Loading skeleton state
 * - Error state with retry option
 * - Export buttons (CSV, PNG)
 * - Full-screen mode toggle
 * - Dark mode support
 * - Responsive layout
 * - Smooth animations
 */
export const ChartWrapper: React.FC<ChartWrapperProps> = ({
  title,
  description,
  isLoading = false,
  error = null,
  children,
  onExportCSV,
  onExportPNG,
  actions,
  className = '',
}) => {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

  const handleFullScreenToggle = () => {
    setIsFullScreen(!isFullScreen);
  };

  const handleExportCSV = () => {
    if (onExportCSV) {
      onExportCSV();
      setShowExportMenu(false);
    }
  };

  const handleExportPNG = () => {
    if (onExportPNG) {
      onExportPNG();
      setShowExportMenu(false);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="h-[300px] w-full animate-pulse">
          <div className="h-full w-full bg-neutral-200 dark:bg-neutral-700 rounded-lg flex items-center justify-center">
            <div className="space-y-3 text-center">
              <div className="h-4 w-32 bg-neutral-300 dark:bg-neutral-600 rounded mx-auto"></div>
              <div className="h-3 w-24 bg-neutral-300 dark:bg-neutral-600 rounded mx-auto"></div>
            </div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="h-[300px] w-full flex items-center justify-center">
          <div className="text-center space-y-4">
            <AlertCircle className="h-12 w-12 text-error-500 mx-auto" />
            <div>
              <p className="text-error-600 dark:text-error-400 font-medium">
                Error loading chart data
              </p>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                {error}
              </p>
            </div>
            <Button2
              variant="outline"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button2>
          </div>
        </div>
      );
    }

    return children;
  };

  const chartContent = (
    <Card2 className={`${className} ${isFullScreen ? 'h-full' : ''}`}>
      <div className="p-4 sm:p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {title}
            </h3>
            {description && (
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                {description}
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 ml-4">
            {actions}
            
            {/* Export Menu */}
            {(onExportCSV || onExportPNG) && (
              <div className="relative">
                <Tooltip content="Export chart">
                  <Button2
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowExportMenu(!showExportMenu)}
                    aria-label="Export chart"
                  >
                    <Download className="h-4 w-4" />
                  </Button2>
                </Tooltip>

                <AnimatePresence>
                  {showExportMenu && (
                    <>
                      {/* Backdrop */}
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setShowExportMenu(false)}
                      />
                      
                      {/* Menu */}
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -10 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 mt-2 w-48 bg-white dark:bg-neutral-800 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-700 py-1 z-50"
                      >
                        {onExportCSV && (
                          <button
                            onClick={handleExportCSV}
                            className="w-full px-4 py-2 text-left text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center space-x-2"
                          >
                            <FileDown className="h-4 w-4" />
                            <span>Export as CSV</span>
                          </button>
                        )}
                        {onExportPNG && (
                          <button
                            onClick={handleExportPNG}
                            className="w-full px-4 py-2 text-left text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center space-x-2"
                          >
                            <ImageIcon className="h-4 w-4" />
                            <span>Export as PNG</span>
                          </button>
                        )}
                      </motion.div>
                    </>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Full Screen Toggle */}
            <Tooltip content={isFullScreen ? 'Exit full screen' : 'Full screen'}>
              <Button2
                variant="ghost"
                size="sm"
                onClick={handleFullScreenToggle}
                aria-label={isFullScreen ? 'Exit full screen' : 'Enter full screen'}
              >
                {isFullScreen ? (
                  <Minimize className="h-4 w-4" />
                ) : (
                  <Maximize className="h-4 w-4" />
                )}
              </Button2>
            </Tooltip>
          </div>
        </div>

        {/* Chart Content */}
        <div className={isFullScreen ? 'h-[calc(100vh-200px)]' : ''}>
          {renderContent()}
        </div>
      </div>
    </Card2>
  );

  // Render in modal if full screen
  if (isFullScreen) {
    return (
      <Modal2
        isOpen={isFullScreen}
        onClose={() => setIsFullScreen(false)}
        title={title}
        size="full"
      >
        <div className="h-full">
          {chartContent}
        </div>
      </Modal2>
    );
  }

  return chartContent;
};

export default ChartWrapper;
