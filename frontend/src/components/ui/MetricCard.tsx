import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react';
import React from 'react';

import { cn } from '@/lib/utils';

export interface MetricCardProps {
    /** Card title */
    title: string;
    /** Primary metric value */
    value: string | number;
    /** Icon component */
    icon: LucideIcon;
    /** Icon color class */
    iconColor?: string;
    /** Trend direction */
    trend?: 'up' | 'down' | 'neutral';
    /** Trend percentage */
    trendValue?: number;
    /** Trend label */
    trendLabel?: string;
    /** Click handler */
    onClick?: () => void;
    /** Additional description */
    description?: string;
    /** Loading state */
    loading?: boolean;
}

/**
 * Enhanced metric card with trend indicators
 * 
 * @example
 * ```tsx
 * <MetricCard
 *   title="Total Applications"
 *   value={45}
 *   icon={Briefcase}
 *   iconColor="text-blue-600"
 *   trend="up"
 *   trendValue={12}
 *   trendLabel="vs last month"
 * />
 * ```
 */
export default function MetricCard({
    title,
    value,
    icon: Icon,
    iconColor = 'text-blue-600',
    trend,
    trendValue,
    trendLabel = 'vs last period',
    onClick,
    description,
    loading = false,
}: MetricCardProps) {
    const getTrendIcon = () => {
        switch (trend) {
            case 'up':
                return <TrendingUp className="h-4 w-4" />;
            case 'down':
                return <TrendingDown className="h-4 w-4" />;
            default:
                return <Minus className="h-4 w-4" />;
        }
    };

    const getTrendColor = () => {
        switch (trend) {
            case 'up':
                return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
            case 'down':
                return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
            default:
                return 'text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-800';
        }
    };

    if (loading) {
        return (
            <div className="bg-white dark:bg-neutral-900 p-6 rounded-xl shadow-sm border border-neutral-200 dark:border-neutral-800 animate-pulse">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded w-24 mb-3"></div>
                        <div className="h-8 bg-neutral-200 dark:bg-neutral-800 rounded w-16 mb-2"></div>
                        <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded w-32"></div>
                    </div>
                    <div className="h-12 w-12 bg-neutral-200 dark:bg-neutral-800 rounded-xl"></div>
                </div>
            </div>
        );
    }

    return (
        <div
            className={cn(
                'bg-white/60 dark:bg-neutral-900/60 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-white/20 dark:border-neutral-800 transition-all duration-300 group',
                onClick && 'cursor-pointer hover:shadow-lg hover:shadow-indigo-500/10 hover:border-primary-500/30 dark:hover:border-primary-500/30 hover:-translate-y-0.5',
            )}
            onClick={onClick}
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
            onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400 mb-1">{title}</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mb-2 tracking-tight">{value}</p>

                    {description && (
                        <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-2">{description}</p>
                    )}

                    {trend && trendValue !== undefined && (
                        <div className="flex items-center gap-2">
                            <div className={cn(
                                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                                getTrendColor(),
                            )}>
                                {getTrendIcon()}
                                <span>{trendValue}%</span>
                            </div>
                            <span className="text-xs text-neutral-500 dark:text-neutral-400">{trendLabel}</span>
                        </div>
                    )}
                </div>

                <div className={cn(
                    'h-12 w-12 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:rotate-3',
                    // Use a safer way to generate background colors or default to neutral
                    'bg-linear-to-br from-neutral-100 to-neutral-50 dark:from-neutral-800 dark:to-neutral-900 shadow-inner',
                )}>
                    <Icon className={cn('h-6 w-6', iconColor)} />
                </div>
            </div>
        </div>
    );
}
