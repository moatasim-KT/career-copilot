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
    iconColor = 'text-primary-600',
    onClick,
    disabled = false,
}: QuickActionCardProps) {
    // Extract color name to create background class dynamically if needed, 
    // but for now let's use a neutral background for better consistency

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                'w-full text-left group relative overflow-hidden',
                'bg-white dark:bg-neutral-800/50',
                'p-4 rounded-xl border border-neutral-200 dark:border-neutral-800',
                'transition-all duration-200 ease-in-out',
                !disabled && 'hover:border-primary-500/50 hover:shadow-md hover:-translate-y-0.5',
                disabled && 'opacity-50 cursor-not-allowed',
            )}
        >
            <div className="flex items-center gap-4">
                <div className={cn(
                    'h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors',
                    'bg-neutral-100 dark:bg-neutral-800 group-hover:bg-primary-50 dark:group-hover:bg-primary-900/20',
                )}>
                    <Icon className={cn('h-5 w-5 transition-colors', iconColor)} />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-0.5 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                        {title}
                    </h3>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 line-clamp-2">
                        {description}
                    </p>
                </div>
            </div>
        </button>
    );
}
