'use client';

import { AlertTriangle } from 'lucide-react';
import React from 'react';

import { m } from '@/lib/motion';

import Button2 from './Button2';
import Modal, { ModalFooter } from './Modal';

export interface ConfirmBulkActionProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  itemCount: number;
  itemNames?: string[];
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  showDontAskAgain?: boolean;
  onDontAskAgainChange?: (checked: boolean) => void;
}

export function ConfirmBulkAction({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  itemCount,
  itemNames = [],
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isDestructive = false,
  showDontAskAgain = false,
  onDontAskAgainChange,
}: ConfirmBulkActionProps) {
  const [dontAskAgain, setDontAskAgain] = React.useState(false);
  const [isConfirming, setIsConfirming] = React.useState(false);

  const handleConfirm = async () => {
    setIsConfirming(true);

    if (showDontAskAgain && dontAskAgain && onDontAskAgainChange) {
      onDontAskAgainChange(true);
    }

    try {
      await onConfirm();
    } finally {
      setIsConfirming(false);
      onClose();
    }
  };

  const handleDontAskAgainChange = (checked: boolean) => {
    setDontAskAgain(checked);
  };

  // Show first 5 items, then "and X more"
  const displayItems = itemNames.slice(0, 5);
  const remainingCount = itemCount - displayItems.length;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="md"
    >
      <div className="space-y-4">
        {/* Warning Icon and Message */}
        <div className="flex items-start space-x-3">
          {isDestructive && (
            <m.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{
                type: 'spring',
                stiffness: 400,
                damping: 20,
              }}
              className="flex-shrink-0"
            >
              <div className="flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/30">
                <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
            </m.div>
          )}
          <div className="flex-1">
            <p className="text-sm text-neutral-700 dark:text-neutral-300">
              {message}
            </p>
          </div>
        </div>

        {/* Item Count */}
        <div className="bg-neutral-50 dark:bg-neutral-800 rounded-lg p-4">
          <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
            {itemCount} {itemCount === 1 ? 'item' : 'items'} will be affected:
          </p>

          {/* List of Items */}
          {displayItems.length > 0 && (
            <ul className="space-y-1">
              {displayItems.map((item, index) => (
                <m.li
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="text-sm text-neutral-600 dark:text-neutral-400 flex items-center space-x-2"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 dark:bg-neutral-500" />
                  <span className="truncate">{item}</span>
                </m.li>
              ))}
            </ul>
          )}

          {/* Remaining Count */}
          {remainingCount > 0 && (
            <m.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-sm text-neutral-500 dark:text-neutral-400 mt-2 italic"
            >
              and {remainingCount} more...
            </m.p>
          )}
        </div>

        {/* Warning Message for Destructive Actions */}
        {isDestructive && (
          <m.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3"
          >
            <p className="text-sm font-medium text-red-800 dark:text-red-300">
              ⚠️ This action cannot be undone
            </p>
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">
              Please confirm that you want to proceed with this operation.
            </p>
          </m.div>
        )}

        {/* Don't Ask Again Checkbox */}
        {showDontAskAgain && (
          <m.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex items-center space-x-2 pt-2 border-t border-neutral-200 dark:border-neutral-700"
          >
            <input
              type="checkbox"
              id="dont-ask-again"
              checked={dontAskAgain}
              onChange={(e) => handleDontAskAgainChange(e.target.checked)}
              className="
                h-4 w-4
                rounded
                border-neutral-300 dark:border-neutral-600
                text-blue-600 dark:text-blue-500
                focus:ring-blue-500 dark:focus:ring-blue-400
                focus:ring-offset-0
              "
            />
            <label
              htmlFor="dont-ask-again"
              className="text-sm text-neutral-700 dark:text-neutral-300 cursor-pointer select-none"
            >
              Don&apos;t ask me again for this action
            </label>
          </m.div>
        )}
      </div>

      <ModalFooter>
        <Button2
          type="button"
          variant="outline"
          onClick={onClose}
          disabled={isConfirming}
        >
          {cancelLabel}
        </Button2>
        <Button2
          type="button"
          variant={isDestructive ? 'destructive' : 'primary'}
          onClick={handleConfirm}
          loading={isConfirming}
        >
          {confirmLabel}
        </Button2>
      </ModalFooter>
    </Modal>
  );
}
