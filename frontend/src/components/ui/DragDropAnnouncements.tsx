/**
 * Drag and Drop Accessibility Announcements
 * Provides screen reader announcements for drag and drop operations
 */

'use client';

import { DragStartEvent, DragEndEvent, DragCancelEvent } from '@dnd-kit/core';
import { useState } from 'react';

interface DragDropAnnouncementsProps {
  onDragStart?: (event: DragStartEvent) => string;
  onDragEnd?: (event: DragEndEvent) => string;
  onDragCancel?: (event: DragCancelEvent) => string;
}

export function useDragDropAnnouncements({
  onDragStart,
  onDragEnd,
  onDragCancel,
}: DragDropAnnouncementsProps = {}) {
  const [announcement, setAnnouncement] = useState('');

  const announcements = {
    onDragStart: (event: DragStartEvent) => {
      if (onDragStart) {
        const message = onDragStart(event);
        setAnnouncement(message);
        return message;
      }
      const message = 'Picked up draggable item. Use arrow keys to move, Enter to drop, Escape to cancel.';
      setAnnouncement(message);
      return message;
    },
    onDragEnd: (event: DragEndEvent) => {
      if (onDragEnd) {
        const message = onDragEnd(event);
        setAnnouncement(message);
        return message;
      }
      if (event.over) {
        const message = 'Item dropped. Position updated.';
        setAnnouncement(message);
        return message;
      }
      const message = 'Item dropped at original position.';
      setAnnouncement(message);
      return message;
    },
    onDragCancel: (event: DragCancelEvent) => {
      if (onDragCancel) {
        const message = onDragCancel(event);
        setAnnouncement(message);
        return message;
      }
      const message = 'Drag cancelled. Item returned to original position.';
      setAnnouncement(message);
      return message;
    },
  };

  return { announcements, announcement };
}

/**
 * Live region component for screen reader announcements
 */
export function DragDropLiveRegion({ announcement }: { announcement: string }) {
  return (
    <div
      role="status"
      aria-live="assertive"
      aria-atomic="true"
      className="sr-only"
    >
      {announcement}
    </div>
  );
}

/**
 * Instructions component for keyboard users
 */
export function DragDropInstructions({ className = '' }: { className?: string }) {
  return (
    <div className={`text-xs text-neutral-500 dark:text-neutral-400 ${className}`}>
      <p>
        <strong>Keyboard navigation:</strong> Tab to focus on items, Space to pick up, Arrow keys
        to move, Enter to drop, Escape to cancel
      </p>
    </div>
  );
}
