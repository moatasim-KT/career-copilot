/**
 * Smart Recommendations Component
 * 
 * Displays ML-generated job recommendations with confidence scores
 * and explanations for why each job matches the user's profile.
 * 
 * @module components/recommendations/SmartRecommendations
 */

'use client';

import {
    ThumbsUp,
    ThumbsDown,
    Bookmark,
    ExternalLink,
    Info,
    TrendingUp,
    MapPin,
    DollarSign,
    Briefcase,
} from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/Badge';
import Button2 from '@/components/ui/Button2';
import Card2, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card2';
import { usePersonalization } from '@/features/personalization/PersonalizationEngine';
import apiClient from '@/lib/api/client';
import { logger } from '@/lib/logger';


interface SmartRecommendationsProps {
    userId: string;
    limit?: number;
    showFilters?: boolean;
}

/**
 * Confidence indicator component
 */
function ConfidenceIndicator({ score }: { score: number }) {
    const getColor = () => {
        if (score >= 80) return 'bg-green-500';
        if (score >= 60) return 'bg-yellow-500';
        return 'bg-orange-500';
    };

    const getLabel = () => {
        if (score >= 80) return 'Excellent match';
        if (score >= 60) return 'Good match';
        return 'Potential match';
    };

    return (
        <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                <div
                    className={`h-full ${getColor()} transition-all duration-500`}
                    style={{ width: `${score}%` }}
                />
            </div>
            <span className="text-sm font-medium">{score}%</span>
            <Badge variant={score >= 80 ? 'success' : score >= 60 ? 'warning' : 'default'}>
                {getLabel()}
            </Badge>
        </div>
    );
}

/**
 * Recommendation card component
 */
function RecommendationCard({
    recommendation,
    onSave,
    onApply,
    onFeedback,
}: {
    recommendation: any;
    onSave: () => void;
    onApply: () => void;
    onFeedback: (isPositive: boolean) => void;
}) {
    const [showDetails, setShowDetails] = useState(false);

    return (
        <Card2 className="hover:shadow-lg transition-shadow duration-200">
            <CardHeader>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <CardTitle className="text-xl mb-1">
                            {recommendation.position}
                        </CardTitle>
                        <p className="text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
                            <Briefcase className="w-4 h-4" />
                            {recommendation.company}
                        </p>
                    </div>
                    <ConfidenceIndicator score={recommendation.score} />
                </div>
            </CardHeader>

            <CardContent className="space-y-4">
                {/* Location & Salary */}
                <div className="flex gap-4 text-sm text-neutral-600 dark:text-neutral-400">
                    <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {recommendation.location}
                    </span>
                    {recommendation.salary && (
                        <span className="flex items-center gap-1">
                            <DollarSign className="w-4 h-4" />
                            ${recommendation.salary.toLocaleString()}
                        </span>
                    )}
                </div>

                {/* Match Reasons */}
                <div className="space-y-2">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-blue-500" />
                        <span className="font-medium text-sm">Why this recommendation?</span>
                    </div>
                    <ul className="space-y-1 ml-6">
                        {recommendation.reasons.slice(0, showDetails ? undefined : 2).map((reason: string, idx: number) => (
                            <li key={idx} className="text-sm text-neutral-600 dark:text-neutral-400 list-disc">
                                {reason}
                            </li>
                        ))}
                    </ul>
                    {recommendation.reasons.length > 2 && (
                        <button
                            onClick={() => setShowDetails(!showDetails)}
                            className="text-blue-500 p-0 h-auto text-sm hover:underline"
                        >
                            {showDetails ? 'Show less' : `Show ${recommendation.reasons.length - 2} more reasons`}
                        </button>
                    )}
                </div>

                {/* Skills Match */}
                <div className="space-y-2">
                    <p className="text-sm font-medium">Skills Match</p>
                    <div className="flex flex-wrap gap-2">
                        {recommendation.matchedSkills.map((skill: string) => (
                            <Badge key={skill} variant="success">
                                ✓ {skill}
                            </Badge>
                        ))}
                        {showDetails && recommendation.missingSkills.slice(0, 3).map((skill: string) => (
                            <Badge key={skill} variant="default">
                                {skill}
                            </Badge>
                        ))}
                    </div>
                    {!showDetails && recommendation.missingSkills.length > 0 && (
                        <p className="text-xs text-neutral-500">
                            {recommendation.missingSkills.length} skills to learn
                        </p>
                    )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <Button2
                        onClick={onApply}
                        className="flex-1"
                    >
                        Apply Now
                    </Button2>
                    <Button2
                        variant="outline"
                        onClick={onSave}
                    >
                        <Bookmark className="w-4 h-4" />
                    </Button2>
                    <Button2
                        variant="outline"
                        onClick={() => window.open(`/jobs/${recommendation.id}`, '_blank')}
                    >
                        <ExternalLink className="w-4 h-4" />
                    </Button2>
                </div>

                {/* Feedback */}
                <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                    <span>Was this helpful?</span>
                    <Button2
                        variant="ghost"
                        size="sm"
                        onClick={() => onFeedback(true)}
                        className="hover:text-green-500"
                    >
                        <ThumbsUp className="w-4 h-4" />
                    </Button2>
                    <Button2
                        variant="ghost"
                        size="sm"
                        onClick={() => onFeedback(false)}
                        className="hover:text-red-500"
                    >
                        <ThumbsDown className="w-4 h-4" />
                    </Button2>
                </div>
            </CardContent>
        </Card2>
    );
}

/**
 * Smart Recommendations Component
 * 
 * @example
 * ```tsx
 * <SmartRecommendations 
 *   userId="user-123" 
 *   limit={10}
 *   showFilters={true}
 * />
 * ```
 */
export function SmartRecommendations({
    userId,
    limit = 10,
    showFilters = true,
}: SmartRecommendationsProps) {
    const {
        recommendations,
        loading,
        trackBehavior,
        getLearningInsights,
    } = usePersonalization(userId);

    const [filter, setFilter] = useState<'all' | 'excellent' | 'good'>('all');
    const [showInsights, setShowInsights] = useState(false);

    const filteredRecommendations = recommendations
        .filter(rec => {
            if (filter === 'excellent') return rec.score >= 80;
            if (filter === 'good') return rec.score >= 60 && rec.score < 80;
            return true;
        })
        .slice(0, limit);

    const insights = getLearningInsights();

    const handleSave = (jobId: string) => {
        trackBehavior('save', jobId);
    };

    const handleApply = (jobId: string) => {
        trackBehavior('apply', jobId);
        // Redirect to application page
        window.location.href = `/jobs/${jobId}/apply`;
    };

    const handleFeedback = async (jobId: string, isPositive: boolean) => {
        if (!isPositive) {
            trackBehavior('reject', jobId);
        }
        // Track feedback for ML improvement
        try {
            await apiClient.recommendations.feedback(Number(jobId), isPositive);
        } catch (error) {
            logger.error('Failed to submit feedback:', error);
        }
    };

    if (loading) {
        return (
            <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                    <Card2 key={i} className="animate-pulse">
                        <CardHeader>
                            <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-2/3" />
                            <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-1/3 mt-2" />
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded" />
                                <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4" />
                            </div>
                        </CardContent>
                    </Card2>
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">Smart Recommendations</h2>
                    <p className="text-neutral-600 dark:text-neutral-400 mt-1">
                        {filteredRecommendations.length} jobs matched to your profile
                    </p>
                </div>
                <Button2
                    variant="outline"
                    size="sm"
                    onClick={() => setShowInsights(!showInsights)}
                >
                    <Info className="w-4 h-4 mr-2" />
                    {showInsights ? 'Hide' : 'Show'} Insights
                </Button2>
            </div>

            {/* Learning Insights */}
            {showInsights && insights.length > 0 && (
                <Card2 className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
                    <CardHeader>
                        <CardTitle className="text-blue-900 dark:text-blue-100 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5" />
                            Your Learning Insights
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2">
                            {insights.map((insight, idx) => (
                                <li key={idx} className="text-sm text-blue-800 dark:text-blue-200 flex items-start gap-2">
                                    <span className="text-blue-500">•</span>
                                    {insight}
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card2>
            )}

            {/* Filters */}
            {showFilters && (
                <div className="flex gap-2">
                    <Button2
                        variant={filter === 'all' ? 'primary' : 'outline'}
                        onClick={() => setFilter('all')}
                        size="sm"
                    >
                        All Matches
                    </Button2>
                    <Button2
                        variant={filter === 'excellent' ? 'primary' : 'outline'}
                        onClick={() => setFilter('excellent')}
                        size="sm"
                    >
                        Excellent (80%+)
                    </Button2>
                    <Button2
                        variant={filter === 'good' ? 'primary' : 'outline'}
                        onClick={() => setFilter('good')}
                        size="sm"
                    >
                        Good (60-80%)
                    </Button2>
                </div>
            )}

            {/* Recommendations */}
            {filteredRecommendations.length === 0 ? (
                <Card2>
                    <CardContent className="py-12 text-center">
                        <p className="text-neutral-600 dark:text-neutral-400">
                            No recommendations found. Try adjusting your preferences.
                        </p>
                    </CardContent>
                </Card2>
            ) : (
                <div className="space-y-4">
                    {filteredRecommendations.map(rec => (
                        <RecommendationCard
                            key={rec.id}
                            recommendation={rec}
                            onSave={() => handleSave(rec.id)}
                            onApply={() => handleApply(rec.id)}
                            onFeedback={(isPositive) => handleFeedback(rec.id, isPositive)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
