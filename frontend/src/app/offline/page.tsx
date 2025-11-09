/**
 * Offline Page
 * 
 * Displayed when the user is offline and tries to access a page
 * that isn't cached by the service worker
 */

import { WifiOff, RefreshCw } from 'lucide-react';
import React from 'react';

export const metadata = {
    title: 'You are offline - Career Copilot',
    description: 'This page requires an internet connection',
};

export default function OfflinePage() {
    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
            <div className="max-w-md w-full text-center">
                {/* Icon */}
                <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                    <WifiOff className="w-12 h-12 text-gray-400" />
                </div>

                {/* Title */}
                <h1 className="text-3xl font-bold text-gray-900 mb-4">
                    You&apos;re Offline
                </h1>

                {/* Description */}
                <p className="text-gray-600 mb-8">
                    It looks like you&apos;ve lost your internet connection. Please check your
                    network settings and try again.
                </p>

                {/* Actions */}
                <div className="space-y-4">
                    <button
                        onClick={() => window.location.reload()}
                        className="
              w-full flex items-center justify-center space-x-2
              px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white
              rounded-lg font-medium transition-colors
            "
                    >
                        <RefreshCw className="w-5 h-5" />
                        <span>Try Again</span>
                    </button>

                    <button
                        onClick={() => window.history.back()}
                        className="
              w-full px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700
              rounded-lg font-medium transition-colors
            "
                    >
                        Go Back
                    </button>
                </div>

                {/* Tips */}
                <div className="mt-12 text-left bg-white rounded-lg p-6 shadow-sm">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        While you&apos;re offline:
                    </h2>
                    <ul className="space-y-2 text-sm text-gray-600">
                        <li className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>Check your Wi-Fi or mobile data connection</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>Try turning airplane mode off</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>Visit recently viewed pages that may be cached</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>Your changes will sync when you&apos;re back online</span>
                        </li>
                    </ul>
                </div>

                {/* Cached Pages */}
                <div className="mt-6">
                    <p className="text-sm text-gray-500 mb-3">Quick links (may work offline):</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                        <a
                            href="/dashboard"
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                        >
                            Dashboard
                        </a>
                        <a
                            href="/applications"
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                        >
                            Applications
                        </a>
                        <a
                            href="/jobs"
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                        >
                            Jobs
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
