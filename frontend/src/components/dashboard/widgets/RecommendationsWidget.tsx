/**
 * Recommendations Widget
 * 
 * Displays AI-powered job recommendations
 */

'use client';

import { Sparkles, ExternalLink } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface Recommendation {
    id: number;
    title: string;
    company: string;
    matchScore: number;
    reasons: string[];
}

export default function RecommendationsWidget() {
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Fetch real data from API
        // Mock data for now
        setRecommendations([
            {
                id: 1,
                title: 'Senior React Developer',
                company: 'TechCorp',
                matchScore: 95,
                reasons: ['Skills match', 'Location preference', 'Salary range'],
            },
            {
                id: 2,
                title: 'Full Stack Engineer',
                company: 'StartupXYZ',
                matchScore: 88,
                reasons: ['Experience level', 'Tech stack'],
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
            {recommendations.map((rec) => (
                <div
                    key={rec.id}
                    className="p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                    <div className="flex items-start justify-between mb-2">
                        <div>
                            <h4 className="font-medium text-sm">{rec.title}</h4>
                            <p className="text-xs text-muted-foreground">{rec.company}</p>
                        </div>
                        <Badge variant="secondary" className="ml-2">
                            {rec.matchScore}%
                        </Badge>
                    </div>

                    <div className="flex flex-wrap gap-1 mb-2">
                        {rec.reasons.map((reason, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                                {reason}
                            </Badge>
                        ))}
                    </div>

                    <Button size="sm" variant="ghost" className="h-7 w-full text-xs">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View Details
                    </Button>
                </div>
            ))}

            {recommendations.length === 0 && (
                <div className="text-center py-6">
                    <Sparkles className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-20" />
                    <p className="text-sm text-muted-foreground">No recommendations yet</p>
                </div>
            )}
        </div>
    );
}
