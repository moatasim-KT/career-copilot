/**
 * Application Card Component
 * Draggable card for displaying application information
 */

'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Calendar, DollarSign, GripVertical, MapPin } from 'lucide-react';

import { Application } from '@/types/application';

interface ApplicationCardProps {
  application: Application;
  isDragging?: boolean;
}

export function ApplicationCard({ application, isDragging = false }: ApplicationCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isSortableDragging,
  } = useSortable({ id: application.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isSortableDragging ? 0.5 : 1,
  };

  const isBeingDragged = isDragging || isSortableDragging;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer ${
        isBeingDragged ? 'shadow-2xl ring-2 ring-blue-500 dark:ring-blue-400' : ''
      }`}
    >
      {/* Drag Handle */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
            {application.job?.title || 'Unknown Position'}
          </h4>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            {application.job?.company || 'Unknown Company'}
          </p>
        </div>
        <div
          {...attributes}
          {...listeners}
          className="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 cursor-grab active:cursor-grabbing"
          aria-label="Drag to move"
        >
          <GripVertical className="h-5 w-5 text-neutral-400 dark:text-neutral-500" />
        </div>
      </div>

      {/* Application Details */}
      <div className="space-y-2">
        {application.job?.location && (
          <div className="flex items-center text-xs text-neutral-600 dark:text-neutral-400">
            <MapPin className="h-3 w-3 mr-1" />
            <span>{application.job.location}</span>
          </div>
        )}

        {application.job?.salary_range && (
          <div className="flex items-center text-xs text-neutral-600 dark:text-neutral-400">
            <DollarSign className="h-3 w-3 mr-1" />
            <span>{application.job.salary_range}</span>
          </div>
        )}

        {application.interview_date && (
          <div className="flex items-center text-xs text-neutral-600 dark:text-neutral-400">
            <Calendar className="h-3 w-3 mr-1" />
            <span>Interview: {new Date(application.interview_date).toLocaleDateString()}</span>
          </div>
        )}

        {application.applied_date && (
          <div className="flex items-center text-xs text-neutral-500 dark:text-neutral-500 mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
            <span>Applied: {new Date(application.applied_date).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {/* Notes Preview */}
      {application.notes && (
        <div className="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
          <p className="text-xs text-neutral-600 dark:text-neutral-400 line-clamp-2">
            {application.notes}
          </p>
        </div>
      )}
    </div>
  );
}
