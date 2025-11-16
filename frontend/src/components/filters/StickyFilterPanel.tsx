/**
 * Sticky Filter Panel Component
 * A persistent filter panel that stays visible while scrolling
 */

'use client';

import React, { useState, useEffect } from 'react';

import { m, AnimatePresence } from '@/lib/motion';

// ============================================================================
// Types
// ============================================================================

export interface FilterOption {
    id: string;
    label: string;
    value: string | number | boolean;
    count?: number;
}

export interface FilterGroup {
    id: string;
    label: string;
    type: 'checkbox' | 'radio' | 'range' | 'search';
    options?: FilterOption[];
    min?: number;
    max?: number;
    value?: any;
}

export interface StickyFilterPanelProps {
    filterGroups: FilterGroup[];
    activeFilters: Record<string, any>;
    onFilterChange: (filterId: string, value: any) => void;
    onClearAll: () => void;
    onApply?: () => void;
    className?: string;
    isSticky?: boolean;
    offsetTop?: number;
}

// ============================================================================
// Sticky Filter Panel Component
// ============================================================================

export function StickyFilterPanel({
    filterGroups,
    activeFilters,
    onFilterChange,
    onClearAll,
    onApply,
    className = '',
    isSticky = true,
    offsetTop = 0,
}: StickyFilterPanelProps) {
    const [isExpanded, setIsExpanded] = useState(true);
    const [isFixed, setIsFixed] = useState(false);

    useEffect(() => {
        if (!isSticky) return;

        const handleScroll = () => {
            setIsFixed(window.scrollY > offsetTop);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [isSticky, offsetTop]);

    const activeFilterCount = Object.keys(activeFilters).filter(
        key => activeFilters[key] !== null && activeFilters[key] !== undefined && activeFilters[key] !== '',
    ).length;

    return (
        <div
            className={`
        ${isFixed && isSticky ? 'fixed top-0 left-0 right-0 z-40 shadow-lg' : 'relative'}
        bg-white border-b border-gray-200 transition-all duration-200
        ${className}
      `}
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                        {activeFilterCount > 0 && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {activeFilterCount} active
                            </span>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        {activeFilterCount > 0 && (
                            <button
                                onClick={onClearAll}
                                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                            >
                                Clear all
                            </button>
                        )}

                        <button
                            onClick={() => setIsExpanded(!isExpanded)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            aria-label={isExpanded ? 'Collapse filters' : 'Expand filters'}
                        >
                            <svg
                                className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Filter Groups */}
                <AnimatePresence>
                    {isExpanded && (
                        <m.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                {filterGroups.map((group) => (
                                    <FilterGroupComponent
                                        key={group.id}
                                        group={group}
                                        value={activeFilters[group.id]}
                                        onChange={(value) => onFilterChange(group.id, value)}
                                    />
                                ))}
                            </div>

                            {/* Apply Button (optional) */}
                            {onApply && (
                                <div className="mt-4 flex justify-end">
                                    <button
                                        onClick={onApply}
                                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                        Apply Filters
                                    </button>
                                </div>
                            )}
                        </m.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

// ============================================================================
// Filter Group Component
// ============================================================================

interface FilterGroupComponentProps {
    group: FilterGroup;
    value: any;
    onChange: (value: any) => void;
}

function FilterGroupComponent({ group, value, onChange }: FilterGroupComponentProps) {
    switch (group.type) {
        case 'checkbox':
            return <CheckboxFilter group={group} value={value} onChange={onChange} />;
        case 'radio':
            return <RadioFilter group={group} value={value} onChange={onChange} />;
        case 'range':
            return <RangeFilter group={group} value={value} onChange={onChange} />;
        case 'search':
            return <SearchFilter group={group} value={value} onChange={onChange} />;
        default:
            return null;
    }
}

// ============================================================================
// Checkbox Filter
// ============================================================================

function CheckboxFilter({ group, value = [], onChange }: FilterGroupComponentProps) {
    const handleToggle = (optionValue: string | number | boolean) => {
        const currentValues = Array.isArray(value) ? value : [];
        const newValues = currentValues.includes(optionValue)
            ? currentValues.filter(v => v !== optionValue)
            : [...currentValues, optionValue];
        onChange(newValues);
    };

    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
                {group.label}
            </label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
                {group.options?.map((option) => (
                    <label key={option.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={Array.isArray(value) && value.includes(option.value)}
                            onChange={() => handleToggle(option.value)}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{option.label}</span>
                        {option.count !== undefined && (
                            <span className="text-xs text-gray-500">({option.count})</span>
                        )}
                    </label>
                ))}
            </div>
        </div>
    );
}

// ============================================================================
// Radio Filter
// ============================================================================

function RadioFilter({ group, value, onChange }: FilterGroupComponentProps) {
    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
                {group.label}
            </label>
            <div className="space-y-2">
                {group.options?.map((option) => (
                    <label key={option.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            checked={value === option.value}
                            onChange={() => onChange(option.value)}
                            className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{option.label}</span>
                        {option.count !== undefined && (
                            <span className="text-xs text-gray-500">({option.count})</span>
                        )}
                    </label>
                ))}
            </div>
        </div>
    );
}

// ============================================================================
// Range Filter
// ============================================================================

function RangeFilter({ group, value = { min: group.min, max: group.max }, onChange }: FilterGroupComponentProps) {
    const [localValue, setLocalValue] = useState(value);

    const handleChange = (field: 'min' | 'max', newValue: number) => {
        const updated = { ...localValue, [field]: newValue };
        setLocalValue(updated);
        onChange(updated);
    };

    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
                {group.label}
            </label>
            <div className="flex items-center gap-2">
                <input
                    type="number"
                    value={localValue.min ?? group.min}
                    onChange={(e) => handleChange('min', Number(e.target.value))}
                    min={group.min}
                    max={group.max}
                    placeholder="Min"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <span className="text-gray-500">-</span>
                <input
                    type="number"
                    value={localValue.max ?? group.max}
                    onChange={(e) => handleChange('max', Number(e.target.value))}
                    min={group.min}
                    max={group.max}
                    placeholder="Max"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
            </div>
        </div>
    );
}

// ============================================================================
// Search Filter
// ============================================================================

function SearchFilter({ group, value = '', onChange }: FilterGroupComponentProps) {
    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
                {group.label}
            </label>
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={`Search ${group.label.toLowerCase()}...`}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
        </div>
    );
}
