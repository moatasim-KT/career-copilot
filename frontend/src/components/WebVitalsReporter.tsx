'use client';

/**
 * Web Vitals Reporter Component
 * 
 * This component initializes Web Vitals tracking when the app loads.
 * It should be included once in the root layout.
 */

import { useEffect } from 'react';
import { initWebVitals } from '@/lib/vitals';

export default function WebVitalsReporter() {
  useEffect(() => {
    // Initialize Web Vitals tracking
    initWebVitals();
  }, []);
  
  // This component doesn't render anything
  return null;
}
