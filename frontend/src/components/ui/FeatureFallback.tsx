/**
 * Feature Fallback Components
 * 
 * Provides graceful degradation for non-critical features.
 * Shows fallback UI when features fail to load or encounter errors.
 * 
 * @module components/ui/FeatureFallback
 */

'use client';

import { AlertCircle, RefreshCw, X } from 'lucide-react';
import { ReactNode, useState } from 'react';

interface FeatureFallbackProps {
  error?: Error | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  title?: string;
  description?: string;
  showRetry?: boolean;
  showDismiss?: boolean;
  variant?: 'inline' | 'card' | 'minimal';
  children?: ReactNode;
}

/**
 * Generic feature fallback component
 */
export function FeatureFallback({
  error,
  onRetry,
  onDismiss,
  title = 'Feature Unavailable',
  description = 'This feature is temporarily unavailable. Please try again later.',
  showRetry = true,
  showDismiss = true,
  variant = 'card',
  children,
}: FeatureFallbackProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    if (onRetry) {
      setIsRetrying(true);
      try {
        await onRetry();
      } finally {
        setIsRetrying(false);
      }
    }
  };

  // Minimal variant - just hide the feature
  if (variant === 'minimal') {
    return null;
  }

  // Inline variant - small inline message
  if (variant === 'inline') {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 py-2">
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        <span>{description}</span>
        {showRetry && onRetry && (
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="text-blue-600 dark:text-blue-400 hover:underline disabled:opacity-50"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  // Card variant - full card with icon and actions
  return (
    <div className="relative bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-6">
      {/* Dismiss button */}
      {showDismiss && onDismiss && (
        <button
          onClick={onDismiss}
          className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      )}

      {/* Icon */}
      <div className="flex items-center justify-center w-10 h-10 mx-auto bg-orange-100 dark:bg-orange-900/30 rounded-full">
        <AlertCircle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
      </div>

      {/* Content */}
      <div className="mt-4 text-center">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">{title}</h3>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">{description}</p>

        {/* Error details in development */}
        {process.env.NODE_ENV === 'development' && error && (
          <details className="mt-3 text-left">
            <summary className="text-xs text-gray-500 dark:text-gray-400 cursor-pointer">
              Error details
            </summary>
            <pre className="mt-2 text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-neutral-700 p-2 rounded overflow-auto max-h-32">
              {error.message}
            </pre>
          </details>
        )}

        {/* Custom children */}
        {children && <div className="mt-4">{children}</div>}

        {/* Retry button */}
        {showRetry && onRetry && (
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            <RefreshCw className={`h-4 w-4 ${isRetrying ? 'animate-spin' : ''}`} />
            {isRetrying ? 'Retrying...' : 'Try Again'}
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Chart fallback - for when charts fail to load
 */
export function ChartFallback({ onRetry }: { onRetry?: () => void }) {
  return (
    <FeatureFallback
      title="Chart Unavailable"
      description="Unable to load chart data. This won't affect other features."
      onRetry={onRetry}
      showDismiss={false}
    />
  );
}

/**
 * Widget fallback - for dashboard widgets
 */
export function WidgetFallback({ onRetry, onDismiss }: { onRetry?: () => void; onDismiss?: () => void }) {
  return (
    <FeatureFallback
      title="Widget Error"
      description="This widget couldn't load. You can dismiss it or try again."
      onRetry={onRetry}
      onDismiss={onDismiss}
      variant="card"
    />
  );
}

/**
 * Notification fallback - for notification system
 */
export function NotificationFallback() {
  return (
    <FeatureFallback
      title="Notifications Unavailable"
      description="Real-time notifications are temporarily unavailable. You can still use the app normally."
      showRetry={false}
      showDismiss={true}
      variant="inline"
    />
  );
}

/**
 * Search fallback - for search features
 */
export function SearchFallback({ onRetry }: { onRetry?: () => void }) {
  return (
    <FeatureFallback
      title="Search Unavailable"
      description="Search is temporarily unavailable. Please try browsing instead."
      onRetry={onRetry}
      showDismiss={false}
      variant="inline"
    />
  );
}

/**
 * Analytics fallback - for analytics features
 */
export function AnalyticsFallback({ onRetry }: { onRetry?: () => void }) {
  return (
    <FeatureFallback
      title="Analytics Unavailable"
      description="Unable to load analytics data. Your other features are working normally."
      onRetry={onRetry}
      showDismiss={true}
    />
  );
}
