/**
 * SWR Pattern Demonstration Component
 * 
 * This component demonstrates the stale-while-revalidate pattern in action.
 * It shows how cached data is displayed immediately while fresh data is fetched.
 */

'use client';

import { useQueryClient } from '@tanstack/react-query';
import React from 'react';

import { useAnalyticsSummary } from '@/hooks/useAnalytics';
import { useApplications } from '@/hooks/useApplications';
import { useJobs } from '@/hooks/useJobs';
import { useUserProfile } from '@/hooks/useUserProfile';
import { queryKeys } from '@/lib/queryClient';
import { useRevalidate, useIsRevalidating } from '@/lib/swr';

/**
 * Demo component showing SWR pattern with jobs data
 */
export function JobsSWRDemo() {
  const { data, isLoading, isStale, isFetching, dataUpdatedAt } = useJobs();
  const { revalidate } = useRevalidate();
  const isRevalidating = useIsRevalidating(queryKeys.jobs.all);

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-6">
      <h3 className="text-lg font-semibold mb-4">Jobs List (SWR Pattern)</h3>

      <div className="space-y-4">
        {/* Status indicators */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500' : 'bg-green-500'}`} />
            <span>{isLoading ? 'Loading...' : 'Loaded'}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isStale ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'}`} />
            <span>{isStale ? 'Revalidating...' : 'Fresh'}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isFetching ? 'bg-purple-500 animate-pulse' : 'bg-gray-400'}`} />
            <span>{isFetching ? 'Fetching...' : 'Idle'}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isRevalidating ? 'bg-indigo-500 animate-pulse' : 'bg-gray-400'}`} />
            <span>{isRevalidating ? 'Background refresh' : 'Cache stable'}</span>
          </div>
        </div>

        {/* Last updated timestamp */}
        <div className="text-sm text-neutral-600 dark:text-neutral-400">
          Last updated: {dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : 'Never'}
        </div>

        {/* Data display */}
        <div className="bg-neutral-50 dark:bg-neutral-900 rounded p-4">
          {isLoading && !data ? (
            <p className="text-neutral-500">Loading initial data...</p>
          ) : (
            <>
              <p className="font-medium mb-2">
                {data?.length || 0} jobs loaded
              </p>
              {isStale && (
                <p className="text-sm text-blue-600 dark:text-blue-400">
                  ✨ Showing cached data while fetching fresh data...
                </p>
              )}
            </>
          )}
        </div>

        {/* Manual revalidation button */}
        <button
          onClick={() => revalidate(queryKeys.jobs.all)}
          disabled={isFetching}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isFetching ? 'Revalidating...' : 'Revalidate Now'}
        </button>
      </div>
    </div>
  );
}

/**
 * Demo component showing SWR pattern with applications data
 */
export function ApplicationsSWRDemo() {
  const { data, isLoading, isFetching, dataUpdatedAt } = useApplications();
  const { revalidate } = useRevalidate();
  const queryClient = useQueryClient();

  // Check if data is stale (being revalidated)
  const queryState = queryClient.getQueryState(queryKeys.applications.all);
  const isStale = queryState?.fetchStatus === 'fetching' && queryState?.status === 'success';

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-6">
      <h3 className="text-lg font-semibold mb-4">Applications List (SWR Pattern)</h3>

      <div className="space-y-4">
        {/* Status indicators */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500' : 'bg-green-500'}`} />
            <span>{isLoading ? 'Loading...' : 'Loaded'}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isStale ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'}`} />
            <span>{isStale ? 'Revalidating...' : 'Fresh'}</span>
          </div>
        </div>

        {/* Last updated timestamp */}
        <div className="text-sm text-neutral-600 dark:text-neutral-400">
          Last updated: {dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : 'Never'}
        </div>

        {/* Data display */}
        <div className="bg-neutral-50 dark:bg-neutral-900 rounded p-4">
          {isLoading && !data ? (
            <p className="text-neutral-500">Loading initial data...</p>
          ) : (
            <>
              <p className="font-medium mb-2">
                {data?.length || 0} applications loaded
              </p>
              {isStale && (
                <p className="text-sm text-blue-600 dark:text-blue-400">
                  ✨ Showing cached data while fetching fresh data...
                </p>
              )}
            </>
          )}
        </div>

        {/* Manual revalidation button */}
        <button
          onClick={() => revalidate(queryKeys.applications.all)}
          disabled={isFetching}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isFetching ? 'Revalidating...' : 'Revalidate Now'}
        </button>
      </div>
    </div>
  );
}

/**
 * Demo component showing SWR pattern with user profile
 */
export function UserProfileSWRDemo() {
  const { data, isLoading, isFetching, dataUpdatedAt } = useUserProfile();
  const { revalidate } = useRevalidate();

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-6">
      <h3 className="text-lg font-semibold mb-4">User Profile (SWR Pattern)</h3>

      <div className="space-y-4">
        {/* Status indicators */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500' : 'bg-green-500'}`} />
            <span>{isLoading ? 'Loading...' : 'Loaded'}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isFetching && !isLoading ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'}`} />
            <span>{isFetching && !isLoading ? 'Revalidating...' : 'Fresh'}</span>
          </div>
        </div>

        {/* Cache info */}
        <div className="text-sm text-neutral-600 dark:text-neutral-400">
          <p>Stale time: 30 minutes</p>
          <p>Refetch on window focus: Yes</p>
          <p>Last updated: {dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : 'Never'}</p>
        </div>

        {/* Data display */}
        <div className="bg-neutral-50 dark:bg-neutral-900 rounded p-4">
          {isLoading && !data ? (
            <p className="text-neutral-500">Loading profile...</p>
          ) : data ? (
            <>
              <p className="font-medium">{data.full_name || data.username}</p>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">{data.email}</p>
              {isFetching && !isLoading && (
                <p className="text-sm text-blue-600 dark:text-blue-400 mt-2">
                  ✨ Showing cached profile while fetching updates...
                </p>
              )}
            </>
          ) : (
            <p className="text-neutral-500">No profile data</p>
          )}
        </div>

        {/* Manual revalidation button */}
        <button
          onClick={() => revalidate(queryKeys.userProfile.current())}
          disabled={isFetching}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isFetching ? 'Revalidating...' : 'Revalidate Now'}
        </button>
      </div>
    </div>
  );
}

/**
 * Demo component showing SWR pattern with analytics
 */
export function AnalyticsSWRDemo() {
  const { data, isLoading, isFetching, dataUpdatedAt } = useAnalyticsSummary();
  const { revalidate } = useRevalidate();

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-6">
      <h3 className="text-lg font-semibold mb-4">Analytics (SWR Pattern)</h3>

      <div className="space-y-4">
        {/* Status indicators */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500' : 'bg-green-500'}`} />
            <span>{isLoading ? 'Loading...' : 'Loaded'}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isFetching && !isLoading ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'}`} />
            <span>{isFetching && !isLoading ? 'Revalidating...' : 'Fresh'}</span>
          </div>
        </div>

        {/* Cache info */}
        <div className="text-sm text-neutral-600 dark:text-neutral-400">
          <p>Stale time: 10 minutes</p>
          <p>Auto-refetch: No</p>
          <p>Last updated: {dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : 'Never'}</p>
        </div>

        {/* Data display */}
        <div className="bg-neutral-50 dark:bg-neutral-900 rounded p-4">
          {isLoading && !data ? (
            <p className="text-neutral-500">Loading analytics...</p>
          ) : data ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">Total Jobs</p>
                  <p className="text-2xl font-bold">{data.total_jobs}</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">Applications</p>
                  <p className="text-2xl font-bold">{data.total_applications}</p>
                </div>
              </div>
              {isFetching && !isLoading && (
                <p className="text-sm text-blue-600 dark:text-blue-400 mt-2">
                  ✨ Showing cached analytics while fetching updates...
                </p>
              )}
            </>
          ) : (
            <p className="text-neutral-500">No analytics data</p>
          )}
        </div>

        {/* Manual revalidation button */}
        <button
          onClick={() => revalidate(queryKeys.analytics.summary())}
          disabled={isFetching}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isFetching ? 'Revalidating...' : 'Revalidate Now'}
        </button>
      </div>
    </div>
  );
}

/**
 * Main demo page component
 */
export function SWRDemoPage() {
  const { revalidateAll } = useRevalidate();
  const isRevalidating = useIsRevalidating();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Stale-While-Revalidate Pattern Demo</h1>
        <p className="text-neutral-600 dark:text-neutral-400">
          This page demonstrates the SWR pattern. Cached data is shown immediately while fresh data is fetched in the background.
        </p>

        <div className="mt-4 flex items-center gap-4">
          <button
            onClick={() => revalidateAll()}
            disabled={isRevalidating}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRevalidating ? 'Revalidating All...' : 'Revalidate All Queries'}
          </button>

          {isRevalidating && (
            <span className="text-sm text-blue-600 dark:text-blue-400">
              Some queries are being revalidated...
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <JobsSWRDemo />
        <ApplicationsSWRDemo />
        <UserProfileSWRDemo />
        <AnalyticsSWRDemo />
      </div>

      <div className="mt-8 p-6 bg-blue-50 dark:bg-blue-950 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">How SWR Works</h3>
        <ul className="space-y-2 text-sm">
          <li>✅ <strong>Instant UI:</strong> Cached data is shown immediately</li>
          <li>✅ <strong>Background Revalidation:</strong> Fresh data is fetched in the background</li>
          <li>✅ <strong>Automatic Updates:</strong> UI updates when fresh data arrives</li>
          <li>✅ <strong>Smart Caching:</strong> Different stale times for different data types</li>
          <li>✅ <strong>Focus Revalidation:</strong> Some queries refetch when you return to the tab</li>
        </ul>
      </div>
    </div>
  );
}
