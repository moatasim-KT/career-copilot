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
import { logger } from '@/lib/logger';

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

const DEFAULT_PREFERENCES: UserPreferences = {
    industries: [],
    locations: [],
    salaryRange: { min: 0, max: 200000 },
    jobTypes: ['full-time'],
    experienceLevel: 'mid',
    skills: [],
    companySize: ['medium', 'large'],
};

function normalizePreferences(preferences?: Partial<UserPreferences> | null): UserPreferences {
    const merged = {
        ...DEFAULT_PREFERENCES,
        ...(preferences || {}),
    } as Partial<UserPreferences>;

    const industries = merged.industries ?? DEFAULT_PREFERENCES.industries;
    const locations = merged.locations ?? DEFAULT_PREFERENCES.locations;
    const salaryRange = merged.salaryRange ?? DEFAULT_PREFERENCES.salaryRange;
    const jobTypes = merged.jobTypes && merged.jobTypes.length > 0
        ? merged.jobTypes
        : DEFAULT_PREFERENCES.jobTypes;
    const skills = merged.skills ?? DEFAULT_PREFERENCES.skills;
    const companySize = merged.companySize ?? DEFAULT_PREFERENCES.companySize;

    return {
        industries: [...industries],
        locations: [...locations],
        salaryRange: {
            min: salaryRange.min ?? DEFAULT_PREFERENCES.salaryRange.min,
            max: salaryRange.max ?? DEFAULT_PREFERENCES.salaryRange.max,
        },
        jobTypes: [...jobTypes],
        experienceLevel: merged.experienceLevel ?? DEFAULT_PREFERENCES.experienceLevel,
        skills: [...skills],
        companySize: [...companySize],
    };
}

interface JobPreviewApiResponse {
    id: number;
    title: string;
    company: { name: string; logo?: string | null } | string;
    location?: string | null;
    salary?: {
        min?: number | null;
        max?: number | null;
        currency?: string | null;
    } | null;
    type?: string | null;
    tags?: string[];
    tech_stack?: string[];
    source?: string | null;
}

interface NormalizedJob {
    id: string;
    company: string;
    position: string;
    location?: string | null;
    salaryValue?: number;
    salaryRange?: {
        min?: number | null;
        max?: number | null;
        currency?: string | null;
    } | null;
    jobType?: UserPreferences['jobTypes'][number] | null;
    tags: string[];
    source?: string | null;
}

const JOB_TYPE_VALUES: UserPreferences['jobTypes'][number][] = ['full-time', 'part-time', 'contract', 'remote'];

function isJobTypeValue(value: string): value is UserPreferences['jobTypes'][number] {
    return JOB_TYPE_VALUES.includes(value as UserPreferences['jobTypes'][number]);
}

function normalizeJobPreview(job: JobPreviewApiResponse): NormalizedJob {
    const companyName = typeof job.company === 'string'
        ? job.company
        : job.company?.name ?? 'Unknown company';

    const salaryMin = job.salary?.min ?? null;
    const salaryMax = job.salary?.max ?? null;
    let salaryValue: number | undefined;
    if (typeof salaryMin === 'number' && typeof salaryMax === 'number') {
        salaryValue = Math.round((salaryMin + salaryMax) / 2);
    } else if (typeof salaryMax === 'number') {
        salaryValue = salaryMax;
    } else if (typeof salaryMin === 'number') {
        salaryValue = salaryMin;
    }

    const rawType = job.type?.toLowerCase() ?? null;
    const normalizedType = rawType && isJobTypeValue(rawType) ? rawType : null;

    const tags = job.tags ?? job.tech_stack ?? [];

    return {
        id: String(job.id),
        company: companyName,
        position: job.title || 'Untitled role',
        location: job.location,
        salaryValue,
        salaryRange: job.salary ?? null,
        jobType: normalizedType,
        tags,
        source: job.source ?? null,
    };
}

function evaluateSkillMatch(job: NormalizedJob, preferences: UserPreferences) {
    const jobSkills = job.tags || [];
    const preferenceSkills = preferences.skills.map(skill => skill.toLowerCase());

    const matchedSkills = jobSkills.filter(skill =>
        preferenceSkills.includes(skill.toLowerCase()),
    );
    const missingSkills = jobSkills.filter(skill =>
        !preferenceSkills.includes(skill.toLowerCase()),
    );

    const matchRatio = jobSkills.length > 0
        ? matchedSkills.length / jobSkills.length
        : 0;

    return { matchedSkills, missingSkills, matchRatio };
}

/**
 * Calculate job match score based on user preferences
 */
function calculateMatchScore(
    job: NormalizedJob,
    preferences: UserPreferences,
    behavior: UserBehavior,
    skillMatchRatio: number,
): number {
    let score = 0;
    const weights = {
        location: 0.25,
        salary: 0.25,
        skills: 0.35,
        jobType: 0.15,
    };

    // Location match (fallback to neutral score when missing)
    if (preferences.locations.length > 0) {
        if (job.location && preferences.locations.some(loc =>
            job.location?.toLowerCase().includes(loc.toLowerCase()),
        )) {
            score += weights.location * 100;
        } else if (!job.location) {
            score += weights.location * 50;
        }
    } else {
        score += weights.location * 50;
    }

    // Salary match
    if (typeof job.salaryValue === 'number') {
        if (job.salaryValue >= preferences.salaryRange.min &&
            job.salaryValue <= preferences.salaryRange.max) {
            score += weights.salary * 100;
        } else {
            const distance = Math.min(
                Math.abs(job.salaryValue - preferences.salaryRange.min),
                Math.abs(job.salaryValue - preferences.salaryRange.max),
            );
            const maxDistance = Math.max(preferences.salaryRange.max - preferences.salaryRange.min, 1);
            score += weights.salary * 100 * (1 - Math.min(distance / maxDistance, 1));
        }
    } else {
        score += weights.salary * 50;
    }

    // Skills match (use neutral score when skills are missing)
    if (job.tags.length > 0) {
        score += weights.skills * 100 * skillMatchRatio;
    } else {
        score += weights.skills * 50;
    }

    // Job type match
    if (job.jobType) {
        if (preferences.jobTypes.includes(job.jobType)) {
            score += weights.jobType * 100;
        } else {
            score += weights.jobType * 50;
        }
    } else {
        score += weights.jobType * 50;
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
    job: NormalizedJob,
    preferences: UserPreferences,
    score: number,
    matchedSkillsCount: number,
    totalSkills: number,
): string[] {
    const reasons: string[] = [];

    // Location match
    if (job.location && preferences.locations.some(loc =>
        job.location?.toLowerCase().includes(loc.toLowerCase()),
    )) {
        reasons.push(`Located in your preferred area: ${job.location}`);
    }

    // Salary match
    if (typeof job.salaryValue === 'number' &&
        job.salaryValue >= preferences.salaryRange.min &&
        job.salaryValue <= preferences.salaryRange.max) {
        reasons.push('Salary within your target range');
    }

    // Skills match
    if (totalSkills > 0 && matchedSkillsCount > 0) {
        reasons.push(`You match ${matchedSkillsCount} of ${totalSkills} highlighted skills`);
    }

    // Job type match
    if (job.jobType && preferences.jobTypes.includes(job.jobType)) {
        reasons.push(`Matches your preferred job type (${job.jobType.replace('-', ' ')})`);
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
                    setPreferences(normalizePreferences(response.data as Partial<UserPreferences>));
                } else {
                    setPreferences(normalizePreferences(null));
                }
            } catch (error) {
                logger.error('Failed to load preferences:', error);
                setPreferences(normalizePreferences(null));
            }
        }

        async function loadBehavior() {
            try {
                const response = await apiClient.personalization.getBehavior(parseInt(userId));
                if (response.data) {
                    setBehavior(response.data);
                }
            } catch (error) {
                logger.error('Failed to load behavior:', error);
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
                const jobs = (response.data || []) as JobPreviewApiResponse[];

                // Score and rank jobs
                // preferences is guarded by the outer early return, but avoid `!` by narrowing
                const prefs = preferences as UserPreferences;
                const scored = jobs.map((job) => {
                    const normalized = normalizeJobPreview(job);
                    const { matchedSkills, missingSkills, matchRatio } = evaluateSkillMatch(normalized, prefs);
                    const score = calculateMatchScore(normalized, prefs, behavior, matchRatio);
                    const reasons = generateMatchReasons(
                        normalized,
                        prefs,
                        score,
                        matchedSkills.length,
                        normalized.tags.length,
                    );

                    return {
                        id: normalized.id,
                        company: normalized.company,
                        position: normalized.position,
                        location: normalized.location || 'Remote',
                        salary: normalized.salaryValue,
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
                logger.error('Failed to generate recommendations:', error);
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
        const basePreferences = preferences ?? DEFAULT_PREFERENCES;
        const newPreferences = normalizePreferences({
            ...basePreferences,
            ...updates,
        });
        setPreferences(newPreferences);

        try {
            await apiClient.personalization.updatePreferences(parseInt(userId), newPreferences);
        } catch (error) {
            logger.error('Failed to update preferences:', error);
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
            logger.error('Failed to track behavior:', error);
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
