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
    applied: 'text-blue-600',
    interview: 'text-purple-600',
    offer: 'text-green-600',
    rejected: 'text-red-600',
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
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {activities.map((activity, index) => {
                const Icon = ACTIVITY_ICONS[activity.type];
                const colorClass = ACTIVITY_COLORS[activity.type];

                return (
                    <div key={activity.id} className="flex gap-3">
                        <div className="relative">
                            <div className={`p-2 rounded-full bg-accent ${colorClass}`}>
                                <Icon className="h-3 w-3" />
                            </div>
                            {index < activities.length - 1 && (
                                <div className="absolute top-8 left-1/2 -translate-x-1/2 w-0.5 h-8 bg-border" />
                            )}
                        </div>
                        <div className="flex-1 pb-4">
                            <p className="font-medium text-sm">{activity.title}</p>
                            <p className="text-xs text-muted-foreground">{activity.description}</p>
                            <p className="text-xs text-muted-foreground mt-1">{activity.timestamp}</p>
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
