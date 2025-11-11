/**
 * Application Kanban Board
 * Drag and drop interface for managing application status
 */

'use client';

import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { AlertCircle, Plus } from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';
import { toast } from 'sonner';

import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';
import {
  Application,
  ApplicationStatus,
  KanbanColumn,
  KANBAN_COLUMNS,
} from '@/types/application';

import { ApplicationCard } from '../kanban/ApplicationCard';
import { KanbanColumnComponent } from '../kanban/KanbanColumn';

export default function ApplicationKanban() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeId, setActiveId] = useState<number | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
  );

  // Load applications
  useEffect(() => {
    let mounted = true;

    (async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.getApplications(0, 1000);
        if (!mounted) return;

        if (response && !response.error && response.data) {
          setApplications(response.data);
        }
      } catch (err) {
        if (!mounted) return;
        setError('Failed to load applications');
        logger.error('ApplicationKanban: load failed', err);
      } finally {
        if (mounted) setIsLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  // Group applications by status
  const columns: KanbanColumn[] = useMemo(() => {
    return KANBAN_COLUMNS.map((col) => ({
      ...col,
      applications: applications.filter((app) => app.status === col.id),
    }));
  }, [applications]);

  const activeApplication = useMemo(
    () => applications.find((app) => app.id === activeId),
    [activeId, applications],
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as number);
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as number;
    const overId = over.id as string | number;

    // Find the application being dragged
    const activeApplication = applications.find((app) => app.id === activeId);
    if (!activeApplication) return;

    // Determine the target status
    let targetStatus: ApplicationStatus | null = null;

    // Check if over is a column
    if (typeof overId === 'string' && KANBAN_COLUMNS.some((col) => col.id === overId)) {
      targetStatus = overId as ApplicationStatus;
    } else if (typeof overId === 'number') {
      // Over is another application, find its column
      const overApplication = applications.find((app) => app.id === overId);
      if (overApplication) {
        targetStatus = overApplication.status as ApplicationStatus;
      }
    }

    if (targetStatus && activeApplication.status !== targetStatus) {
      // Optimistically update the UI
      setApplications((apps) =>
        apps.map((app) =>
          app.id === activeId ? { ...app, status: targetStatus } : app,
        ),
      );
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeId = active.id as number;
    const overId = over.id as string | number;

    // Find the application being dragged
    const activeApplication = applications.find((app) => app.id === activeId);
    if (!activeApplication) return;

    // Determine the target status
    let targetStatus: ApplicationStatus | null = null;

    // Check if over is a column
    if (typeof overId === 'string' && KANBAN_COLUMNS.some((col) => col.id === overId)) {
      targetStatus = overId as ApplicationStatus;
    } else if (typeof overId === 'number') {
      // Over is another application, find its column
      const overApplication = applications.find((app) => app.id === overId);
      if (overApplication) {
        targetStatus = overApplication.status as ApplicationStatus;
      }
    }

    if (!targetStatus || activeApplication.status === targetStatus) {
      return;
    }

    // Store previous state for rollback
    const previousApplications = [...applications];

    try {
      // Update via API
      const response = await apiClient.updateApplication(activeId, {
        status: targetStatus,
      });

      if (response && !response.error) {
        toast.success(
          `Application moved to ${targetStatus.charAt(0).toUpperCase() + targetStatus.slice(1)}`,
        );
      } else {
        throw new Error('Failed to update application');
      }
    } catch (err) {
      // Rollback on error
      setApplications(previousApplications);
      toast.error('Failed to update application status');
      logger.error('ApplicationKanban: update failed', err);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700 h-96"
              >
                <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4 mb-4"></div>
                <div className="space-y-3">
                  {[...Array(3)].map((_, j) => (
                    <div
                      key={j}
                      className="h-24 bg-neutral-200 dark:bg-neutral-700 rounded"
                    ></div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-4xl font-bold text-neutral-900 dark:text-white">
            Application Board
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-2">
            Drag and drop applications to update their status
          </p>
        </div>

        <button
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          onClick={() => {
            // TODO: Open add application modal
            toast.info('Add application feature coming soon');
          }}
        >
          <Plus className="h-5 w-5" />
          <span>Add Application</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400 dark:text-red-500" />
            <div className="ml-3">
              <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Kanban Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {columns.map((column) => (
            <KanbanColumnComponent key={column.id} column={column} />
          ))}
        </div>

        {/* Drag Overlay */}
        <DragOverlay>
          {activeApplication ? (
            <div className="opacity-90">
              <ApplicationCard application={activeApplication} isDragging />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Keyboard Instructions */}
      <div className="text-xs text-neutral-500 dark:text-neutral-400 text-center mt-8">
        <p>
          <strong>Keyboard:</strong> Tab to focus, Space to pick up, Arrow keys to move,
          Enter to drop
        </p>
      </div>
    </div>
  );
}
