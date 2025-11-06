/**
 * Bulk Operations Component
 * 
 * Enterprise-grade bulk operations for job applications with selection,
 * action buttons, progress tracking, and undo support.
 * 
 * @module components/bulk/BulkOperations
 */

'use client';

import { CheckSquare, Square, Trash2, Archive, Tag, Download, RotateCcw } from 'lucide-react';
import React, { useState, useCallback } from 'react';

export interface BulkItem {
    id: string | number;
    [key: string]: any;
}

export interface BulkAction {
    id: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    color?: string;
    confirmMessage?: string;
    handler: (selectedIds: (string | number)[]) => Promise<void>;
}

export interface BulkOperationsProps<T extends BulkItem> {
    items: T[];
    selectedIds: (string | number)[];
    onSelectionChange: (ids: (string | number)[]) => void;
    actions: BulkAction[];
    renderItem: (item: T, isSelected: boolean, onToggle: () => void) => React.ReactNode;
    onUndo?: () => void;
    canUndo?: boolean;
}

/**
 * Bulk Operations Component
 * 
 * Features:
 * - Multi-select with select all
 * - Configurable bulk actions
 * - Progress tracking
 * - Undo support
 * - Keyboard shortcuts (Ctrl+A for select all)
 * - Accessibility compliant
 * 
 * @example
 * ```tsx
 * <BulkOperations
 *   items={applications}
 *   selectedIds={selected}
 *   onSelectionChange={setSelected}
 *   actions={bulkActions}
 *   renderItem={(item, isSelected, onToggle) => (
 *     <ApplicationCard {...item} selected={isSelected} onSelect={onToggle} />
 *   )}
 * />
 * ```
 */
export function BulkOperations<T extends BulkItem>({
    items,
    selectedIds,
    onSelectionChange,
    actions,
    renderItem,
    onUndo,
    canUndo = false,
}: BulkOperationsProps<T>) {
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentAction, setCurrentAction] = useState<string | null>(null);

    const isAllSelected = items.length > 0 && selectedIds.length === items.length;
    const isSomeSelected = selectedIds.length > 0 && !isAllSelected;

    const handleSelectAll = useCallback(() => {
        if (isAllSelected) {
            onSelectionChange([]);
        } else {
            onSelectionChange(items.map((item) => item.id));
        }
    }, [isAllSelected, items, onSelectionChange]);

    const handleToggleItem = useCallback(
        (id: string | number) => {
            if (selectedIds.includes(id)) {
                onSelectionChange(selectedIds.filter((selectedId) => selectedId !== id));
            } else {
                onSelectionChange([...selectedIds, id]);
            }
        },
        [selectedIds, onSelectionChange],
    );

    const handleAction = useCallback(
        async (action: BulkAction) => {
            if (selectedIds.length === 0) return;

            if (action.confirmMessage) {
                const confirmed = window.confirm(
                    action.confirmMessage.replace('{count}', selectedIds.length.toString()),
                );
                if (!confirmed) return;
            }

            setIsProcessing(true);
            setCurrentAction(action.id);

            try {
                await action.handler(selectedIds);
                onSelectionChange([]);
            } catch (error) {
                console.error(`Bulk action ${action.id} failed:`, error);
            } finally {
                setIsProcessing(false);
                setCurrentAction(null);
            }
        },
        [selectedIds, onSelectionChange],
    );

    // Keyboard shortcut for select all
    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                e.preventDefault();
                handleSelectAll();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleSelectAll]);

    return (
        <div className="space-y-4">
            {/* Bulk Actions Toolbar */}
            <div className="sticky top-0 z-10 bg-white border-b border-gray-200 p-4 shadow-sm">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        {/* Select All Checkbox */}
                        <button
                            onClick={handleSelectAll}
                            className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-100 transition-colors"
                            aria-label={isAllSelected ? 'Deselect all' : 'Select all'}
                        >
                            {isAllSelected ? (
                                <CheckSquare className="w-5 h-5 text-blue-600" />
                            ) : isSomeSelected ? (
                                <div className="w-5 h-5 border-2 border-blue-600 bg-blue-100 rounded" />
                            ) : (
                                <Square className="w-5 h-5 text-gray-400" />
                            )}
                            <span className="text-sm font-medium text-gray-700">
                                {selectedIds.length > 0
                                    ? `${selectedIds.length} selected`
                                    : 'Select all'}
                            </span>
                        </button>

                        {/* Action Buttons */}
                        {selectedIds.length > 0 && (
                            <div className="flex items-center gap-2">
                                {actions.map((action) => {
                                    const Icon = action.icon;
                                    const isCurrentAction = currentAction === action.id;

                                    return (
                                        <button
                                            key={action.id}
                                            onClick={() => handleAction(action)}
                                            disabled={isProcessing}
                                            className={`
                        flex items-center gap-2 px-3 py-2 rounded-md font-medium
                        transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                        ${action.color || 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
                      `}
                                            aria-label={action.label}
                                        >
                                            <Icon className="w-4 h-4" />
                                            <span className="text-sm">
                                                {isCurrentAction ? 'Processing...' : action.label}
                                            </span>
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Undo Button */}
                    {canUndo && onUndo && (
                        <button
                            onClick={onUndo}
                            className="flex items-center gap-2 px-3 py-2 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                            aria-label="Undo last action"
                        >
                            <RotateCcw className="w-4 h-4" />
                            <span className="text-sm font-medium">Undo</span>
                        </button>
                    )}
                </div>

                {/* Progress Bar */}
                {isProcessing && (
                    <div className="mt-4">
                        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                            <div className="bg-blue-600 h-full animate-pulse" style={{ width: '100%' }} />
                        </div>
                    </div>
                )}
            </div>

            {/* Items List */}
            <div className="space-y-2">
                {items.map((item) => {
                    const isSelected = selectedIds.includes(item.id);
                    return (
                        <div key={item.id}>
                            {renderItem(item, isSelected, () => handleToggleItem(item.id))}
                        </div>
                    );
                })}
            </div>

            {/* Empty State */}
            {items.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                    <p>No items to display</p>
                </div>
            )}
        </div>
    );
}

/**
 * Predefined Bulk Actions
 * 
 * Common bulk actions for job applications
 */
export const BULK_ACTIONS: Record<string, Omit<BulkAction, 'handler'>> = {
    DELETE: {
        id: 'delete',
        label: 'Delete',
        icon: Trash2,
        color: 'bg-red-100 text-red-700 hover:bg-red-200',
        confirmMessage: 'Are you sure you want to delete {count} item(s)?',
    },
    ARCHIVE: {
        id: 'archive',
        label: 'Archive',
        icon: Archive,
        color: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
    },
    TAG: {
        id: 'tag',
        label: 'Add Tag',
        icon: Tag,
        color: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
    },
    EXPORT: {
        id: 'export',
        label: 'Export',
        icon: Download,
        color: 'bg-green-100 text-green-700 hover:bg-green-200',
    },
};
