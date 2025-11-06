/**
 * Quick Filter Chips Component
 * Common filter shortcuts for quick job searches
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import React from 'react';

// ============================================================================
// Types
// ============================================================================

export interface QuickFilter {
    id: string;
    label: string;
    icon?: React.ReactNode;
    filters: Record<string, any>;
    color?: 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'gray';
}

export interface QuickFilterChipsProps {
    filters: QuickFilter[];
    activeFilters: Record<string, any>;
    onFilterClick: (filter: QuickFilter) => void;
    onRemoveFilter: (filterId: string) => void;
    className?: string;
}

// ============================================================================
// Quick Filter Chips Component
// ============================================================================

export function QuickFilterChips({
    filters,
    activeFilters,
    onFilterClick,
    onRemoveFilter,
    className = '',
}: QuickFilterChipsProps) {
    const isFilterActive = (filter: QuickFilter): boolean => {
        return Object.entries(filter.filters).every(
            ([key, value]) => {
                const activeValue = activeFilters[key];
                if (Array.isArray(value) && Array.isArray(activeValue)) {
                    return value.every(v => activeValue.includes(v));
                }
                return JSON.stringify(activeValue) === JSON.stringify(value);
            },
        );
    };

    const activeChipIds = filters
        .filter(isFilterActive)
        .map(f => f.id);

    return (
        <div className={`flex flex-wrap items-center gap-2 ${className}`}>
            {/* Quick Filter Chips */}
            {filters.map((filter) => {
                const isActive = activeChipIds.includes(filter.id);

                return (
                    <FilterChip
                        key={filter.id}
                        filter={filter}
                        isActive={isActive}
                        onClick={() => onFilterClick(filter)}
                        onRemove={() => onRemoveFilter(filter.id)}
                    />
                );
            })}
        </div>
    );
}

// ============================================================================
// Filter Chip Component
// ============================================================================

interface FilterChipProps {
    filter: QuickFilter;
    isActive: boolean;
    onClick: () => void;
    onRemove: () => void;
}

function FilterChip({ filter, isActive, onClick, onRemove }: FilterChipProps) {
    const colorClasses = {
        blue: {
            inactive: 'bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200',
            active: 'bg-blue-600 text-white border-blue-600',
        },
        green: {
            inactive: 'bg-green-50 text-green-700 hover:bg-green-100 border-green-200',
            active: 'bg-green-600 text-white border-green-600',
        },
        purple: {
            inactive: 'bg-purple-50 text-purple-700 hover:bg-purple-100 border-purple-200',
            active: 'bg-purple-600 text-white border-purple-600',
        },
        orange: {
            inactive: 'bg-orange-50 text-orange-700 hover:bg-orange-100 border-orange-200',
            active: 'bg-orange-600 text-white border-orange-600',
        },
        red: {
            inactive: 'bg-red-50 text-red-700 hover:bg-red-100 border-red-200',
            active: 'bg-red-600 text-white border-red-600',
        },
        gray: {
            inactive: 'bg-gray-50 text-gray-700 hover:bg-gray-100 border-gray-200',
            active: 'bg-gray-600 text-white border-gray-600',
        },
    };

    const color = filter.color || 'blue';
    const classes = isActive ? colorClasses[color].active : colorClasses[color].inactive;

    return (
        <motion.button
            layout
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={onClick}
            className={`
        inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border
        text-sm font-medium transition-all duration-200
        ${classes}
        ${isActive ? 'shadow-sm' : ''}
      `}
        >
            {filter.icon && <span className="flex-shrink-0">{filter.icon}</span>}
            <span>{filter.label}</span>

            {isActive && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove();
                    }}
                    className="ml-1 flex-shrink-0 hover:bg-white/20 rounded-full p-0.5 transition-colors"
                    aria-label={`Remove ${filter.label} filter`}
                >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            )}
        </motion.button>
    );
}

// ============================================================================
// Preset Quick Filters
// ============================================================================

export const jobQuickFilters: QuickFilter[] = [
    {
        id: 'remote',
        label: 'Remote Only',
        filters: { remote: true },
        color: 'blue',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    },
    {
        id: 'full-time',
        label: 'Full-time',
        filters: { job_type: 'Full-time' },
        color: 'green',
    },
    {
        id: 'entry-level',
        label: 'Entry Level',
        filters: { experience_level: 'Entry' },
        color: 'purple',
    },
    {
        id: 'senior',
        label: 'Senior',
        filters: { experience_level: 'Senior' },
        color: 'orange',
    },
    {
        id: 'high-match',
        label: 'High Match (>80%)',
        filters: { match_score_min: 80 },
        color: 'green',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
        ),
    },
    {
        id: 'recent',
        label: 'Posted This Week',
        filters: { posted_within_days: 7 },
        color: 'blue',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    },
    {
        id: 'tech-stack',
        label: 'My Tech Stack',
        filters: { match_tech_stack: true },
        color: 'purple',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
        ),
    },
    {
        id: 'saved',
        label: 'Saved Jobs',
        filters: { is_saved: true },
        color: 'red',
        icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
        ),
    },
];

// ============================================================================
// Active Filter Display
// ============================================================================

export interface ActiveFilterTagsProps {
    activeFilters: Record<string, any>;
    filterLabels: Record<string, string>;
    onRemove: (key: string) => void;
    onClearAll: () => void;
    className?: string;
}

export function ActiveFilterTags({
    activeFilters,
    filterLabels,
    onRemove,
    onClearAll,
    className = '',
}: ActiveFilterTagsProps) {
    const activeKeys = Object.keys(activeFilters).filter(
        key => activeFilters[key] !== null &&
            activeFilters[key] !== undefined &&
            activeFilters[key] !== '' &&
            !(Array.isArray(activeFilters[key]) && activeFilters[key].length === 0),
    );

    if (activeKeys.length === 0) return null;

    const formatValue = (value: any): string => {
        if (Array.isArray(value)) {
            return value.join(', ');
        }
        if (typeof value === 'boolean') {
            return value ? 'Yes' : 'No';
        }
        if (typeof value === 'object') {
            return Object.values(value).filter(Boolean).join(' - ');
        }
        return String(value);
    };

    return (
        <div className={`flex flex-wrap items-center gap-2 ${className}`}>
            <span className="text-sm font-medium text-gray-700">Active filters:</span>

            <AnimatePresence>
                {activeKeys.map((key) => (
                    <motion.div
                        key={key}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="inline-flex items-center gap-1.5 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                    >
                        <span className="font-medium">{filterLabels[key] || key}:</span>
                        <span>{formatValue(activeFilters[key])}</span>
                        <button
                            onClick={() => onRemove(key)}
                            className="ml-1 hover:bg-gray-200 rounded-full p-0.5 transition-colors"
                            aria-label={`Remove ${filterLabels[key] || key} filter`}
                        >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </motion.div>
                ))}
            </AnimatePresence>

            {activeKeys.length > 1 && (
                <button
                    onClick={onClearAll}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                >
                    Clear all
                </button>
            )}
        </div>
    );
}
