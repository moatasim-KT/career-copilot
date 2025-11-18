'use client';

import { AlertCircle, RefreshCw, Bug, Home, ArrowLeft } from 'lucide-react';
import React, { Component, ErrorInfo, ReactNode } from 'react';

import { classifyError, formatErrorForLogging, ErrorType } from '@/lib/errorHandling';
import { logger } from '@/lib/logger';

interface Props {
	children: ReactNode;
	fallback?: ReactNode;
	onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
	hasError: boolean;
	error: Error | null;
	errorInfo: ErrorInfo | null;
	errorType: ErrorType;
}

export class ErrorBoundary extends Component<Props, State> {
	constructor(props: Props) {
		super(props);
		this.state = {
			hasError: false,
			error: null,
			errorInfo: null,
			errorType: 'unknown',
		};
	}

	static getDerivedStateFromError(error: Error): Partial<State> {
		return {
			hasError: true,
			error,
			errorType: classifyError(error),
		};
	}

	componentDidCatch(error: Error, errorInfo: ErrorInfo) {
		// Log error to console in development
		if (process.env.NODE_ENV === 'development') {
			logger.error('ErrorBoundary caught:', error, errorInfo);
		}

		// Log error for monitoring (Sentry, etc.)
		this.logErrorToService(error, errorInfo);

		// Update state with error info
		this.setState({ errorInfo });

		// Call custom error handler if provided
		if (this.props.onError) {
			this.props.onError(error, errorInfo);
		}
	}

	logErrorToService(error: Error, errorInfo: ErrorInfo) {
		// In production, send to Sentry
		if (process.env.NODE_ENV === 'production') {
			const errorLog = formatErrorForLogging(error, {
				component: 'ErrorBoundary',
				metadata: {
					componentStack: errorInfo.componentStack,
				},
			});

			// Send to Sentry
			try {
				import('@/lib/sentry').then(({ captureException, setContext }) => {
					setContext('error_boundary', {
						componentStack: errorInfo.componentStack,
					});

					captureException(error, {
						tags: {
							errorType: classifyError(error),
							source: 'ErrorBoundary',
						},
						extra: {
							errorLog,
						},
						level: 'error',
					});
				});
			} catch (sentryError) {
				logger.error('[Sentry Error]', sentryError);
			}
		} else {
			// Log to console in development
			const errorLog = formatErrorForLogging(error, {
				component: 'ErrorBoundary',
				metadata: {
					componentStack: errorInfo.componentStack,
				},
			});
			logger.error('[Error Monitoring]', errorLog);
		}
	}

	handleRetry = () => {
		this.setState({
			hasError: false,
			error: null,
			errorInfo: null,
			errorType: 'unknown',
		});
	};

	handleReportIssue = () => {
		const { error, errorInfo } = this.state;

		// Create issue report data
		const issueData = {
			error: error?.message,
			stack: error?.stack,
			componentStack: errorInfo?.componentStack,
			userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
			url: typeof window !== 'undefined' ? window.location.href : 'SSR',
			timestamp: new Date().toISOString(),
		};

		// In production, this would send to backend or open issue tracker
		logger.info('Report issue:', issueData);

		// For now, copy to clipboard
		if (typeof navigator !== 'undefined' && navigator.clipboard) {
			navigator.clipboard.writeText(JSON.stringify(issueData, null, 2));
			alert('Error details copied to clipboard. Please share with support.');
		}
	};

	handleGoHome = () => {
		window.location.href = '/dashboard';
	};

	handleGoBack = () => {
		window.history.back();
	};

	getUserFriendlyMessage(): string {
		const { errorType, error } = this.state;

		switch (errorType) {
			case 'network':
				return 'We\'re having trouble connecting to the server. Please check your internet connection.';
			case 'auth':
				return 'There was an authentication issue. Please try logging in again.';
			case 'server':
				return 'Our servers are experiencing issues. We\'re working to fix this.';
			case 'client':
				return 'Something went wrong with your request. Please try again.';
			default:
				return error?.message || 'An unexpected error occurred. Please try again.';
		}
	}

	getErrorIcon() {
		const { errorType } = this.state;

		const iconClass = 'h-6 w-6';
		const containerClass = 'flex items-center justify-center w-12 h-12 mx-auto rounded-full';

		switch (errorType) {
			case 'network':
				return (
					<div className={`${containerClass} bg-orange-100 dark:bg-orange-900/30`}>
						<AlertCircle className={`${iconClass} text-orange-600 dark:text-orange-400`} />
					</div>
				);
			case 'auth':
				return (
					<div className={`${containerClass} bg-yellow-100 dark:bg-yellow-900/30`}>
						<AlertCircle className={`${iconClass} text-yellow-600 dark:text-yellow-400`} />
					</div>
				);
			case 'server':
				return (
					<div className={`${containerClass} bg-red-100 dark:bg-red-900/30`}>
						<AlertCircle className={`${iconClass} text-red-600 dark:text-red-400`} />
					</div>
				);
			default:
				return (
					<div className={`${containerClass} bg-red-100 dark:bg-red-900/30`}>
						<AlertCircle className={`${iconClass} text-red-600 dark:text-red-400`} />
					</div>
				);
		}
	}

	render() {
		if (this.state.hasError) {
			// Use custom fallback if provided
			if (this.props.fallback) {
				return this.props.fallback;
			}

			const userMessage = this.getUserFriendlyMessage();
			const showTechnicalDetails = process.env.NODE_ENV === 'development';

			return (
				<div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900 px-4 py-8">
					<div className="max-w-lg w-full bg-white dark:bg-neutral-800 rounded-lg shadow-lg p-8">
						{/* Error Icon */}
						{this.getErrorIcon()}

						{/* Error Title */}
						<h2 className="mt-4 text-xl md:text-3xl font-semibold text-center text-gray-900 dark:text-white">
							Oops! Something went wrong
						</h2>

						{/* User-friendly message */}
						<p className="mt-3 text-base text-center text-gray-600 dark:text-gray-300">
							{userMessage}
						</p>

						{/* Technical details (development only) */}
						{showTechnicalDetails && this.state.error && (
							<div className="mt-4 p-4 bg-gray-100 dark:bg-neutral-700 rounded-md">
								<p className="text-xs font-mono text-gray-700 dark:text-gray-300 break-all">
									{this.state.error.message}
								</p>
								{this.state.error.stack && (
									<details className="mt-2">
										<summary className="text-xs text-gray-600 dark:text-gray-400 cursor-pointer">
											Stack trace
										</summary>
										<pre className="mt-2 text-xs text-gray-600 dark:text-gray-400 overflow-auto max-h-40">
											{this.state.error.stack}
										</pre>
									</details>
								)}
							</div>
						)}

						{/* Action buttons */}
						<div className="mt-6 space-y-3">
							{/* Retry button */}
							<button
								onClick={this.handleRetry}
								className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2.5 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
							>
								<RefreshCw className="h-4 w-4" />
								Try Again
							</button>

							{/* Secondary actions */}
							<div className="grid grid-cols-2 gap-3">
								<button
									onClick={this.handleGoBack}
									className="flex items-center justify-center gap-2 bg-gray-100 dark:bg-neutral-700 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-md hover:bg-gray-200 dark:hover:bg-neutral-600 transition-colors text-sm font-medium"
								>
									<ArrowLeft className="h-4 w-4" />
									Go Back
								</button>

								<button
									onClick={this.handleGoHome}
									className="flex items-center justify-center gap-2 bg-gray-100 dark:bg-neutral-700 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-md hover:bg-gray-200 dark:hover:bg-neutral-600 transition-colors text-sm font-medium"
								>
									<Home className="h-4 w-4" />
									Home
								</button>
							</div>

							{/* Report issue button */}
							<button
								onClick={this.handleReportIssue}
								className="w-full flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 py-2 px-4 rounded-md hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors text-sm"
							>
								<Bug className="h-4 w-4" />
								Report Issue
							</button>
						</div>

						{/* Help text */}
						<p className="mt-6 text-xs text-center text-gray-500 dark:text-gray-400">
							If this problem persists, please contact support with the error details.
						</p>
					</div>
				</div>
			);
		}

		return this.props.children;
	}
}
