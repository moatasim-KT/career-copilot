/**
 * Recent Jobs Widget
 * 
 * Displays the latest 5 job listings
 */

'use client';

import { Building2, MapPin } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/Button';

interface Job {
    id: number;
    title: string;
    company: string;
    location: string;
    posted: string;
}

export default function RecentJobsWidget() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Fetch real data from API
        // Mock data for now
        setJobs([
            {
                id: 1,
                title: 'Senior Frontend Developer',
                company: 'TechCorp',
                location: 'Berlin, Germany',
                posted: '2 hours ago',
            },
            {
                id: 2,
                title: 'Full Stack Engineer',
                company: 'StartupXYZ',
                location: 'Amsterdam, Netherlands',
                posted: '5 hours ago',
            },
            {
                id: 3,
                title: 'React Developer',
                company: 'BigTech Inc',
                location: 'Munich, Germany',
                posted: '1 day ago',
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
        <div className="space-y-3">
            {jobs.map((job) => (
                <div
                    key={job.id}
                    className="p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                    <h4 className="font-medium text-sm mb-1">{job.title}</h4>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
                        <div className="flex items-center gap-1">
                            <Building2 className="h-3 w-3" />
                            <span>{job.company}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            <span>{job.location}</span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">{job.posted}</span>
                        <Button size="sm" variant="outline" className="h-7 text-xs">
                            View
                        </Button>
                    </div>
                </div>
            ))}

            {jobs.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                    No recent jobs
                </p>
            )}
        </div>
    );
}
