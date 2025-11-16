/**
 * Draggable widget wrapper component
 * Provides drag and drop functionality for dashboard widgets
 */

'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import { ReactNode } from 'react';

import { m } from '@/lib/motion';

interface DraggableWidgetProps {
  id: string;
  children: ReactNode;
  gridSpan?: {
    cols: number;
    rows?: number;
  };
}

export function DraggableWidget({ id, children, gridSpan }: DraggableWidgetProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  // Determine grid column span class
  const colSpanClass = gridSpan?.cols === 2 ? 'lg:col-span-2' : 'lg:col-span-1';

  return (
    <m.div
      ref={setNodeRef}
      style={style}
      className={`relative group ${colSpanClass}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Drag Handle */}
      <div
        {...attributes}
        {...listeners}
        className="absolute top-2 right-2 z-10 p-2 rounded-lg bg-white/80 dark:bg-neutral-800/80 backdrop-blur-sm border border-neutral-200 dark:border-neutral-700 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing shadow-sm hover:shadow-md"
        aria-label="Drag to reorder"
      >
        <GripVertical className="h-5 w-5 text-neutral-600 dark:text-neutral-400" />
      </div>

      {/* Widget Content */}
      <div className={isDragging ? 'pointer-events-none' : ''}>
        {children}
      </div>

      {/* Drop Indicator */}
      {isDragging && (
        <div className="absolute inset-0 border-2 border-dashed border-blue-500 dark:border-blue-400 rounded-lg bg-blue-50/50 dark:bg-blue-900/20 pointer-events-none" />
      )}
    </m.div>
  );
}
