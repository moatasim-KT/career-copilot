/**
 * Personalization Engine
 * 
 * ML-based personalization system for job recommendations,
 * user preferences, and adaptive UI customization.
 * 
 * @module features/personalization/PersonalizationEngine
 */

import { useState, useEffect, useCallback } from 'react';

import apiClient from '@/lib/api/client';

export interface UserPreferences {
    industries: string[];
    locations: string[];
    salaryRange: { min: number; max: number };
    jobTypes: ('full-time' | 'part-time' | 'contract' | 'remote')[];
    experienceLevel: 'entry' | 'mid' | 'senior' | 'lead' | 'executive';
    skills: string[];
    companySize: ('startup' | 'small' | 'medium' | 'large' | 'enterprise')[];
}

export interface JobRecommendation {
    id: string;
    company: string;
    position: string;
    location: string;
    salary?: number;
    score: number; // 0-100
    reasons: string[];
    matchedSkills: string[];
    missingSkills: string[];
}

export interface UserBehavior {
    viewedJobs: string[];
    appliedJobs: string[];
    savedJobs: string[];
    rejectedJobs: string[];
    searchQueries: string[];
    clickPatterns: Record<string, number>;
}

/**
 * Calculate job match score based on user preferences
 */
function calculateMatchScore(
    job: any,
    preferences: UserPreferences,
    behavior: UserBehavior,
): number {
    let score = 0;
    const weights = {
        industry: 0.2,
        location: 0.15,
        salary: 0.2,
        skills: 0.25,
        jobType: 0.1,
        companySize: 0.1,
    };

    // Industry match
    if (preferences.industries.some(ind =>
        job.industry?.toLowerCase().includes(ind.toLowerCase()),
    )) {
        score += weights.industry * 100;
    }

    // Location match
    if (preferences.locations.some(loc =>
        job.location?.toLowerCase().includes(loc.toLowerCase()),
    )) {
        score += weights.location * 100;
    }

    // Salary match
    if (job.salary) {
        if (job.salary >= preferences.salaryRange.min &&
            job.salary <= preferences.salaryRange.max) {
            score += weights.salary * 100;
        } else {
            // Partial credit for close matches
            const distance = Math.min(
                Math.abs(job.salary - preferences.salaryRange.min),
                Math.abs(job.salary - preferences.salaryRange.max),
            );
            const maxDistance = preferences.salaryRange.max - preferences.salaryRange.min;
            score += weights.salary * 100 * (1 - Math.min(distance / maxDistance, 1));
        }
    }

    // Skills match
    const jobSkills = job.requiredSkills || [];
    const matchedSkills = jobSkills.filter((skill: string) =>
        preferences.skills.some(ps => ps.toLowerCase() === skill.toLowerCase()),
    );
    if (jobSkills.length > 0) {
        score += weights.skills * 100 * (matchedSkills.length / jobSkills.length);
    }

    // Job type match
    if (preferences.jobTypes.includes(job.type)) {
        score += weights.jobType * 100;
    }

    // Company size match
    if (preferences.companySize.includes(job.companySize)) {
        score += weights.companySize * 100;
    }

    // Behavioral boost
    if (behavior.viewedJobs.includes(job.id)) {
        score *= 1.05; // 5% boost for viewed jobs
    }
    if (behavior.savedJobs.includes(job.id)) {
        score *= 1.1; // 10% boost for saved jobs
    }
    if (behavior.rejectedJobs.includes(job.id)) {
        score *= 0.5; // 50% penalty for rejected jobs
    }

    return Math.min(Math.round(score), 100);
}

/**
 * Generate match reasons based on score components
 */
function generateMatchReasons(
    job: any,
    preferences: UserPreferences,
    score: number,
): string[] {
    const reasons: string[] = [];

    // Industry match
    if (preferences.industries.some(ind =>
        job.industry?.toLowerCase().includes(ind.toLowerCase()),
    )) {
        reasons.push(`Matches your interest in ${job.industry}`);
    }

    // Location match
    if (preferences.locations.some(loc =>
        job.location?.toLowerCase().includes(loc.toLowerCase()),
    )) {
        reasons.push(`Located in your preferred area: ${job.location}`);
    }

    // Salary match
    if (job.salary &&
        job.salary >= preferences.salaryRange.min &&
        job.salary <= preferences.salaryRange.max) {
        reasons.push('Salary within your target range');
    }

    // Skills match
    const jobSkills = job.requiredSkills || [];
    const matchedSkills = jobSkills.filter((skill: string) =>
        preferences.skills.some(ps => ps.toLowerCase() === skill.toLowerCase()),
    );
    if (matchedSkills.length > 0) {
        reasons.push(`You have ${matchedSkills.length} of ${jobSkills.length} required skills`);
    }

    // Experience level
    if (job.experienceLevel === preferences.experienceLevel) {
        reasons.push('Perfect match for your experience level');
    }

    if (score >= 80) {
        reasons.push('Highly recommended based on your profile');
    }

    return reasons;
}

/**
 * Personalization Engine Hook
 * 
 * @example
 * ```tsx
 * function JobRecommendations() {
 *   const { recommendations, updatePreferences, loading } = usePersonalization();
 *   
 *   return (
 *     <div>
 *       {recommendations.map(rec => (
 *         <JobCard key={rec.id} job={rec} score={rec.score} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function usePersonalization(userId: string) {
    const [preferences, setPreferences] = useState<UserPreferences | null>(null);
    const [behavior, setBehavior] = useState<UserBehavior>({
        viewedJobs: [],
        appliedJobs: [],
        savedJobs: [],
        rejectedJobs: [],
        searchQueries: [],
        clickPatterns: {},
    });
    const [recommendations, setRecommendations] = useState<JobRecommendation[]>([]);
    const [loading, setLoading] = useState(true);

    /**
     * Load user preferences
     */
    useEffect(() => {
        async function loadPreferences() {
            try {
                const response = await apiClient.personalization.getPreferences(parseInt(userId));
                if (response.data) {
                    setPreferences(response.data);
                } else {
                    // Use default preferences
                    setPreferences({
                        industries: [],
                        locations: [],
                        salaryRange: { min: 0, max: 200000 },
                        jobTypes: ['full-time'],
                        experienceLevel: 'mid',
                        skills: [],
                        companySize: ['medium', 'large'],
                    });
                }
            } catch (error) {
                console.error('Failed to load preferences:', error);
                // Use default preferences
                setPreferences({
                    industries: [],
                    locations: [],
                    salaryRange: { min: 0, max: 200000 },
                    jobTypes: ['full-time'],
                    experienceLevel: 'mid',
                    skills: [],
                    companySize: ['medium', 'large'],
                });
            }
        }

        async function loadBehavior() {
            try {
                const response = await apiClient.personalization.getBehavior(parseInt(userId));
                if (response.data) {
                    setBehavior(response.data);
                }
            } catch (error) {
                console.error('Failed to load behavior:', error);
            }
        }

        loadPreferences();
        loadBehavior();
    }, [userId]);    /**
     * Generate recommendations
     */
    useEffect(() => {
        if (!preferences) return;

        async function generateRecommendations() {
            setLoading(true);
            try {
                // Fetch available jobs
                const response = await apiClient.jobs.available({ limit: 100 });
                const jobs = response.data || [];

                // Score and rank jobs
                const scored = jobs.map((job: any) => {
                    const score = calculateMatchScore(job, preferences!, behavior);
                    const reasons = generateMatchReasons(job, preferences!, score);

                    const jobSkills = job.requiredSkills || [];
                    const matchedSkills = jobSkills.filter((skill: string) =>
                        preferences!.skills.some(ps => ps.toLowerCase() === skill.toLowerCase()),
                    );
                    const missingSkills = jobSkills.filter((skill: string) =>
                        !preferences!.skills.some(ps => ps.toLowerCase() === skill.toLowerCase()),
                    );

                    return {
                        id: job.id,
                        company: job.company,
                        position: job.position,
                        location: job.location,
                        salary: job.salary,
                        score,
                        reasons,
                        matchedSkills,
                        missingSkills,
                    };
                });

                // Sort by score and take top 20
                const topRecommendations = scored
                    .sort((a: JobRecommendation, b: JobRecommendation) => b.score - a.score)
                    .slice(0, 20);

                setRecommendations(topRecommendations);
            } catch (error) {
                console.error('Failed to generate recommendations:', error);
            } finally {
                setLoading(false);
            }
        }

        generateRecommendations();
    }, [preferences, behavior]);

    /**
     * Update user preferences
     */
    const updatePreferences = useCallback(async (
        updates: Partial<UserPreferences>,
    ) => {
        const newPreferences = { ...preferences, ...updates } as UserPreferences;
        setPreferences(newPreferences);

        try {
            await apiClient.personalization.updatePreferences(parseInt(userId), newPreferences);
        } catch (error) {
            console.error('Failed to update preferences:', error);
        }
    }, [preferences, userId]);

    /**
     * Track user behavior
     */
    const trackBehavior = useCallback(async (
        action: 'view' | 'apply' | 'save' | 'reject',
        jobId: string,
    ) => {
        const newBehavior = { ...behavior };

        switch (action) {
            case 'view':
                if (!newBehavior.viewedJobs.includes(jobId)) {
                    newBehavior.viewedJobs.push(jobId);
                }
                break;
            case 'apply':
                if (!newBehavior.appliedJobs.includes(jobId)) {
                    newBehavior.appliedJobs.push(jobId);
                }
                break;
            case 'save':
                if (!newBehavior.savedJobs.includes(jobId)) {
                    newBehavior.savedJobs.push(jobId);
                }
                break;
            case 'reject':
                if (!newBehavior.rejectedJobs.includes(jobId)) {
                    newBehavior.rejectedJobs.push(jobId);
                }
                break;
        }

        setBehavior(newBehavior);

        try {
            await apiClient.personalization.trackBehavior(parseInt(userId), action, jobId);
        } catch (error) {
            console.error('Failed to track behavior:', error);
        }
    }, [behavior, userId]);

    /**
     * Get learning insights
     */
    const getLearningInsights = useCallback(() => {
        const insights: string[] = [];

        // Analyze application patterns
        const avgScore = behavior.appliedJobs.length > 0
            ? recommendations
                .filter(r => behavior.appliedJobs.includes(r.id))
                .reduce((sum, r) => sum + r.score, 0) / behavior.appliedJobs.length
            : 0;

        if (avgScore > 0) {
            insights.push(`You typically apply to jobs with ${avgScore.toFixed(0)}% match score`);
        }

        // Most common skills in saved jobs
        const savedSkills = recommendations
            .filter(r => behavior.savedJobs.includes(r.id))
            .flatMap(r => r.matchedSkills);

        const skillCounts = savedSkills.reduce((acc, skill) => {
            acc[skill] = (acc[skill] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        const topSkills = Object.entries(skillCounts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 3)
            .map(([skill]) => skill);

        if (topSkills.length > 0) {
            insights.push(`You're most interested in jobs requiring: ${topSkills.join(', ')}`);
        }

        return insights;
    }, [behavior, recommendations]);

    return {
        preferences,
        recommendations,
        behavior,
        loading,
        updatePreferences,
        trackBehavior,
        getLearningInsights,
    };
}
