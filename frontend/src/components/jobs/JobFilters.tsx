/**
 * Phase 3.3: Job Filters Component
 * Filters for new job board fields (equity, tech stack, experience level, etc.)
 */

import { Filter, X } from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';

export interface JobFilters {
    experienceLevel?: string[];
    techStack?: string[];
    fundingStage?: string[];
    hasEquity?: boolean;
    hasSalary?: boolean;
    remote?: boolean;
    jobLanguage?: string[];
    source?: string[];
}

interface JobFiltersComponentProps {
    filters: JobFilters;
    onFiltersChange: (filters: JobFilters) => void;
    availableTechStack?: string[];
}

const EXPERIENCE_LEVELS = [
    'Internship',
    'Entry Level',
    'Junior',
    'Mid-Level',
    'Senior',
    'Lead',
    'Staff',
    'Principal',
    'Manager',
];

const FUNDING_STAGES = [
    'Bootstrapped',
    'Pre-Seed',
    'Seed',
    'Series A',
    'Series B',
    'Series C',
    'Series D+',
    'Public',
];

const LANGUAGES = [
    { code: 'en', name: 'English' },
    { code: 'de', name: 'German' },
    { code: 'fr', name: 'French' },
    { code: 'it', name: 'Italian' },
    { code: 'es', name: 'Spanish' },
];

const JOB_SOURCES = ['AngelList', 'XING', 'Welcome to the Jungle', 'LinkedIn', 'Indeed'];

export default function JobFiltersComponent({ filters, onFiltersChange, availableTechStack = [] }: JobFiltersComponentProps) {
    const toggleExperienceLevel = (level: string) => {
        const current = filters.experienceLevel || [];
        const updated = current.includes(level)
            ? current.filter(l => l !== level)
            : [...current, level];
        onFiltersChange({ ...filters, experienceLevel: updated.length ? updated : undefined });
    };

    const toggleTechStack = (tech: string) => {
        const current = filters.techStack || [];
        const updated = current.includes(tech)
            ? current.filter(t => t !== tech)
            : [...current, tech];
        onFiltersChange({ ...filters, techStack: updated.length ? updated : undefined });
    };

    const toggleFundingStage = (stage: string) => {
        const current = filters.fundingStage || [];
        const updated = current.includes(stage)
            ? current.filter(s => s !== stage)
            : [...current, stage];
        onFiltersChange({ ...filters, fundingStage: updated.length ? updated : undefined });
    };

    const toggleLanguage = (lang: string) => {
        const current = filters.jobLanguage || [];
        const updated = current.includes(lang)
            ? current.filter(l => l !== lang)
            : [...current, lang];
        onFiltersChange({ ...filters, jobLanguage: updated.length ? updated : undefined });
    };

    const toggleSource = (source: string) => {
        const current = filters.source || [];
        const updated = current.includes(source)
            ? current.filter(s => s !== source)
            : [...current, source];
        onFiltersChange({ ...filters, source: updated.length ? updated : undefined });
    };

    const clearFilters = () => {
        onFiltersChange({});
    };

    const activeFiltersCount =
        (filters.experienceLevel?.length || 0) +
        (filters.techStack?.length || 0) +
        (filters.fundingStage?.length || 0) +
        (filters.jobLanguage?.length || 0) +
        (filters.source?.length || 0) +
        (filters.hasEquity ? 1 : 0) +
        (filters.hasSalary ? 1 : 0) +
        (filters.remote ? 1 : 0);

    return (
        <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-gray-600" />
                    <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                    {activeFiltersCount > 0 && (
                        <Badge variant="secondary">{activeFiltersCount}</Badge>
                    )}
                </div>
                {activeFiltersCount > 0 && (
                    <button
                        onClick={clearFilters}
                        className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
                    >
                        <X className="w-4 h-4" />
                        Clear All
                    </button>
                )}
            </div>

            {/* Quick Filters */}
            <div className="space-y-4">
                <div>
                    <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={filters.hasEquity || false}
                            onChange={(e) => onFiltersChange({ ...filters, hasEquity: e.target.checked || undefined })}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        Has Equity
                    </label>
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={filters.hasSalary || false}
                            onChange={(e) => onFiltersChange({ ...filters, hasSalary: e.target.checked || undefined })}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        Salary Disclosed
                    </label>
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={filters.remote || false}
                            onChange={(e) => onFiltersChange({ ...filters, remote: e.target.checked || undefined })}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        Remote Only
                    </label>
                </div>
            </div>

            {/* Experience Level */}
            <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Experience Level</h4>
                <div className="flex flex-wrap gap-2">
                    {EXPERIENCE_LEVELS.map((level) => (
                        <Badge
                            key={level}
                            variant={filters.experienceLevel?.includes(level) ? 'default' : 'outline'}
                            className="cursor-pointer"
                            onClick={() => toggleExperienceLevel(level)}
                        >
                            {level}
                        </Badge>
                    ))}
                </div>
            </div>

            {/* Funding Stage */}
            <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Funding Stage</h4>
                <div className="flex flex-wrap gap-2">
                    {FUNDING_STAGES.map((stage) => (
                        <Badge
                            key={stage}
                            variant={filters.fundingStage?.includes(stage) ? 'default' : 'outline'}
                            className="cursor-pointer"
                            onClick={() => toggleFundingStage(stage)}
                        >
                            {stage}
                        </Badge>
                    ))}
                </div>
            </div>

            {/* Tech Stack */}
            {availableTechStack.length > 0 && (
                <div className="mt-6">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Tech Stack</h4>
                    <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                        {availableTechStack.slice(0, 20).map((tech) => (
                            <Badge
                                key={tech}
                                variant={filters.techStack?.includes(tech) ? 'default' : 'outline'}
                                className="cursor-pointer"
                                onClick={() => toggleTechStack(tech)}
                            >
                                {tech}
                            </Badge>
                        ))}
                    </div>
                </div>
            )}

            {/* Language */}
            <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Job Language</h4>
                <div className="flex flex-wrap gap-2">
                    {LANGUAGES.map((lang) => (
                        <Badge
                            key={lang.code}
                            variant={filters.jobLanguage?.includes(lang.code) ? 'default' : 'outline'}
                            className="cursor-pointer"
                            onClick={() => toggleLanguage(lang.code)}
                        >
                            {lang.name}
                        </Badge>
                    ))}
                </div>
            </div>

            {/* Source */}
            <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Job Board</h4>
                <div className="flex flex-wrap gap-2">
                    {JOB_SOURCES.map((source) => (
                        <Badge
                            key={source}
                            variant={filters.source?.includes(source) ? 'default' : 'outline'}
                            className="cursor-pointer"
                            onClick={() => toggleSource(source)}
                        >
                            {source}
                        </Badge>
                    ))}
                </div>
            </div>
        </div>
    );
}
