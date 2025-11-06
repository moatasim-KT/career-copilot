/**
 * Skeleton Loading Components
 * 
 * Enterprise-grade skeleton screens for optimal loading UX
 * Provides visual feedback while content is loading
 * 
 * @module components/common/Skeleton
 */

'use client';

import { clsx } from 'clsx';
import React from 'react';

export interface SkeletonProps {
    /** Width of the skeleton (CSS value) */
    width?: string | number;
    /** Height of the skeleton (CSS value) */
    height?: string | number;
    /** Border radius variant */
    variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
    /** Animation type */
    animation?: 'pulse' | 'wave' | 'none';
    /** Additional CSS classes */
    className?: string;
    /** Number of lines for text variant */
    lines?: number;
}

/**
 * Base Skeleton Component
 * 
 * @example
 * ```tsx
 * <Skeleton width="100%" height={40} variant="rectangular" />
 * ```
 */
export function Skeleton({
    width = '100%',
    height = 20,
    variant = 'text',
    animation = 'pulse',
    className = '',
}: SkeletonProps) {
    const widthValue = typeof width === 'number' ? `${width}px` : width;
    const heightValue = typeof height === 'number' ? `${height}px` : height;

    return (
        <div
            className={clsx(
                'bg-gray-200',
                {
                    'animate-pulse': animation === 'pulse',
                    'animate-shimmer': animation === 'wave',
                    'rounded-full': variant === 'circular',
                    'rounded-md': variant === 'rounded',
                    'rounded': variant === 'text',
                    'rounded-none': variant === 'rectangular',
                },
                className,
            )}
            style={{
                width: widthValue,
                height: heightValue,
                display: 'inline-block',
            }}
            aria-busy="true"
            aria-live="polite"
            role="status"
        />
    );
}

/**
 * Text Skeleton Component
 * 
 * @example
 * ```tsx
 * <SkeletonText lines={3} />
 * ```
 */
export function SkeletonText({ lines = 1, className = '' }: { lines?: number; className?: string }) {
    return (
        <div className={clsx('space-y-2', className)}>
            {Array.from({ length: lines }).map((_, index) => (
                <Skeleton
                    key={index}
                    width={index === lines - 1 ? '80%' : '100%'}
                    height={16}
                    variant="text"
                />
            ))}
        </div>
    );
}

/**
 * Card Skeleton Component
 * 
 * @example
 * ```tsx
 * <SkeletonCard />
 * ```
 */
export function SkeletonCard({ className = '' }: { className?: string }) {
    return (
        <div className={clsx('bg-white rounded-lg shadow p-6', className)}>
            <div className="flex items-start space-x-4">
                {/* Avatar */}
                <Skeleton variant="circular" width={48} height={48} />

                {/* Content */}
                <div className="flex-1">
                    {/* Title */}
                    <Skeleton width="60%" height={20} className="mb-2" />

                    {/* Description */}
                    <SkeletonText lines={2} />
                </div>
            </div>

            {/* Footer */}
            <div className="mt-4 flex items-center justify-between">
                <Skeleton width={100} height={32} variant="rounded" />
                <Skeleton width={80} height={32} variant="rounded" />
            </div>
        </div>
    );
}

/**
 * Table Skeleton Component
 * 
 * @example
 * ```tsx
 * <SkeletonTable rows={5} columns={4} />
 * ```
 */
export function SkeletonTable({
    rows = 5,
    columns = 3,
    className = '',
}: {
    rows?: number;
    columns?: number;
    className?: string;
}) {
    return (
        <div className={clsx('bg-white rounded-lg shadow overflow-hidden', className)}>
            {/* Header */}
            <div className="border-b border-gray-200 p-4">
                <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
                    {Array.from({ length: columns }).map((_, index) => (
                        <Skeleton key={index} height={20} />
                    ))}
                </div>
            </div>

            {/* Rows */}
            <div className="divide-y divide-gray-200">
                {Array.from({ length: rows }).map((_, rowIndex) => (
                    <div key={rowIndex} className="p-4">
                        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
                            {Array.from({ length: columns }).map((_, colIndex) => (
                                <Skeleton key={colIndex} height={16} />
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/**
 * List Skeleton Component
 * 
 * @example
 * ```tsx
 * <SkeletonList items={10} />
 * ```
 */
export function SkeletonList({ items = 5, className = '' }: { items?: number; className?: string }) {
    return (
        <div className={clsx('space-y-3', className)}>
            {Array.from({ length: items }).map((_, index) => (
                <div key={index} className="flex items-center space-x-3">
                    <Skeleton variant="circular" width={40} height={40} />
                    <div className="flex-1">
                        <Skeleton width="40%" height={16} className="mb-2" />
                        <Skeleton width="70%" height={12} />
                    </div>
                </div>
            ))}
        </div>
    );
}

/**
 * Dashboard Skeleton Component
 * 
 * @example
 * ```tsx
 * <SkeletonDashboard />
 * ```
 */
export function SkeletonDashboard({ className = '' }: { className?: string }) {
    return (
        <div className={clsx('space-y-6', className)}>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, index) => (
                    <div key={index} className="bg-white rounded-lg shadow p-6">
                        <Skeleton width="60%" height={16} className="mb-2" />
                        <Skeleton width="40%" height={32} className="mb-2" />
                        <Skeleton width="80%" height={12} />
                    </div>
                ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <Skeleton width="50%" height={24} className="mb-6" />
                    <Skeleton width="100%" height={300} variant="rounded" />
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <Skeleton width="50%" height={24} className="mb-6" />
                    <Skeleton width="100%" height={300} variant="rounded" />
                </div>
            </div>

            {/* Table */}
            <SkeletonTable rows={10} columns={5} />
        </div>
    );
}

/**
 * Application Card Skeleton
 * 
 * @example
 * ```tsx
 * <SkeletonApplicationCard />
 * ```
 */
export function SkeletonApplicationCard({ className = '' }: { className?: string }) {
    return (
        <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200 p-6', className)}>
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                    <Skeleton width="70%" height={24} className="mb-2" />
                    <Skeleton width="50%" height={16} />
                </div>
                <Skeleton variant="rounded" width={80} height={28} />
            </div>

            <div className="space-y-3 mb-4">
                <div className="flex items-center space-x-2">
                    <Skeleton variant="circular" width={16} height={16} />
                    <Skeleton width="40%" height={14} />
                </div>
                <div className="flex items-center space-x-2">
                    <Skeleton variant="circular" width={16} height={16} />
                    <Skeleton width="30%" height={14} />
                </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <Skeleton width={100} height={32} variant="rounded" />
                <Skeleton variant="circular" width={32} height={32} />
            </div>
        </div>
    );
}

// Add shimmer animation to tailwind
// Add this to your tailwind.config.ts:
// animation: {
//   shimmer: 'shimmer 2s infinite',
// },
// keyframes: {
//   shimmer: {
//     '0%': { backgroundPosition: '-1000px 0' },
//     '100%': { backgroundPosition: '1000px 0' },
//   },
// },
