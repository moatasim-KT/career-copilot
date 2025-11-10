/**
 * Demo page to test route prefetching functionality
 * Open DevTools Network tab to see prefetch requests
 */

'use client';

import { useState } from 'react';
import { ArrowRight, Network, CheckCircle2 } from 'lucide-react';

import { PrefetchLink } from '@/components/ui/PrefetchLink';
import { usePrefetchRoutes } from '@/hooks/useRoutePrefetch';

const criticalRoutes = [
  { href: '/dashboard', label: 'Dashboard', description: 'Main dashboard with stats' },
  { href: '/jobs', label: 'Jobs', description: 'Browse job listings' },
  { href: '/applications', label: 'Applications', description: 'Track your applications' },
  { href: '/recommendations', label: 'Recommendations', description: 'AI-powered job matches' },
  { href: '/analytics', label: 'Analytics', description: 'View your job search analytics' },
];

export default function PrefetchDemoPage() {
  const [prefetchedAll, setPrefetchedAll] = useState(false);
  const { prefetchAll } = usePrefetchRoutes(
    criticalRoutes.map(r => r.href),
  );

  const handlePrefetchAll = () => {
    prefetchAll();
    setPrefetchedAll(true);
    setTimeout(() => setPrefetchedAll(false), 2000);
  };

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-neutral-100 mb-4">
            Route Prefetching Demo
          </h1>
          <p className="text-lg text-neutral-600 dark:text-neutral-400 mb-6">
            Open DevTools → Network tab to see prefetch requests in action
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-lg">
            <Network className="w-5 h-5" />
            <span className="text-sm font-medium">
              Hover over links to trigger prefetch after 50ms delay
            </span>
          </div>
        </div>

        {/* Batch Prefetch */}
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700 p-6 mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Batch Prefetch
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            Prefetch all critical routes at once for faster navigation
          </p>
          <button
            onClick={handlePrefetchAll}
            disabled={prefetchedAll}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white rounded-md font-medium transition-colors"
          >
            {prefetchedAll ? (
              <>
                <CheckCircle2 className="w-5 h-5" />
                Prefetched!
              </>
            ) : (
              <>
                <Network className="w-5 h-5" />
                Prefetch All Routes
              </>
            )}
          </button>
        </div>

        {/* Individual Links */}
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700 p-6">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Individual Route Prefetching
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Hover over these links to see individual prefetch requests
          </p>
          
          <div className="space-y-3">
            {criticalRoutes.map((route) => (
              <PrefetchLink
                key={route.href}
                href={route.href}
                className="block p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:border-primary-500 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                      {route.label}
                    </h3>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      {route.description}
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-neutral-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 group-hover:translate-x-1 transition-all" />
                </div>
              </PrefetchLink>
            ))}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            How to Test
          </h3>
          <ol className="space-y-2 text-blue-800 dark:text-blue-200">
            <li className="flex items-start gap-2">
              <span className="font-semibold">1.</span>
              <span>Open Chrome DevTools (F12 or Cmd+Option+I)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-semibold">2.</span>
              <span>Go to the Network tab</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-semibold">3.</span>
              <span>Filter by "Fetch/XHR" or "All"</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-semibold">4.</span>
              <span>Hover over the links above and watch for prefetch requests</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-semibold">5.</span>
              <span>Click a link and notice the instant navigation (data already loaded)</span>
            </li>
          </ol>
        </div>

        {/* Performance Notes */}
        <div className="mt-8 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-3">
            Performance Benefits
          </h3>
          <ul className="space-y-2 text-green-800 dark:text-green-200">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Near-instant page transitions for prefetched routes</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>50ms delay prevents unnecessary prefetches on quick mouse movements</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Each route is only prefetched once to save bandwidth</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Touch devices prefetch immediately on touch for better mobile UX</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
