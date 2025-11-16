/**
 * Draggable List Component
 * Generic component for drag-to-reorder functionality
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
  DragCancelEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import React, { ReactNode } from 'react';

import {
  useDragDropAnnouncements,
  DragDropLiveRegion,
  DragDropInstructions,
} from './DragDropAnnouncements';

interface DraggableListProps<T> {
  items: T[];
  onReorder: (items: T[]) => void;
  renderItem: (item: T, isDragging?: boolean) => ReactNode;
  getItemId: (item: T) => string | number;
  className?: string;
}

export function DraggableList<T>({
  items,
  onReorder,
  renderItem,
  getItemId,
  className = '',
}: DraggableListProps<T>) {
  const [activeId, setActiveId] = React.useState<string | number | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  // Accessibility announcements
  const { announcements, announcement } = useDragDropAnnouncements({
    onDragStart: () => 'Picked up item. Use arrow keys to move, Enter to drop, Escape to cancel.',
    onDragEnd: (event) => {
      if (event.over && event.active.id !== event.over.id) {
        return 'Item moved to new position.';
      }
      return 'Item dropped at original position.';
    },
    onDragCancel: () => 'Drag cancelled. Item returned to original position.',
  });

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id);
    announcements.onDragStart(event);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex((item) => getItemId(item) === active.id);
      const newIndex = items.findIndex((item) => getItemId(item) === over.id);

      if (oldIndex !== -1 && newIndex !== -1) {
        const newItems = arrayMove(items, oldIndex, newIndex);
        onReorder(newItems);
      }
    }

    setActiveId(null);
    announcements.onDragEnd(event);
  };

  const handleDragCancel = (event: DragCancelEvent) => {
    setActiveId(null);
    announcements.onDragCancel(event);
  };

  const activeItem = items.find((item) => getItemId(item) === activeId);

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <SortableContext
          items={items.map((item) => getItemId(item))}
          strategy={verticalListSortingStrategy}
        >
          <div className={className}>
            {items.map((item) => (
              <DraggableListItem
                key={getItemId(item)}
                id={getItemId(item)}
                item={item}
                renderItem={renderItem}
              />
            ))}
          </div>
        </SortableContext>

        <DragOverlay>
          {activeItem ? (
            <div className="opacity-90">{renderItem(activeItem, true)}</div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Live region for screen reader announcements */}
      <DragDropLiveRegion announcement={announcement} />

      {/* Keyboard instructions */}
      <DragDropInstructions className="mt-4 text-center" />
    </>
  );
}

interface DraggableListItemProps<T> {
  id: string | number;
  item: T;
  renderItem: (item: T, isDragging?: boolean) => ReactNode;
}

function DraggableListItem<T>({ id, item, renderItem }: DraggableListItemProps<T>) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="relative group"
      role="listitem"
      aria-grabbed={isDragging}
    >
      {/* Drag Handle */}
      <div
        {...attributes}
        {...listeners}
        className="absolute left-2 top-1/2 -translate-y-1/2 z-10 p-1 rounded bg-white/80 dark:bg-neutral-800/80 backdrop-blur-sm border border-neutral-200 dark:border-neutral-700 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
        aria-label="Drag to reorder. Press Space to pick up, Arrow keys to move, Enter to drop, Escape to cancel."
        tabIndex={0}
      >
        <GripVertical className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
      </div>

      {/* Item Content */}
      <div className={isDragging ? 'pointer-events-none' : ''}>
        {renderItem(item, isDragging)}
      </div>
    </div>
  );
}
