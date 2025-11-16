/**
 * Prefetching Demonstration Components
 * 
 * These components demonstrate various prefetching strategies.
 */

'use client';

import Link from 'next/link';
import React, { useState } from 'react';

import { useApplications } from '@/hooks/useApplications';
import { useJobs } from '@/hooks/useJobs';
import { logger } from '@/lib/logger';
import {
  usePrefetchJob,
  usePrefetchApplication,
  usePrefetchNextPage,
  usePrefetchOnScroll,
  usePrefetchRoute,
} from '@/lib/prefetch';

/**
 * Job card with hover prefetch
 */
export function JobCardWithPrefetch({ job }: { job: any }) {
  const prefetchJob = usePrefetchJob();

  return (
    <Link
      href={`/jobs/${job.id}`}
      onMouseEnter={() => prefetchJob(job.id)}
      className="block p-4 border border-neutral-200 dark:border-neutral-800 rounded-lg hover:border-primary-500 transition-colors"
    >
      <h3 className="font-semibold">{job.title}</h3>
      <p className="text-sm text-neutral-600 dark:text-neutral-400">{job.company}</p>
      <p className="text-xs text-neutral-500 mt-2">
        Hover to prefetch details
      </p>
    </Link>
  );
}

/**
 * Application card with hover prefetch
 */
export function ApplicationCardWithPrefetch({ application }: { application: any }) {
  const prefetchApplication = usePrefetchApplication();

  return (
    <Link
      href={`/applications/${application.id}`}
      onMouseEnter={() => prefetchApplication(application.id)}
      className="block p-4 border border-neutral-200 dark:border-neutral-800 rounded-lg hover:border-primary-500 transition-colors"
    >
      <h3 className="font-semibold">{application.job?.title || 'Application'}</h3>
      <p className="text-sm text-neutral-600 dark:text-neutral-400">
        Status: {application.status}
      </p>
      <p className="text-xs text-neutral-500 mt-2">
        Hover to prefetch details
      </p>
    </Link>
  );
}

/**
 * Jobs list with next page prefetch
 */
export function JobsListWithPrefetch() {
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data: jobs, isLoading } = useJobs({ skip: page * pageSize, limit: pageSize });

  const { observerRef } = usePrefetchNextPage({
    currentPage: page,
    pageSize,
    totalItems: 100, // In real app, this would come from API
    onPrefetch: async () => {
      // Prefetch next page
      // In real implementation, this would use prefetchJobs
      logger.info('Prefetching next page:', page + 1);
    },
  });

  if (isLoading) {
    return <div className="p-4">Loading jobs...</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Jobs (Page {page + 1})</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {jobs?.map((job: any) => (
          <JobCardWithPrefetch key={job.id} job={job} />
        ))}
      </div>

      {/* Sentinel element for intersection observer */}
      <div ref={observerRef} className="h-4" />

      <div className="flex gap-4">
        <button
          onClick={() => setPage(p => Math.max(0, p - 1))}
          disabled={page === 0}
          className="px-4 py-2 bg-neutral-200 dark:bg-neutral-800 rounded disabled:opacity-50"
        >
          Previous
        </button>
        <button
          onClick={() => setPage(p => p + 1)}
          className="px-4 py-2 bg-primary-600 text-white rounded"
        >
          Next
        </button>
      </div>

      <p className="text-sm text-neutral-600 dark:text-neutral-400">
        Next page will be prefetched when you scroll near the bottom
      </p>
    </div>
  );
}

/**
 * Applications list with scroll prefetch
 */
export function ApplicationsListWithPrefetch() {
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data: applications, isLoading } = useApplications({ skip: page * pageSize, limit: pageSize });

  usePrefetchOnScroll({
    onPrefetch: async () => {
      // Prefetch next page
      logger.info('Prefetching next page on scroll:', page + 1);
      setPage(p => p + 1);
    },
    threshold: 0.8,
    enabled: true,
  });

  if (isLoading) {
    return <div className="p-4">Loading applications...</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Applications (Page {page + 1})</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {applications?.map((app: any) => (
          <ApplicationCardWithPrefetch key={app.id} application={app} />
        ))}
      </div>

      <p className="text-sm text-neutral-600 dark:text-neutral-400">
        Scroll down to automatically load and prefetch more applications
      </p>
    </div>
  );
}

/**
 * Navigation with route prefetch
 */
export function NavigationWithPrefetch() {
  const { prefetchDashboard, prefetchJobsPage, prefetchApplicationsPage } = usePrefetchRoute();

  return (
    <nav className="flex gap-4 p-4 bg-neutral-100 dark:bg-neutral-900 rounded-lg">
      <Link
        href="/dashboard"
        onMouseEnter={() => prefetchDashboard()}
        className="px-4 py-2 bg-white dark:bg-neutral-800 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
      >
        Dashboard
      </Link>

      <Link
        href="/jobs"
        onMouseEnter={() => prefetchJobsPage()}
        className="px-4 py-2 bg-white dark:bg-neutral-800 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
      >
        Jobs
      </Link>

      <Link
        href="/applications"
        onMouseEnter={() => prefetchApplicationsPage()}
        className="px-4 py-2 bg-white dark:bg-neutral-800 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
      >
        Applications
      </Link>

      <p className="ml-auto text-sm text-neutral-600 dark:text-neutral-400 self-center">
        Hover over links to prefetch page data
      </p>
    </nav>
  );
}

/**
 * Main prefetch demo page
 */
export function PrefetchDemoPage() {
  const [activeDemo, setActiveDemo] = useState<'jobs' | 'applications' | 'navigation'>('jobs');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Prefetching Demo</h1>
        <p className="text-neutral-600 dark:text-neutral-400">
          This page demonstrates various prefetching strategies to improve perceived performance.
        </p>
      </div>

      <div className="mb-6 flex gap-4">
        <button
          onClick={() => setActiveDemo('jobs')}
          className={`px-4 py-2 rounded ${activeDemo === 'jobs'
            ? 'bg-primary-600 text-white'
            : 'bg-neutral-200 dark:bg-neutral-800'
            }`}
        >
          Jobs (Hover + Next Page)
        </button>
        <button
          onClick={() => setActiveDemo('applications')}
          className={`px-4 py-2 rounded ${activeDemo === 'applications'
            ? 'bg-primary-600 text-white'
            : 'bg-neutral-200 dark:bg-neutral-800'
            }`}
        >
          Applications (Scroll)
        </button>
        <button
          onClick={() => setActiveDemo('navigation')}
          className={`px-4 py-2 rounded ${activeDemo === 'navigation'
            ? 'bg-primary-600 text-white'
            : 'bg-neutral-200 dark:bg-neutral-800'
            }`}
        >
          Navigation (Route)
        </button>
      </div>

      <div className="mb-8">
        {activeDemo === 'jobs' && <JobsListWithPrefetch />}
        {activeDemo === 'applications' && <ApplicationsListWithPrefetch />}
        {activeDemo === 'navigation' && <NavigationWithPrefetch />}
      </div>

      <div className="p-6 bg-blue-50 dark:bg-blue-950 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Prefetching Strategies</h3>
        <ul className="space-y-2 text-sm">
          <li>✅ <strong>Hover Prefetch:</strong> Data is prefetched when you hover over a link or card</li>
          <li>✅ <strong>Next Page Prefetch:</strong> Next page is prefetched when you&rsquo;re near the end of the current page</li>
          <li>✅ <strong>Scroll Prefetch:</strong> Data is prefetched when you scroll past a threshold</li>
          <li>✅ <strong>Route Prefetch:</strong> Page data is prefetched when you hover over navigation links</li>
          <li>✅ <strong>Related Data Prefetch:</strong> Related data is automatically prefetched</li>
        </ul>
      </div>
    </div>
  );
}
