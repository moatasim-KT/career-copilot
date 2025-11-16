/**
 * Saved Filters Component
 * Save and manage filter presets with localStorage
 */

'use client';

import React, { useState, useEffect } from 'react';

import { logger } from '@/lib/logger';
import { m, AnimatePresence } from '@/lib/motion';

// ============================================================================
// Types
// ============================================================================

export interface SavedFilter {
    id: string;
    name: string;
    filters: Record<string, any>;
    createdAt: string;
    updatedAt: string;
    icon?: string;
    color?: string;
}

export interface SavedFiltersProps {
    currentFilters: Record<string, any>;
    onApplyFilter: (filters: Record<string, any>) => void;
    storageKey?: string;
    className?: string;
}

// ============================================================================
// Saved Filters Component
// ============================================================================

export function SavedFilters({
    currentFilters,
    onApplyFilter,
    storageKey = 'career-copilot-saved-filters',
    className = '',
}: SavedFiltersProps) {
    const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingFilter, setEditingFilter] = useState<SavedFilter | null>(null);
    const [filterName, setFilterName] = useState('');

    // Load saved filters from localStorage
    useEffect(() => {
        const loadFilters = () => {
            try {
                const stored = localStorage.getItem(storageKey);
                if (stored) {
                    setSavedFilters(JSON.parse(stored));
                }
            } catch (error) {
                logger.error('Failed to load saved filters:', error);
            }
        };

        loadFilters();
    }, [storageKey]);

    // Save filters to localStorage
    const saveToStorage = (filters: SavedFilter[]) => {
        try {
            localStorage.setItem(storageKey, JSON.stringify(filters));
            setSavedFilters(filters);
        } catch (error) {
            logger.error('Failed to save filters:', error);
        }
    };

    // Create new filter
    const handleSaveFilter = () => {
        if (!filterName.trim()) return;

        const now = new Date().toISOString();
        const newFilter: SavedFilter = {
            id: `filter_${Date.now()}`,
            name: filterName,
            filters: currentFilters,
            createdAt: now,
            updatedAt: now,
        };

        saveToStorage([...savedFilters, newFilter]);
        setFilterName('');
        setIsModalOpen(false);
    };

    // Update existing filter
    const handleUpdateFilter = () => {
        if (!editingFilter || !filterName.trim()) return;

        const updated = savedFilters.map(f =>
            f.id === editingFilter.id
                ? { ...f, name: filterName, filters: currentFilters, updatedAt: new Date().toISOString() }
                : f,
        );

        saveToStorage(updated);
        setEditingFilter(null);
        setFilterName('');
        setIsModalOpen(false);
    };

    // Delete filter
    const handleDeleteFilter = (id: string) => {
        if (confirm('Are you sure you want to delete this saved filter?')) {
            saveToStorage(savedFilters.filter(f => f.id !== id));
        }
    };

    // Apply filter
    const handleApplyFilter = (filter: SavedFilter) => {
        onApplyFilter(filter.filters);
    };

    // Open modal for saving
    const openSaveModal = () => {
        setEditingFilter(null);
        setFilterName('');
        setIsModalOpen(true);
    };

    // Open modal for editing
    const openEditModal = (filter: SavedFilter) => {
        setEditingFilter(filter);
        setFilterName(filter.name);
        setIsModalOpen(true);
    };

    const hasActiveFilters = Object.keys(currentFilters).some(
        key => currentFilters[key] !== null && currentFilters[key] !== undefined && currentFilters[key] !== '',
    );

    return (
        <div className={className}>
            {/* Save Button */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-700">Saved Filters</h3>
                <button
                    onClick={openSaveModal}
                    disabled={!hasActiveFilters}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Save Current
                </button>
            </div>

            {/* Saved Filters List */}
            {savedFilters.length === 0 ? (
                <div className="text-center py-8 text-gray-500 text-sm">
                    <svg className="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                    </svg>
                    <p>No saved filters yet</p>
                    <p className="text-xs mt-1">Apply some filters and save them for quick access</p>
                </div>
            ) : (
                <div className="space-y-2">
                    <AnimatePresence>
                        {savedFilters.map((filter) => (
                            <FilterItem
                                key={filter.id}
                                filter={filter}
                                onApply={() => handleApplyFilter(filter)}
                                onEdit={() => openEditModal(filter)}
                                onDelete={() => handleDeleteFilter(filter.id)}
                            />
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Save/Edit Modal */}
            <AnimatePresence>
                {isModalOpen && (
                    <SaveFilterModal
                        isEditing={!!editingFilter}
                        filterName={filterName}
                        onFilterNameChange={setFilterName}
                        onSave={editingFilter ? handleUpdateFilter : handleSaveFilter}
                        onCancel={() => {
                            setIsModalOpen(false);
                            setEditingFilter(null);
                            setFilterName('');
                        }}
                    />
                )}
            </AnimatePresence>
        </div>
    );
}

// ============================================================================
// Filter Item Component
// ============================================================================

interface FilterItemProps {
    filter: SavedFilter;
    onApply: () => void;
    onEdit: () => void;
    onDelete: () => void;
}

function FilterItem({ filter, onApply, onEdit, onDelete }: FilterItemProps) {
    const filterCount = Object.keys(filter.filters).filter(
        key => filter.filters[key] !== null && filter.filters[key] !== undefined && filter.filters[key] !== '',
    ).length;

    return (
        <m.div
            layout
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="group flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
        >
            <button
                onClick={onApply}
                className="flex-1 flex items-center gap-3 text-left"
            >
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                    </svg>
                </div>

                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{filter.name}</p>
                    <p className="text-xs text-gray-500">{filterCount} filters active</p>
                </div>
            </button>

            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={onEdit}
                    className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                    aria-label="Edit filter"
                >
                    <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                </button>
                <button
                    onClick={onDelete}
                    className="p-1.5 hover:bg-red-100 rounded transition-colors"
                    aria-label="Delete filter"
                >
                    <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </div>
        </m.div>
    );
}

// ============================================================================
// Save Filter Modal
// ============================================================================

interface SaveFilterModalProps {
    isEditing: boolean;
    filterName: string;
    onFilterNameChange: (name: string) => void;
    onSave: () => void;
    onCancel: () => void;
}

function SaveFilterModal({
    isEditing,
    filterName,
    onFilterNameChange,
    onSave,
    onCancel,
}: SaveFilterModalProps) {
    return (
        <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={onCancel}
        >
            <m.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    {isEditing ? 'Edit Saved Filter' : 'Save Filter'}
                </h3>

                <div className="mb-4">
                    <label htmlFor="filter-name" className="block text-sm font-medium text-gray-700 mb-2">
                        Filter Name
                    </label>
                    <input
                        id="filter-name"
                        type="text"
                        value={filterName}
                        onChange={(e) => onFilterNameChange(e.target.value)}
                        placeholder="e.g., Remote Senior React Jobs"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        autoFocus
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && filterName.trim()) {
                                onSave();
                            }
                        }}
                    />
                </div>

                <div className="flex justify-end gap-2">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onSave}
                        disabled={!filterName.trim()}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isEditing ? 'Update' : 'Save'}
                    </button>
                </div>
            </m.div>
        </m.div>
    );
}

// ============================================================================
// Hooks for managing saved filters
// ============================================================================

export function useSavedFilters(storageKey: string = 'career-copilot-saved-filters') {
    const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([]);

    useEffect(() => {
        try {
            const stored = localStorage.getItem(storageKey);
            if (stored) {
                setSavedFilters(JSON.parse(stored));
            }
        } catch (error) {
            logger.error('Failed to load saved filters:', error);
        }
    }, [storageKey]);

    const saveFilter = (name: string, filters: Record<string, any>) => {
        const now = new Date().toISOString();
        const newFilter: SavedFilter = {
            id: `filter_${Date.now()}`,
            name,
            filters,
            createdAt: now,
            updatedAt: now,
        };

        const updated = [...savedFilters, newFilter];
        localStorage.setItem(storageKey, JSON.stringify(updated));
        setSavedFilters(updated);
    };

    const deleteFilter = (id: string) => {
        const updated = savedFilters.filter(f => f.id !== id);
        localStorage.setItem(storageKey, JSON.stringify(updated));
        setSavedFilters(updated);
    };

    const updateFilter = (id: string, name: string, filters: Record<string, any>) => {
        const updated = savedFilters.map(f =>
            f.id === id
                ? { ...f, name, filters, updatedAt: new Date().toISOString() }
                : f,
        );
        localStorage.setItem(storageKey, JSON.stringify(updated));
        setSavedFilters(updated);
    };

    return {
        savedFilters,
        saveFilter,
        deleteFilter,
        updateFilter,
    };
}
