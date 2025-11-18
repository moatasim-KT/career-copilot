/**
 * Status Overview Widget
 * 
 * Displays a pie chart of application statuses
 */

'use client';

import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/Badge';

interface StatusData {
    status: string;
    count: number;
    color: string;
}

export default function StatusOverviewWidget() {
    const [statusData, setStatusData] = useState<StatusData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Fetch real data from API
        // Mock data for now
        setStatusData([
            { status: 'Applied', count: 15, color: '#3b82f6' },
            { status: 'In Progress', count: 8, color: '#f59e0b' },
            { status: 'Interview', count: 5, color: '#8b5cf6' },
            { status: 'Offer', count: 2, color: '#10b981' },
            { status: 'Rejected', count: 10, color: '#ef4444' },
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

    const total = statusData.reduce((sum, item) => sum + item.count, 0);

    return (
        <div className="space-y-4">
            <div className="text-center mb-4">
                <p className="text-3xl font-bold">{total}</p>
                <p className="text-sm text-muted-foreground">Total Applications</p>
            </div>

            <div className="space-y-2">
                {statusData.map((item) => (
                    <div key={item.status} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: item.color }}
                            />
                            <span className="text-sm">{item.status}</span>
                        </div>
                        <Badge variant="secondary">{item.count}</Badge>
                    </div>
                ))}
            </div>
        </div>
    );
}
