import { LucideIcon } from 'lucide-react';
import React from 'react';

import { getRelativeTime } from '@/lib/utils';

export interface ActivityTimelineItemProps {
    /** Activity title */
    title: string;
    /** Activity description */
    description: string;
    /** Timestamp */
    timestamp: Date | string;
    /** Icon component */
    icon: LucideIcon;
    /** Icon color */
    iconColor?: string;
    /** Action label (optional) */
    actionLabel?: string;
    /** Action handler (optional) */
    onAction?: () => void;
}

/**
 * Timeline item for activity feed
 * 
 * @example
 * ```tsx
 * <ActivityTimelineItem
 *   title="Application Submitted"
 *   description="Software Engineer at Google"
 *   timestamp={new Date()}
 *   icon={FileText}
 *   iconColor="text-blue-600"
 * />
 * ```
 */
export default function ActivityTimelineItem({
    title,
    description,
    timestamp,
    icon: Icon,
    iconColor = 'text-blue-600',
    actionLabel,
    onAction,
}: ActivityTimelineItemProps) {
    return (
        <div className="flex items-start space-x-3 py-3">
            {/* Icon */}
            <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${iconColor.replace('text-', 'bg-').replace('-600', '-100')}`}>
                <Icon className={`h-4 w-4 ${iconColor}`} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{title}</p>
                        <p className="text-sm text-gray-600 mt-0.5">{description}</p>
                    </div>
                    {actionLabel && onAction && (
                        <button
                            onClick={onAction}
                            className="text-xs text-blue-600 hover:text-blue-700 font-medium ml-2"
                        >
                            {actionLabel}
                        </button>
                    )}
                </div>
                <p className="text-xs text-gray-500 mt-1">{getRelativeTime(timestamp)}</p>
            </div>
        </div>
    );
}
