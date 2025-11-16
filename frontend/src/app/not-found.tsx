/**
 * 404 Not Found Page
 * 
 * Custom 404 error page with helpful navigation and search.
 * 
 * @module app/not-found
 */

'use client';

import { FileQuestion, Home, Search, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900 px-4 py-8">
      <div className="max-w-2xl w-full text-center">
        {/* 404 Illustration */}
        <div className="flex items-center justify-center mb-8">
          <div className="relative">
            <div className="text-9xl font-bold text-neutral-200 dark:text-neutral-800">404</div>
            <div className="absolute inset-0 flex items-center justify-center">
              <FileQuestion className="h-20 w-20 text-neutral-400 dark:text-neutral-600" />
            </div>
          </div>
        </div>

        {/* Error message */}
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Page Not Found
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
          Sorry, we couldn&apos;t find the page you&apos;re looking for. It might have been moved or deleted.
        </p>

        {/* Search bar */}
        <div className="max-w-md mx-auto mb-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search for jobs, applications..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-neutral-700 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const query = e.currentTarget.value;
                  if (query) {
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                  }
                }
              }}
            />
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            <Home className="h-5 w-5" />
            Go to Dashboard
          </Link>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors font-medium"
          >
            <ArrowLeft className="h-5 w-5" />
            Go Back
          </button>
        </div>

        {/* Helpful links */}
        <div className="border-t border-gray-200 dark:border-neutral-800 pt-8">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            Popular Pages
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Link
              href="/jobs"
              className="p-4 bg-white dark:bg-neutral-800 rounded-lg hover:shadow-md transition-shadow text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
            >
              <div className="font-medium">Jobs</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Browse openings</div>
            </Link>
            <Link
              href="/applications"
              className="p-4 bg-white dark:bg-neutral-800 rounded-lg hover:shadow-md transition-shadow text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
            >
              <div className="font-medium">Applications</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Track progress</div>
            </Link>
            <Link
              href="/recommendations"
              className="p-4 bg-white dark:bg-neutral-800 rounded-lg hover:shadow-md transition-shadow text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
            >
              <div className="font-medium">Recommendations</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Job matches</div>
            </Link>
            <Link
              href="/help"
              className="p-4 bg-white dark:bg-neutral-800 rounded-lg hover:shadow-md transition-shadow text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
            >
              <div className="font-medium">Help</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Get support</div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
