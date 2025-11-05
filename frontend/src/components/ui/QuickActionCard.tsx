import { LucideIcon } from 'lucide-react';
import React from 'react';

import { cn } from '@/lib/utils';

export interface QuickActionCardProps {
    /** Action title */
    title: string;
    /** Action description */
    description: string;
    /** Icon component */
    icon: LucideIcon;
    /** Icon color class */
    iconColor?: string;
    /** Click handler */
    onClick: () => void;
    /** Disabled state */
    disabled?: boolean;
}

/**
 * Quick action card for dashboard
 * 
 * @example
 * ```tsx
 * <QuickActionCard
 *   title="Add New Job"
 *   description="Track a new opportunity"
 *   icon={Plus}
 *   onClick={handleAddJob}
 * />
 * ```
 */
export default function QuickActionCard({
    title,
    description,
    icon: Icon,
    iconColor = 'text-blue-600',
    onClick,
    disabled = false,
}: QuickActionCardProps) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                'w-full text-left bg-white p-4 rounded-lg border transition-all duration-200',
                !disabled && 'hover:shadow-md hover:border-blue-300 cursor-pointer',
                disabled && 'opacity-50 cursor-not-allowed',
            )}
        >
            <div className="flex items-start space-x-3">
                <div className={cn(
                    'h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0',
                    iconColor.replace('text-', 'bg-').replace('-600', '-100'),
                )}>
                    <Icon className={cn('h-5 w-5', iconColor)} />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-900 mb-0.5">{title}</h3>
                    <p className="text-xs text-gray-600 line-clamp-2">{description}</p>
                </div>
            </div>
        </button>
    );
}
