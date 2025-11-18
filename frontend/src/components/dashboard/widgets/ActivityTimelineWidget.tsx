/**
 * Activity Timeline Widget
 * 
 * Displays recent activity timeline
 */

'use client';

import { CheckCircle2, Clock, XCircle, Calendar } from 'lucide-react';
import { useEffect, useState } from 'react';

interface Activity {
    id: number;
    type: 'applied' | 'interview' | 'offer' | 'rejected';
    title: string;
    description: string;
    timestamp: string;
}

const ACTIVITY_ICONS = {
    applied: Clock,
    interview: Calendar,
    offer: CheckCircle2,
    rejected: XCircle,
};

const ACTIVITY_COLORS = {
    applied: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400',
    interview: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400',
    offer: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400',
    rejected: 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400',
};

export default function ActivityTimelineWidget() {
    const [activities, setActivities] = useState<Activity[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Fetch real data from API
        // Mock data for now
        setActivities([
            {
                id: 1,
                type: 'interview',
                title: 'Interview Scheduled',
                description: 'TechCorp - Senior Developer',
                timestamp: '2 hours ago',
            },
            {
                id: 2,
                type: 'applied',
                title: 'Application Submitted',
                description: 'StartupXYZ - Full Stack Engineer',
                timestamp: '5 hours ago',
            },
            {
                id: 3,
                type: 'offer',
                title: 'Offer Received',
                description: 'BigTech Inc - React Developer',
                timestamp: '1 day ago',
            },
        ]);
        setLoading(false);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-neutral-900 dark:border-neutral-100" />
            </div>
        );
    }

    return (
        <div className="space-y-0">
            {activities.map((activity, index) => {
                const Icon = ACTIVITY_ICONS[activity.type];
                const colorClass = ACTIVITY_COLORS[activity.type];

                return (
                    <div key={activity.id} className="flex gap-4 group">
                        <div className="relative flex flex-col items-center">
                            <div className={`p-2 rounded-full ring-4 ring-white dark:ring-neutral-900 z-10 ${colorClass}`}>
                                <Icon className="h-4 w-4" />
                            </div>
                            {index < activities.length - 1 && (
                                <div className="absolute top-8 bottom-[-8px] w-px bg-neutral-200 dark:bg-neutral-800" />
                            )}
                        </div>
                        <div className="flex-1 pb-6 pt-1">
                            <div className="flex justify-between items-start">
                                <p className="font-semibold text-sm text-neutral-900 dark:text-neutral-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                    {activity.title}
                                </p>
                                <span className="text-xs font-medium text-neutral-400 dark:text-neutral-500 whitespace-nowrap ml-2">
                                    {activity.timestamp}
                                </span>
                            </div>
                            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-0.5">
                                {activity.description}
                            </p>
                        </div>
                    </div>
                );
            })}

            {activities.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                    No recent activity
                </p>
            )}
        </div>
    );
}
