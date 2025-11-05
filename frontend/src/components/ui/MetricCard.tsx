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
                return 'text-green-600 bg-green-50';
            case 'down':
                return 'text-red-600 bg-red-50';
            default:
                return 'text-gray-600 bg-gray-50';
        }
    };

    if (loading) {
        return (
            <div className="bg-white p-6 rounded-lg shadow-sm border animate-pulse">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
                        <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
                        <div className="h-4 bg-gray-200 rounded w-32"></div>
                    </div>
                    <div className="h-10 w-10 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    return (
        <div
            className={cn(
                'bg-white p-6 rounded-lg shadow-sm border transition-all duration-200',
                onClick && 'cursor-pointer hover:shadow-md hover:border-blue-300',
            )}
            onClick={onClick}
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
            onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
                    <p className="text-3xl font-bold text-gray-900 mb-2">{value}</p>

                    {description && (
                        <p className="text-xs text-gray-500 mb-2">{description}</p>
                    )}

                    {trend && trendValue !== undefined && (
                        <div className={cn(
                            'inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium',
                            getTrendColor(),
                        )}>
                            {getTrendIcon()}
                            <span>{trendValue}%</span>
                            <span className="text-gray-500">{trendLabel}</span>
                        </div>
                    )}
                </div>

                <div className={cn(
                    'h-12 w-12 rounded-lg flex items-center justify-center',
                    iconColor.replace('text-', 'bg-').replace('-600', '-100'),
                )}>
                    <Icon className={cn('h-6 w-6', iconColor)} />
                </div>
            </div>
        </div>
    );
}
