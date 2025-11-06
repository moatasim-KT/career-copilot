/**
 * Tag Input Component
 * For entering skills, keywords, and other tag-based data
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import React, { useState, useRef, KeyboardEvent, ChangeEvent } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface Tag {
    id: string;
    label: string;
    value: string;
}

interface TagInputProps {
    tags: Tag[];
    onChange: (tags: Tag[]) => void;
    placeholder?: string;
    maxTags?: number;
    allowDuplicates?: boolean;
    suggestions?: string[];
    className?: string;
    disabled?: boolean;
    validate?: (value: string) => boolean | string;
    onInvalidTag?: (error: string) => void;
}

// ============================================================================
// Tag Input Component
// ============================================================================

export function TagInput({
    tags,
    onChange,
    placeholder = 'Add a tag...',
    maxTags,
    allowDuplicates = false,
    suggestions = [],
    className = '',
    disabled = false,
    validate,
    onInvalidTag,
}: TagInputProps) {
    const [inputValue, setInputValue] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Filter suggestions based on input
    const filteredSuggestions = suggestions.filter(
        (suggestion) =>
            suggestion.toLowerCase().includes(inputValue.toLowerCase()) &&
            (allowDuplicates || !tags.some((tag) => tag.value === suggestion)),
    );

    // Add a tag
    const addTag = (value: string) => {
        const trimmedValue = value.trim();

        if (!trimmedValue) return;

        // Validate
        if (validate) {
            const validationResult = validate(trimmedValue);
            if (validationResult !== true) {
                const errorMsg = typeof validationResult === 'string' ? validationResult : 'Invalid tag';
                setError(errorMsg);
                onInvalidTag?.(errorMsg);
                return;
            }
        }

        // Check for duplicates
        if (!allowDuplicates && tags.some((tag) => tag.value === trimmedValue)) {
            setError('Tag already exists');
            return;
        }

        // Check max tags
        if (maxTags && tags.length >= maxTags) {
            setError(`Maximum ${maxTags} tags allowed`);
            return;
        }

        // Add tag
        const newTag: Tag = {
            id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            label: trimmedValue,
            value: trimmedValue,
        };

        onChange([...tags, newTag]);
        setInputValue('');
        setError(null);
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
    };

    // Remove a tag
    const removeTag = (tagId: string) => {
        onChange(tags.filter((tag) => tag.id !== tagId));
    };

    // Handle input change
    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setInputValue(value);
        setShowSuggestions(value.length > 0 && filteredSuggestions.length > 0);
        setSelectedSuggestionIndex(-1);
        setError(null);
    };

    // Handle key down
    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();

            if (selectedSuggestionIndex >= 0 && selectedSuggestionIndex < filteredSuggestions.length) {
                addTag(filteredSuggestions[selectedSuggestionIndex]);
            } else {
                addTag(inputValue);
            }
        } else if (e.key === 'Backspace' && inputValue === '' && tags.length > 0) {
            // Remove last tag on backspace if input is empty
            removeTag(tags[tags.length - 1].id);
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedSuggestionIndex((prev) =>
                prev < filteredSuggestions.length - 1 ? prev + 1 : prev,
            );
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedSuggestionIndex((prev) => (prev > 0 ? prev - 1 : -1));
        } else if (e.key === 'Escape') {
            setShowSuggestions(false);
            setSelectedSuggestionIndex(-1);
        }
    };

    // Handle suggestion click
    const handleSuggestionClick = (suggestion: string) => {
        addTag(suggestion);
    };

    return (
        <div className={`tag-input ${className}`}>
            {/* Tags Container */}
            <div
                className={`
          flex flex-wrap gap-2 p-3 min-h-[48px] border rounded-lg bg-white
          ${disabled ? 'opacity-50 cursor-not-allowed bg-gray-50' : 'cursor-text'}
          ${error ? 'border-red-300' : 'border-gray-300 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500'}
        `}
                onClick={() => !disabled && inputRef.current?.focus()}
            >
                {/* Tags */}
                <AnimatePresence>
                    {tags.map((tag) => (
                        <motion.div
                            key={tag.id}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                        >
                            <span>{tag.label}</span>
                            {!disabled && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        removeTag(tag.id);
                                    }}
                                    className="ml-1 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                                >
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            )}
                        </motion.div>
                    ))}
                </AnimatePresence>

                {/* Input */}
                <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setShowSuggestions(inputValue.length > 0 && filteredSuggestions.length > 0)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                    placeholder={tags.length === 0 ? placeholder : ''}
                    disabled={disabled}
                    className="flex-1 min-w-[120px] outline-none bg-transparent"
                />
            </div>

            {/* Error Message */}
            {error && (
                <div className="mt-2 text-sm text-red-600">
                    {error}
                </div>
            )}

            {/* Max Tags Counter */}
            {maxTags && (
                <div className="mt-2 text-xs text-gray-500 text-right">
                    {tags.length} / {maxTags} tags
                </div>
            )}

            {/* Suggestions Dropdown */}
            {showSuggestions && filteredSuggestions.length > 0 && (
                <div className="relative">
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
                        {filteredSuggestions.map((suggestion, index) => (
                            <button
                                key={suggestion}
                                onClick={() => handleSuggestionClick(suggestion)}
                                className={`
                  w-full text-left px-4 py-2 text-sm hover:bg-blue-50 transition-colors
                  ${index === selectedSuggestionIndex ? 'bg-blue-100' : ''}
                `}
                            >
                                {suggestion}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Preset Tag Suggestions
// ============================================================================

export const skillSuggestions = [
    'JavaScript',
    'TypeScript',
    'React',
    'Node.js',
    'Python',
    'Java',
    'C++',
    'Go',
    'Rust',
    'SQL',
    'MongoDB',
    'PostgreSQL',
    'Redis',
    'Docker',
    'Kubernetes',
    'AWS',
    'Azure',
    'GCP',
    'CI/CD',
    'Git',
    'Agile',
    'Scrum',
    'REST API',
    'GraphQL',
    'Machine Learning',
    'Data Science',
    'DevOps',
    'Testing',
    'Security',
];

export const jobTypeSuggestions = [
    'Full-time',
    'Part-time',
    'Contract',
    'Freelance',
    'Internship',
    'Remote',
    'Hybrid',
    'On-site',
];

export const locationSuggestions = [
    'San Francisco, CA',
    'New York, NY',
    'Seattle, WA',
    'Austin, TX',
    'Boston, MA',
    'Los Angeles, CA',
    'Chicago, IL',
    'Denver, CO',
    'Remote',
];
