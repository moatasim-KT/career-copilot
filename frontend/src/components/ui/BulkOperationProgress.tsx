'use client';

import { X, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import React from 'react';

import { m, AnimatePresence } from '@/lib/motion';

import Button2 from './Button2';
import Modal from './Modal2';

export interface BulkOperationError {
  itemId: string | number;
  itemName: string;
  error: string;
}

export interface BulkOperationProgressProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  totalItems: number;
  processedItems: number;
  successCount: number;
  failureCount: number;
  errors?: BulkOperationError[];
  isComplete: boolean;
  isCancellable?: boolean;
  onCancel?: () => void;
  onRetry?: (failedItemIds: (string | number)[]) => void;
}

export function BulkOperationProgress({
  isOpen,
  onClose,
  title,
  totalItems,
  processedItems,
  successCount,
  failureCount,
  errors = [],
  isComplete,
  isCancellable = false,
  onCancel,
  onRetry,
}: BulkOperationProgressProps) {
  const progress = totalItems > 0 ? (processedItems / totalItems) * 100 : 0;
  const hasErrors = errors.length > 0;

  const handleRetry = () => {
    if (onRetry && errors.length > 0) {
      const failedIds = errors.map(e => e.itemId);
      onRetry(failedIds);
    }
  };

  return (
    <Modal
      open={isOpen}
      onClose={isComplete ? onClose : () => { }}
      title={title}
      size="md"
    >
      <div className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-neutral-700 dark:text-neutral-300">
              {isComplete ? 'Complete' : 'Processing...'}
            </span>
            <span className="text-neutral-600 dark:text-neutral-400">
              {processedItems} of {totalItems} items
            </span>
          </div>

          {/* Progress Bar Container */}
          <div className="relative h-3 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
            <m.div
              className={`absolute inset-y-0 left-0 rounded-full ${hasErrors && isComplete
                ? 'bg-yellow-500 dark:bg-yellow-600'
                : 'bg-blue-600 dark:bg-blue-500'
                }`}
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{
                duration: 0.3,
                ease: 'easeOut',
              }}
            />

            {/* Animated shimmer effect while processing */}
            {!isComplete && (
              <m.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                animate={{
                  x: ['-100%', '100%'],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
            )}
          </div>

          {/* Progress Percentage */}
          <div className="text-center">
            <m.span
              key={progress}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-2xl font-bold text-neutral-900 dark:text-neutral-100"
            >
              {Math.round(progress)}%
            </m.span>
          </div>
        </div>

        {/* Status Text */}
        <div className="text-center">
          <AnimatePresence mode="wait">
            {!isComplete ? (
              <m.p
                key="processing"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-sm text-neutral-600 dark:text-neutral-400"
              >
                Processing {processedItems} of {totalItems} items...
              </m.p>
            ) : (
              <m.div
                key="complete"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="space-y-2"
              >
                <div className="flex items-center justify-center space-x-2">
                  {hasErrors ? (
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    {hasErrors ? 'Completed with errors' : 'Successfully completed'}
                  </p>
                </div>
              </m.div>
            )}
          </AnimatePresence>
        </div>

        {/* Success/Failure Summary */}
        {isComplete && (
          <m.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 gap-4"
          >
            {/* Success Count */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                <div>
                  <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                    {successCount}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400">
                    Successful
                  </p>
                </div>
              </div>
            </div>

            {/* Failure Count */}
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                <div>
                  <p className="text-2xl font-bold text-red-700 dark:text-red-300">
                    {failureCount}
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400">
                    Failed
                  </p>
                </div>
              </div>
            </div>
          </m.div>
        )}

        {/* Error List */}
        {hasErrors && isComplete && (
          <m.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-2"
          >
            <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              Failed Items:
            </p>
            <div className="max-h-48 overflow-y-auto space-y-2 bg-neutral-50 dark:bg-neutral-800 rounded-lg p-3">
              {errors.map((error, index) => (
                <m.div
                  key={error.itemId}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start space-x-2 text-sm"
                >
                  <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-neutral-900 dark:text-neutral-100 truncate">
                      {error.itemName}
                    </p>
                    <p className="text-xs text-red-600 dark:text-red-400">
                      {error.error}
                    </p>
                  </div>
                </m.div>
              ))}
            </div>
          </m.div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-2 pt-4 border-t border-neutral-200 dark:border-neutral-700">
          {!isComplete && isCancellable && onCancel && (
            <Button2
              variant="outline"
              onClick={onCancel}
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button2>
          )}

          {isComplete && hasErrors && onRetry && (
            <Button2
              variant="outline"
              onClick={handleRetry}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry Failed ({failureCount})
            </Button2>
          )}

          {isComplete && (
            <Button2
              variant="primary"
              onClick={onClose}
            >
              Close
            </Button2>
          )}
        </div>
      </div>
    </Modal>
  );
}
