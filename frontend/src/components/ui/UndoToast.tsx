'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Undo2, X } from 'lucide-react';
import React, { useEffect, useState } from 'react';

import Button2 from './Button2';

export interface UndoToastProps {
  isVisible: boolean;
  message: string;
  onUndo: () => void;
  onDismiss: () => void;
  timeout?: number; // in milliseconds
  isUndoing?: boolean;
}

export function UndoToast({
  isVisible,
  message,
  onUndo,
  onDismiss,
  timeout = 5000,
  isUndoing = false,
}: UndoToastProps) {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (!isVisible) {
      setProgress(100);
      return;
    }

    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, timeout - elapsed);
      const newProgress = (remaining / timeout) * 100;
      
      setProgress(newProgress);

      if (remaining === 0) {
        clearInterval(interval);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [isVisible, timeout]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: 100, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 100, opacity: 0, scale: 0.95 }}
          transition={{
            type: 'spring',
            stiffness: 400,
            damping: 30,
          }}
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
        >
          <div
            className="
              relative
              min-w-[320px]
              max-w-md
              bg-neutral-900 dark:bg-neutral-800
              text-white
              rounded-lg
              shadow-2xl
              overflow-hidden
            "
          >
            {/* Progress Bar */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-neutral-700">
              <motion.div
                className="h-full bg-blue-500"
                initial={{ width: '100%' }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.05, ease: 'linear' }}
              />
            </div>

            {/* Content */}
            <div className="flex items-center justify-between p-4 pt-5">
              <div className="flex items-center space-x-3 flex-1">
                <motion.div
                  initial={{ rotate: -180, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  transition={{
                    type: 'spring',
                    stiffness: 300,
                    damping: 20,
                  }}
                >
                  <Undo2 className="h-5 w-5 text-blue-400" />
                </motion.div>
                <p className="text-sm font-medium">{message}</p>
              </div>

              <div className="flex items-center space-x-2 ml-4">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button2
                    variant="ghost"
                    size="sm"
                    onClick={onUndo}
                    disabled={isUndoing}
                    loading={isUndoing}
                    className="
                      text-blue-400 hover:text-blue-300
                      hover:bg-blue-500/20
                      font-semibold
                    "
                  >
                    Undo
                  </Button2>
                </motion.div>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={onDismiss}
                  disabled={isUndoing}
                  className="
                    p-1
                    rounded
                    text-neutral-400
                    hover:text-white
                    hover:bg-neutral-700
                    transition-colors
                    disabled:opacity-50
                    disabled:cursor-not-allowed
                  "
                  aria-label="Dismiss"
                >
                  <X className="h-4 w-4" />
                </motion.button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
