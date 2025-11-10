'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import React from 'react';

import Button2 from './Button2';

export interface BulkAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'destructive' | 'outline' | 'ghost';
  requiresConfirmation?: boolean;
  action: (selectedIds: string[] | number[]) => Promise<void> | void;
  disabled?: boolean;
}

export interface BulkActionBarProps {
  selectedCount: number;
  selectedIds: string[] | number[];
  actions: BulkAction[];
  onClearSelection: () => void;
  className?: string;
}

export function BulkActionBar({
  selectedCount,
  selectedIds,
  actions,
  onClearSelection,
  className = '',
}: BulkActionBarProps) {
  const [isExecuting, setIsExecuting] = React.useState(false);
  const [executingActionId, setExecutingActionId] = React.useState<string | null>(null);

  const handleActionClick = async (action: BulkAction) => {
    if (action.disabled || isExecuting) return;

    setIsExecuting(true);
    setExecutingActionId(action.id);

    try {
      await action.action(selectedIds);
    } catch (error) {
      console.error('Bulk action failed:', error);
    } finally {
      setIsExecuting(false);
      setExecutingActionId(null);
    }
  };

  return (
    <AnimatePresence>
      {selectedCount > 0 && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{
            type: 'spring',
            stiffness: 300,
            damping: 30,
          }}
          className={`fixed bottom-0 left-0 right-0 z-50 ${className}`}
        >
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-6">
            <div
              className="
                glass
                rounded-lg
                border border-neutral-200 dark:border-neutral-700
                bg-white/90 dark:bg-neutral-900/90
                backdrop-blur-lg
                shadow-2xl
                p-4
              "
            >
              <div className="flex items-center justify-between gap-4">
                {/* Selection Count */}
                <div className="flex items-center space-x-3">
                  <motion.div
                    key={selectedCount}
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{
                      type: 'spring',
                      stiffness: 400,
                      damping: 20,
                    }}
                    className="
                      flex items-center justify-center
                      h-10 w-10
                      rounded-full
                      bg-blue-100 dark:bg-blue-900/30
                      text-blue-600 dark:text-blue-400
                      font-semibold
                      text-sm
                    "
                  >
                    {selectedCount}
                  </motion.div>
                  <div>
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                      {selectedCount} {selectedCount === 1 ? 'item' : 'items'} selected
                    </p>
                    <p className="text-xs text-neutral-600 dark:text-neutral-400">
                      Choose an action to apply
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2">
                  {actions.map((action) => {
                    const Icon = action.icon;
                    const isThisActionExecuting = executingActionId === action.id;

                    return (
                      <motion.div
                        key={action.id}
                        whileHover={{ scale: action.disabled ? 1 : 1.02 }}
                        whileTap={{ scale: action.disabled ? 1 : 0.98 }}
                      >
                        <Button2
                          variant={action.variant || 'default'}
                          onClick={() => handleActionClick(action)}
                          disabled={action.disabled || isExecuting}
                          loading={isThisActionExecuting}
                          className="flex items-center space-x-2"
                        >
                          {!isThisActionExecuting && <Icon className="h-4 w-4" />}
                          <span>{action.label}</span>
                        </Button2>
                      </motion.div>
                    );
                  })}

                  {/* Clear Selection Button */}
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button2
                      variant="ghost"
                      onClick={onClearSelection}
                      disabled={isExecuting}
                      className="flex items-center space-x-2"
                      title="Clear selection"
                    >
                      <X className="h-4 w-4" />
                      <span className="hidden sm:inline">Clear</span>
                    </Button2>
                  </motion.div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
