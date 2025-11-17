/**
 * Application Stats Widget
 * 
 * Displays key metrics about applications
 */

'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';
import { useEffect, useState } from 'react';

interface Stat {
    label: string;
    value: string;
    change: number;
    trend: 'up' | 'down';
}

export default function ApplicationStatsWidget() {
    const [stats, setStats] = useState<Stat[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Fetch real data from API
        // Mock data for now
        setStats([
            {
                label: 'Total Applications',
                value: '40',
                change: 12,
                trend: 'up',
            },
            {
                label: 'Response Rate',
                value: '35%',
                change: 5,
                trend: 'up',
            },
            {
                label: 'Avg. Response Time',
                value: '5.2 days',
                change: 8,
                trend: 'down',
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
            {stats.map((stat) => (
                <div key={stat.label} className="space-y-1">
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                        <div
                            className={`flex items-center gap-1 text-xs ${stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                                }`}
                        >
                            {stat.trend === 'up' ? (
                                <TrendingUp className="h-3 w-3" />
                            ) : (
                                <TrendingDown className="h-3 w-3" />
                            )}
                            <span>{stat.change}%</span>
                        </div>
                    </div>
                    <p className="text-2xl font-bold">{stat.value}</p>
                </div>
            ))}
        </div>
    );
}
