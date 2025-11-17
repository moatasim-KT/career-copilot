/**
 * Skills Progress Widget
 * 
 * Displays progress bars for skills development
 */

'use client';

import { useEffect, useState } from 'react';

import { Progress } from '@/components/ui/progress';

interface Skill {
    name: string;
    level: number;
    target: number;
}

export default function SkillsProgressWidget() {
    const [skills, setSkills] = useState<Skill[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Fetch real data from API
        // Mock data for now
        setSkills([
            { name: 'React', level: 85, target: 90 },
            { name: 'TypeScript', level: 75, target: 85 },
            { name: 'Node.js', level: 70, target: 80 },
            { name: 'AWS', level: 60, target: 75 },
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
            {skills.map((skill) => {
                const percentage = (skill.level / skill.target) * 100;

                return (
                    <div key={skill.name} className="space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{skill.name}</span>
                            <span className="text-xs text-muted-foreground">
                                {skill.level}% / {skill.target}%
                            </span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                    </div>
                );
            })}

            {skills.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                    No skills tracked
                </p>
            )}
        </div>
    );
}
