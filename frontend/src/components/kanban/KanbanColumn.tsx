/**
 * Kanban Column Component
 * Displays a column of applications in the kanban board
 */

'use client';

import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { motion } from 'framer-motion';

import { KanbanColumn } from '@/types/application';

import { ApplicationCard } from './ApplicationCard';

interface KanbanColumnProps {
  column: KanbanColumn;
}

export function KanbanColumnComponent({ column }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
  });

  const colorClasses = {
    blue: 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700',
    purple:
      'bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700',
    green: 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700',
    red: 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700',
  };

  const headerColorClasses = {
    blue: 'text-blue-700 dark:text-blue-300',
    purple: 'text-purple-700 dark:text-purple-300',
    green: 'text-green-700 dark:text-green-300',
    red: 'text-red-700 dark:text-red-300',
  };

  return (
    <div
      ref={setNodeRef}
      className={`rounded-lg border-2 transition-colors ${
        isOver
          ? 'border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
          : 'border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50'
      }`}
    >
      {/* Column Header */}
      <div
        className={`p-4 border-b-2 ${colorClasses[column.color as keyof typeof colorClasses]}`}
      >
        <div className="flex items-center justify-between">
          <h3
            className={`text-lg font-semibold ${headerColorClasses[column.color as keyof typeof headerColorClasses]}`}
          >
            {column.title}
          </h3>
          <span className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
            {column.applications.length}
          </span>
        </div>
      </div>

      {/* Applications List */}
      <div className="p-4 space-y-3 min-h-[400px] max-h-[calc(100vh-300px)] overflow-y-auto">
        <SortableContext
          items={column.applications.map((app) => app.id)}
          strategy={verticalListSortingStrategy}
        >
          {column.applications.length > 0 ? (
            column.applications.map((application) => (
              <motion.div
                key={application.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <ApplicationCard application={application} />
              </motion.div>
            ))
          ) : (
            <div className="text-center py-8 text-neutral-500 dark:text-neutral-400">
              <p className="text-sm">No applications</p>
              <p className="text-xs mt-1">Drag applications here</p>
            </div>
          )}
        </SortableContext>
      </div>
    </div>
  );
}
