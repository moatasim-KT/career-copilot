/**
 * Goals Tracker Widget
 * 
 * Displays career goals with completion percentage
 */

'use client';

import { Target, CheckCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Progress } from '@/components/ui/progress';

interface Goal {
    id: number;
    title: string;
    progress: number;
    deadline: string;
}

export default function GoalsTrackerWidget() {
    const [goals, setGoals] = useState<Goal[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Fetch real data from API
        // Mock data for now
        setGoals([
            {
                id: 1,
                title: 'Apply to 50 positions',
                progress: 80,
                deadline: 'End of month',
            },
            {
                id: 2,
                title: 'Complete 3 interviews',
                progress: 66,
                deadline: 'This week',
            },
            {
                id: 3,
                title: 'Learn new framework',
                progress: 45,
                deadline: 'This quarter',
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
            {goals.map((goal) => (
                <div key={goal.id} className="space-y-2">
                    <div className="flex items-start justify-between">
                        <div className="flex items-start gap-2">
                            {goal.progress === 100 ? (
                                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
                            ) : (
                                <Target className="h-4 w-4 text-muted-foreground mt-0.5" />
                            )}
                            <div>
                                <p className="text-sm font-medium">{goal.title}</p>
                                <p className="text-xs text-muted-foreground">{goal.deadline}</p>
                            </div>
                        </div>
                        <span className="text-xs font-medium">{goal.progress}%</span>
                    </div>
                    <Progress value={goal.progress} className="h-2" />
                </div>
            ))}

            {goals.length === 0 && (
                <div className="text-center py-6">
                    <Target className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-20" />
                    <p className="text-sm text-muted-foreground">No goals set</p>
                </div>
            )}
        </div>
    );
}
