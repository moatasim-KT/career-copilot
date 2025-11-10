/**
 * Bulk Actions Component
 * Multi-select and bulk operations for jobs
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import React, { useState, useEffect } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface BulkAction {
    id: string;
    label: string;
    icon: React.ReactNode;
    variant: 'primary' | 'secondary' | 'danger';
    onClick: (selectedIds: string[]) => void | Promise<void>;
    requiresConfirmation?: boolean;
    confirmationMessage?: string;
}

export interface BulkActionsBarProps {
    selectedIds: string[];
    totalCount: number;
    actions: BulkAction[];
    onClearSelection: () => void;
    className?: string;
}

// ============================================================================
// Bulk Actions Bar Component
// ============================================================================

export function BulkActionsBar({
    selectedIds,
    totalCount,
    actions,
    onClearSelection,
    className = '',
}: BulkActionsBarProps) {
    const [isProcessing, setIsProcessing] = useState(false);
    const [processingAction, setProcessingAction] = useState<string | null>(null);

    const selectedCount = selectedIds.length;
    const hasSelection = selectedCount > 0;

    const handleAction = async (action: BulkAction) => {
        if (action.requiresConfirmation) {
            const message = action.confirmationMessage ||
                `Are you sure you want to perform this action on ${selectedCount} item(s)?`;

            if (!confirm(message)) {
                return;
            }
        }

        try {
            setIsProcessing(true);
            setProcessingAction(action.id);
            await action.onClick(selectedIds);
        } catch (error) {
            console.error(`Failed to execute bulk action: ${action.id}`, error);
        } finally {
            setIsProcessing(false);
            setProcessingAction(null);
        }
    };

    return (
        <AnimatePresence>
            {hasSelection && (
                <motion.div
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 100, opacity: 0 }}
                    className={`
            fixed bottom-0 left-0 right-0 glass border-t border-gray-200 dark:border-neutral-700 shadow-lg z-40
            ${className}
          `}
                >
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                        <div className="flex items-center justify-between gap-4">
                            {/* Selection Info */}
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2">
                                    <div className="w-5 h-5 bg-blue-600 rounded flex items-center justify-center">
                                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                        </svg>
                                    </div>
                                    <span className="text-sm font-medium text-gray-900">
                                        {selectedCount} of {totalCount} selected
                                    </span>
                                </div>

                                <button
                                    onClick={onClearSelection}
                                    className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                                >
                                    Clear selection
                                </button>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center gap-2">
                                {actions.map((action) => (
                                    <BulkActionButton
                                        key={action.id}
                                        action={action}
                                        onClick={() => handleAction(action)}
                                        isProcessing={isProcessing && processingAction === action.id}
                                        disabled={isProcessing}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

// ============================================================================
// Bulk Action Button
// ============================================================================

interface BulkActionButtonProps {
    action: BulkAction;
    onClick: () => void;
    isProcessing: boolean;
    disabled: boolean;
}

function BulkActionButton({ action, onClick, isProcessing, disabled }: BulkActionButtonProps) {
    const variantClasses = {
        primary: 'bg-blue-600 text-white hover:bg-blue-700',
        secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
        danger: 'bg-red-600 text-white hover:bg-red-700',
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`
        inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
        transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
        ${variantClasses[action.variant]}
        ${isProcessing ? 'scale-95' : 'hover:scale-105'}
      `}
        >
            {isProcessing ? (
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
            ) : (
                action.icon
            )}
            <span>{action.label}</span>
        </button>
    );
}

// ============================================================================
// Checkbox Component for Selection
// ============================================================================

export interface SelectionCheckboxProps {
    id: string;
    isSelected: boolean;
    onToggle: (id: string) => void;
    className?: string;
}

export function SelectionCheckbox({
    id,
    isSelected,
    onToggle,
    className = '',
}: SelectionCheckboxProps) {
    return (
        <div className={`flex items-center ${className}`}>
            <input
                type="checkbox"
                id={`select-${id}`}
                checked={isSelected}
                onChange={() => onToggle(id)}
                onClick={(e) => e.stopPropagation()}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
            />
        </div>
    );
}

// ============================================================================
// Select All Checkbox
// ============================================================================

export interface SelectAllCheckboxProps {
    selectedCount: number;
    totalCount: number;
    onSelectAll: () => void;
    onClearAll: () => void;
    className?: string;
}

export function SelectAllCheckbox({
    selectedCount,
    totalCount,
    onSelectAll,
    onClearAll,
    className = '',
}: SelectAllCheckboxProps) {
    const isAllSelected = selectedCount === totalCount && totalCount > 0;
    const isSomeSelected = selectedCount > 0 && selectedCount < totalCount;

    const handleClick = () => {
        if (isAllSelected || isSomeSelected) {
            onClearAll();
        } else {
            onSelectAll();
        }
    };

    return (
        <div className={`flex items-center ${className}`}>
            <button
                type="button"
                onClick={handleClick}
                className="relative w-5 h-5 border-2 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
                {isAllSelected && (
                    <div className="absolute inset-0 bg-blue-600 rounded flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                )}
                {isSomeSelected && !isAllSelected && (
                    <div className="absolute inset-0 bg-blue-600 rounded flex items-center justify-center">
                        <div className="w-2 h-0.5 bg-white" />
                    </div>
                )}
            </button>
        </div>
    );
}

// ============================================================================
// Preset Bulk Actions for Jobs
// ============================================================================

export const jobBulkActions: BulkAction[] = [
    {
        id: 'save',
        label: 'Save Selected',
        variant: 'primary',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
        ),
        onClick: async (selectedIds) => {
            // Implement save logic
            console.log('Saving jobs:', selectedIds);
        },
    },
    {
        id: 'apply',
        label: 'Quick Apply',
        variant: 'primary',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
        onClick: async (selectedIds) => {
            console.log('Applying to jobs:', selectedIds);
        },
    },
    {
        id: 'export',
        label: 'Export',
        variant: 'secondary',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
        ),
        onClick: async (selectedIds) => {
            console.log('Exporting jobs:', selectedIds);
        },
    },
    {
        id: 'delete',
        label: 'Remove',
        variant: 'danger',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
        ),
        requiresConfirmation: true,
        confirmationMessage: 'Are you sure you want to remove the selected jobs? This action cannot be undone.',
        onClick: async (selectedIds) => {
            console.log('Deleting jobs:', selectedIds);
        },
    },
];

// ============================================================================
// Hook for managing bulk selection
// ============================================================================

export function useBulkSelection<T extends { id: string }>(items: T[]) {
    const [selectedIds, setSelectedIds] = useState<string[]>([]);

    const toggleSelection = (id: string) => {
        setSelectedIds(prev =>
            prev.includes(id)
                ? prev.filter(selectedId => selectedId !== id)
                : [...prev, id],
        );
    };

    const selectAll = () => {
        setSelectedIds(items.map(item => item.id));
    };

    const clearSelection = () => {
        setSelectedIds([]);
    };

    const isSelected = (id: string) => selectedIds.includes(id);

    const selectedItems = items.filter(item => selectedIds.includes(item.id));

    return {
        selectedIds,
        selectedItems,
        toggleSelection,
        selectAll,
        clearSelection,
        isSelected,
        selectedCount: selectedIds.length,
    };
}
