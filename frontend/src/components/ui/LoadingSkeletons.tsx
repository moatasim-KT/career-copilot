/**
 * Loading Skeleton Components
 * 
 * Reusable skeleton loaders for lazy-loaded components
 * to improve perceived performance during code splitting.
 */

import React from 'react';

import { cn } from '@/lib/utils';

interface SkeletonProps {
    className?: string;
}

/**
 * Basic skeleton element
 */
export function Skeleton({ className }: SkeletonProps) {
    return (
        <div
            className={cn(
                'animate-pulse rounded-md bg-neutral-200 dark:bg-neutral-800',
                className,
            )}
        />
    );
}

/**
 * Kanban Board Loading Skeleton
 */
export function KanbanLoadingSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header skeleton */}
            <div className="flex items-center justify-between">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-10 w-32" />
            </div>

            {/* Kanban columns skeleton */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-4">
                {[1, 2, 3, 4].map((col) => (
                    <div key={col} className="space-y-3">
                        {/* Column header */}
                        <div className="flex items-center justify-between rounded-lg bg-neutral-100 dark:bg-neutral-900 p-3">
                            <Skeleton className="h-5 w-24" />
                            <Skeleton className="h-5 w-8" />
                        </div>

                        {/* Cards */}
                        <div className="space-y-2">
                            {[1, 2, 3].map((card) => (
                                <div
                                    key={card}
                                    className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4 space-y-3"
                                >
                                    <Skeleton className="h-5 w-3/4" />
                                    <Skeleton className="h-4 w-1/2" />
                                    <div className="flex gap-2">
                                        <Skeleton className="h-6 w-16" />
                                        <Skeleton className="h-6 w-20" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/**
 * Analytics Page Loading Skeleton
 */
export function AnalyticsLoadingSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <Skeleton className="h-10 w-64" />
                <Skeleton className="h-5 w-96" />
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[1, 2, 3, 4].map((stat) => (
                    <div
                        key={stat}
                        className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 space-y-2"
                    >
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-8 w-16" />
                        <Skeleton className="h-3 w-32" />
                    </div>
                ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {[1, 2].map((chart) => (
                    <div
                        key={chart}
                        className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 space-y-4"
                    >
                        <Skeleton className="h-6 w-48" />
                        <Skeleton className="h-64 w-full" />
                    </div>
                ))}
            </div>

            {/* Table */}
            <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 space-y-4">
                <Skeleton className="h-6 w-40" />
                <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map((row) => (
                        <div key={row} className="flex gap-4">
                            <Skeleton className="h-10 w-full" />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

/**
 * Table Loading Skeleton
 */
export function TableLoadingSkeleton() {
    return (
        <div className="space-y-4">
            {/* Table header */}
            <div className="flex gap-4 rounded-lg bg-neutral-100 dark:bg-neutral-900 p-4">
                {[1, 2, 3, 4, 5].map((col) => (
                    <Skeleton key={col} className="h-5 w-24" />
                ))}
            </div>

            {/* Table rows */}
            <div className="space-y-2">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((row) => (
                    <div
                        key={row}
                        className="flex gap-4 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4"
                    >
                        {[1, 2, 3, 4, 5].map((col) => (
                            <Skeleton key={col} className="h-5 w-24" />
                        ))}
                    </div>
                ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
                <Skeleton className="h-10 w-32" />
                <div className="flex gap-2">
                    <Skeleton className="h-10 w-10" />
                    <Skeleton className="h-10 w-10" />
                    <Skeleton className="h-10 w-10" />
                </div>
                <Skeleton className="h-10 w-32" />
            </div>
        </div>
    );
}

/**
 * Dashboard Widget Loading Skeleton
 */
export function DashboardWidgetSkeleton() {
    return (
        <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 space-y-4">
            <div className="flex items-center justify-between">
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-6 w-6" />
            </div>
            <Skeleton className="h-32 w-full" />
            <div className="flex justify-between">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-16" />
            </div>
        </div>
    );
}

/**
 * Form Loading Skeleton
 */
export function FormLoadingSkeleton() {
    return (
        <div className="space-y-6">
            {[1, 2, 3, 4].map((field) => (
                <div key={field} className="space-y-2">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-10 w-full" />
                </div>
            ))}
            <div className="flex gap-4">
                <Skeleton className="h-10 w-32" />
                <Skeleton className="h-10 w-32" />
            </div>
        </div>
    );
}

/**
 * Card Grid Loading Skeleton
 */
export function CardGridLoadingSkeleton({ count = 6 }: { count?: number }) {
    return (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: count }).map((_, index) => (
                <div
                    key={index}
                    className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 space-y-3"
                >
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-5/6" />
                    <div className="flex gap-2 pt-2">
                        <Skeleton className="h-8 w-20" />
                        <Skeleton className="h-8 w-24" />
                    </div>
                </div>
            ))}
        </div>
    );
}

/**
 * Page Header Loading Skeleton
 */
export function PageHeaderSkeleton() {
    return (
        <div className="space-y-4 pb-6 border-b border-neutral-200 dark:border-neutral-800">
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-5 w-96" />
            <div className="flex gap-3">
                <Skeleton className="h-10 w-32" />
                <Skeleton className="h-10 w-24" />
            </div>
        </div>
    );
}
