/**
 * Advanced Search Component with Fuzzy Matching
 * 
 * Enterprise-grade search with fuzzy matching, keyboard navigation,
 * recent searches, and search suggestions
 * 
 * @module components/common/AdvancedSearch
 */

'use client';

import { Search, X, Clock, TrendingUp, ArrowRight } from 'lucide-react';
import React, { useState, useRef, useEffect, useCallback } from 'react';

export interface SearchResult<T = any> {
    /** Unique identifier */
    id: string | number;
    /** Display title */
    title: string;
    /** Optional subtitle */
    subtitle?: string;
    /** Optional description */
    description?: string;
    /** Optional category */
    category?: string;
    /** Original data */
    data: T;
    /** Match score (0-1) */
    score?: number;
    /** Highlighted title with matches */
    highlightedTitle?: string;
}

export interface AdvancedSearchProps<T> {
    /** Placeholder text */
    placeholder?: string;
    /** Search results */
    results: SearchResult<T>[];
    /** Whether search is loading */
    isLoading?: boolean;
    /** Callback when search query changes */
    onSearch: (query: string) => void;
    /** Callback when a result is selected */
    onSelect: (result: SearchResult<T>) => void;
    /** Recent searches */
    recentSearches?: string[];
    /** Trending searches */
    trendingSearches?: string[];
    /** Debounce delay in milliseconds */
    debounceDelay?: number;
    /** Minimum characters to trigger search */
    minChars?: number;
    /** Custom result renderer */
    renderResult?: (result: SearchResult<T>) => React.ReactNode;
    /** Additional CSS classes */
    className?: string;
    /** Show recent searches */
    showRecent?: boolean;
    /** Show trending searches */
    showTrending?: boolean;
    /** Maximum results to show */
    maxResults?: number;
}

/**
 * Fuzzy Search Utility
 * 
 * Implements a simple fuzzy matching algorithm
 */
export function fuzzyMatch(query: string, text: string): { score: number; highlights: number[] } {
    query = query.toLowerCase();
    text = text.toLowerCase();

    let score = 0;
    let queryIndex = 0;
    const highlights: number[] = [];

    for (let i = 0; i < text.length && queryIndex < query.length; i++) {
        if (text[i] === query[queryIndex]) {
            score++;
            highlights.push(i);
            queryIndex++;
        }
    }

    // Normalize score (0-1)
    const normalizedScore = queryIndex === query.length ? score / text.length : 0;

    return { score: normalizedScore, highlights };
}

/**
 * Highlight matched text
 */
export function highlightText(text: string, highlights: number[]): React.ReactNode {
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    highlights.forEach((index, i) => {
        if (index > lastIndex) {
            parts.push(text.substring(lastIndex, index));
        }
        parts.push(
            <mark key={i} className="bg-yellow-100 text-neutral-900 font-medium">
                {text[index]}
            </mark>,
        );
        lastIndex = index + 1;
    });

    if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex));
    }

    return <>{parts}</>;
}

/**
 * Advanced Search Component
 * 
 * @example
 * ```tsx
 * function JobSearch() {
 *   const [results, setResults] = useState([]);
 *   
 *   const handleSearch = async (query) => {
 *     const data = await searchJobs(query);
 *     setResults(data);
 *   };
 *   
 *   return (
 *     <AdvancedSearch
 *       results={results}
 *       onSearch={handleSearch}
 *       onSelect={(result) => router.push(`/jobs/${result.id}`)}
 *       showRecent
 *       showTrending
 *     />
 *   );
 * }
 * ```
 */
export function AdvancedSearch<T>({
    placeholder = 'Search...',
    results = [],
    isLoading = false,
    onSearch,
    onSelect,
    recentSearches = [],
    trendingSearches = [],
    debounceDelay = 300,
    minChars = 2,
    renderResult,
    className = '',
    showRecent = true,
    showTrending = true,
    maxResults = 10,
}: AdvancedSearchProps<T>) {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const resultsRef = useRef<HTMLDivElement>(null);
    const debounceTimer = useRef<NodeJS.Timeout | null>(null);

    // Debounced search
    const debouncedSearch = useCallback(
        (value: string) => {
            if (debounceTimer.current) {
                clearTimeout(debounceTimer.current);
            }

            debounceTimer.current = setTimeout(() => {
                if (value.length >= minChars) {
                    onSearch(value);
                }
            }, debounceDelay);
        },
        [onSearch, debounceDelay, minChars],
    );

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setQuery(value);
        setIsOpen(true);
        setSelectedIndex(0);
        debouncedSearch(value);
    };

    // Handle result selection
    const handleSelect = (result: SearchResult<T>) => {
        onSelect(result);
        setQuery('');
        setIsOpen(false);
        inputRef.current?.blur();
    };

    // Handle quick search selection (recent/trending)
    const handleQuickSearch = (searchQuery: string) => {
        setQuery(searchQuery);
        setIsOpen(true);
        onSearch(searchQuery);
        inputRef.current?.focus();
    };

    // Keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen) return;

        const displayedResults = results.slice(0, maxResults);

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex((prev) => (prev + 1) % displayedResults.length);
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex((prev) => (prev - 1 + displayedResults.length) % displayedResults.length);
                break;
            case 'Enter':
                e.preventDefault();
                if (displayedResults[selectedIndex]) {
                    handleSelect(displayedResults[selectedIndex]);
                }
                break;
            case 'Escape':
                e.preventDefault();
                setIsOpen(false);
                inputRef.current?.blur();
                break;
        }
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (
                resultsRef.current &&
                !resultsRef.current.contains(e.target as Node) &&
                !inputRef.current?.contains(e.target as Node)
            ) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Clear search
    const handleClear = () => {
        setQuery('');
        setIsOpen(false);
        inputRef.current?.focus();
    };

    const displayedResults = results.slice(0, maxResults);
    const showQuickSearches = query.length < minChars && (recentSearches.length > 0 || trendingSearches.length > 0);

    return (
        <div className={`relative ${className}`}>
            {/* Search Input */}
            <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setIsOpen(true)}
                    placeholder={placeholder}
                    className="
            w-full pl-12 pr-12 py-3 rounded-lg border border-neutral-300
            focus:border-blue-500 focus:ring-2 focus:ring-blue-100
            transition-all outline-none text-base
          "
                    aria-label="Search"
                    aria-autocomplete="list"
                    aria-expanded={isOpen}
                    aria-controls="search-results"
                    role="combobox"
                />
                {query && (
                    <button
                        onClick={handleClear}
                        className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-neutral-100 rounded-full transition-colors"
                        aria-label="Clear search"
                    >
                        <X className="w-5 h-5 text-neutral-400" />
                    </button>
                )}
            </div>

            {/* Results Dropdown */}
            {isOpen && (
                <div
                    ref={resultsRef}
                    id="search-results"
                    className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border border-neutral-200 max-h-96 overflow-y-auto z-50"
                    role="listbox"
                >
                    {/* Loading */}
                    {isLoading && (
                        <div className="flex items-center justify-center py-8">
                            <div className="w-6 h-6 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
                        </div>
                    )}

                    {/* Quick Searches */}
                    {!isLoading && showQuickSearches && (
                        <div className="py-2">
                            {showRecent && recentSearches.length > 0 && (
<div className="px-4 py-2">
                                    <div className="flex items-center space-x-2 text-xs font-semibold text-neutral-500 uppercase mb-2">
                                        <Clock className="w-4 h-4" />
                                        <span>Recent Searches</span>
                                    </div>
                                    <div className="space-y-1">
                                        {recentSearches.map((search, index) => (
                                            <button
                                                key={index}
                                                onClick={() => handleQuickSearch(search)}
                                                className="w-full text-left px-3 py-2 rounded-md hover:bg-neutral-50 transition-colors flex items-center justify-between group"
                                            >
                                                <span className="text-neutral-700">{search}</span>
                                                <ArrowRight className="w-4 h-4 text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {showTrending && trendingSearches.length > 0 && (
                                <div className="px-4 py-2 border-t border-neutral-100">
                                    <div className="flex items-center space-x-2 text-xs font-semibold text-neutral-500 uppercase mb-2">
                                        <TrendingUp className="w-4 h-4" />
                                        <span>Trending</span>
                                    </div>
                                    <div className="space-y-1">
                                        {trendingSearches.map((search, index) => (
                                            <button
                                                key={index}
                                                onClick={() => handleQuickSearch(search)}
                                                className="w-full text-left px-3 py-2 rounded-md hover:bg-neutral-50 transition-colors flex items-center justify-between group"
                                            >
                                                <span className="text-neutral-700">{search}</span>
                                                <ArrowRight className="w-4 h-4 text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Search Results */}
                    {!isLoading && query.length >= minChars && (
                        <>
                            {displayedResults.length > 0 ? (
                                <div className="py-2">
                                    {displayedResults.map((result, index) => (
                                        <button
                                            key={result.id}
                                            onClick={() => handleSelect(result)}
                                            className={`
                        w-full text-left px-4 py-3 transition-colors
                        ${selectedIndex === index ? 'bg-blue-50' : 'hover:bg-neutral-50'}
                      `}
                                            role="option"
                                            aria-selected={selectedIndex === index}
                                        >
                                            {renderResult ? (
                                                renderResult(result)
                                            ) : (
                                                <div>
                                                    <div className="font-medium text-neutral-900 mb-1">
                                                        {result.highlightedTitle || result.title}
                                                    </div>
                                                    {result.subtitle && (
                                                        <div className="text-sm text-neutral-600 mb-1">{result.subtitle}</div>
                                                    )}
                                                    {result.description && (
                                                        <div className="text-sm text-neutral-500 line-clamp-2">
                                                            {result.description}
                                                        </div>
                                                    )}
                                                    {result.category && (
                                                        <div className="text-xs text-blue-600 mt-1">{result.category}</div>
                                                    )}
                                                </div>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="py-8 text-center text-neutral-500">
                                    <p>No results found for &quot;{query}&quot;</p>
                                    <p className="text-sm mt-1">Try a different search term</p>
                                </div>
                            )}
                        </>
                    )}

                    {/* Hint */}
                    {!isLoading && query.length > 0 && query.length < minChars && (
                        <div className="py-8 text-center text-neutral-500 text-sm">
                            Type at least {minChars} characters to search
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
