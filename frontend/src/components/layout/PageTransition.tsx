'use client';

import { AnimatePresence, motion } from 'framer-motion';
import React from 'react';
import { pageTransition } from '@/lib/animations';

interface PageTransitionProps {
  children: React.ReactNode;
  /**
   * Optional key used to trigger AnimatePresence transitions when route changes.
   * If you pass a dynamic key (like pathname) the wrapper will animate between keys.
   */
  transitionKey?: string | number;
}

export default function PageTransition({ children, transitionKey = 'page' }: PageTransitionProps) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={transitionKey}
        variants={pageTransition}
        initial="initial"
        animate="animate"
        exit="exit"
        style={{ minHeight: '100vh' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
