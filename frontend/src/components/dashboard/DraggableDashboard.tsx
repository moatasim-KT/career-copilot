/**
 * Draggable Dashboard Component
 * Provides drag and drop functionality for dashboard widgets
 */

'use client';

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { motion, AnimatePresence } from 'framer-motion';
import { RotateCcw, Settings, GripVertical } from 'lucide-react';
import { useState } from 'react';

import { DraggableWidget } from './DraggableWidget';
import { useDashboardLayout } from '@/hooks/useDashboardLayout';
import { DashboardWidget as DashboardWidgetType } from '@/types/dashboard';

interface DraggableDashboardProps {
  children: (widget: DashboardWidgetType) => React.ReactNode;
}

export function DraggableDashboard({ children }: DraggableDashboardProps) {
  const {
    visibleWidgets,
    isLoading,
    reorderWidgets,
    resetLayout,
  } = useDashboardLayout();

  const [activeId, setActiveId] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement required to start drag
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      reorderWidgets(active.id as string, over.id as string);
    }

    setActiveId(null);
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  const handleResetLayout = () => {
    if (confirm('Are you sure you want to reset the dashboard layout to default?')) {
      resetLayout();
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700 h-64"
              >
                <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-4"></div>
                <div className="h-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const activeWidget = visibleWidgets.find((w) => w.id === activeId);

  return (
    <div className="space-y-6">
      {/* Dashboard Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            Dashboard Layout
          </h2>
          <span className="text-sm text-neutral-500 dark:text-neutral-400">
            (Drag widgets to reorder)
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
            aria-label="Toggle widget settings"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </button>

          <button
            onClick={handleResetLayout}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
            aria-label="Reset layout to default"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Reset Layout</span>
          </button>
        </div>
      </div>

      {/* Widget Settings Panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white dark:bg-neutral-800 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700 p-4 overflow-hidden"
          >
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
              Widget Visibility
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              All widgets are currently visible. Widget visibility controls coming soon.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Draggable Widgets Grid */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <SortableContext
          items={visibleWidgets.map((w) => w.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {visibleWidgets.map((widget) => (
              <DraggableWidget
                key={widget.id}
                id={widget.id}
                gridSpan={widget.gridSpan}
              >
                {children(widget)}
              </DraggableWidget>
            ))}
          </div>
        </SortableContext>

        {/* Drag Overlay */}
        <DragOverlay>
          {activeWidget ? (
            <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-2xl border-2 border-blue-500 dark:border-blue-400 p-6 opacity-90">
              <div className="flex items-center space-x-2">
                <GripVertical className="h-5 w-5 text-neutral-600 dark:text-neutral-400" />
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  {activeWidget.title}
                </h3>
              </div>
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Keyboard Instructions */}
      <div className="text-xs text-neutral-500 dark:text-neutral-400 text-center">
        <p>
          <strong>Keyboard:</strong> Tab to focus, Space to pick up, Arrow keys to move, Enter to drop
        </p>
      </div>
    </div>
  );
}
