/**
 * Hook for managing dashboard widget layout
 * Handles widget reordering, visibility, and persistence
 */

import { useState, useEffect, useCallback } from 'react';
import { DashboardWidget, DEFAULT_DASHBOARD_WIDGETS } from '@/types/dashboard';
import { logger } from '@/lib/logger';

const STORAGE_KEY = 'dashboard-layout';

export function useDashboardLayout() {
  const [widgets, setWidgets] = useState<DashboardWidget[]>(DEFAULT_DASHBOARD_WIDGETS);
  const [isLoading, setIsLoading] = useState(true);

  // Load layout from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Merge with defaults to handle new widgets
        const mergedWidgets = mergeWithDefaults(parsed.widgets);
        setWidgets(mergedWidgets);
      }
    } catch (error) {
      logger.error('Failed to load dashboard layout', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save layout to localStorage whenever it changes
  const saveLayout = useCallback((newWidgets: DashboardWidget[]) => {
    try {
      const layout = {
        widgets: newWidgets,
        lastUpdated: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
      logger.info('Dashboard layout saved');
    } catch (error) {
      logger.error('Failed to save dashboard layout', error);
    }
  }, []);

  // Reorder widgets
  const reorderWidgets = useCallback(
    (activeId: string, overId: string) => {
      setWidgets((prevWidgets) => {
        const oldIndex = prevWidgets.findIndex((w) => w.id === activeId);
        const newIndex = prevWidgets.findIndex((w) => w.id === overId);

        if (oldIndex === -1 || newIndex === -1) return prevWidgets;

        const newWidgets = [...prevWidgets];
        const [movedWidget] = newWidgets.splice(oldIndex, 1);
        newWidgets.splice(newIndex, 0, movedWidget);

        // Update positions
        const updatedWidgets = newWidgets.map((widget, index) => ({
          ...widget,
          position: index,
        }));

        saveLayout(updatedWidgets);
        return updatedWidgets;
      });
    },
    [saveLayout]
  );

  // Toggle widget visibility
  const toggleWidgetVisibility = useCallback(
    (widgetId: string) => {
      setWidgets((prevWidgets) => {
        const newWidgets = prevWidgets.map((widget) =>
          widget.id === widgetId
            ? { ...widget, visible: !widget.visible }
            : widget
        );
        saveLayout(newWidgets);
        return newWidgets;
      });
    },
    [saveLayout]
  );

  // Reset to default layout
  const resetLayout = useCallback(() => {
    setWidgets(DEFAULT_DASHBOARD_WIDGETS);
    saveLayout(DEFAULT_DASHBOARD_WIDGETS);
    logger.info('Dashboard layout reset to default');
  }, [saveLayout]);

  // Get visible widgets sorted by position
  const visibleWidgets = widgets
    .filter((w) => w.visible)
    .sort((a, b) => a.position - b.position);

  return {
    widgets,
    visibleWidgets,
    isLoading,
    reorderWidgets,
    toggleWidgetVisibility,
    resetLayout,
  };
}

/**
 * Merge stored widgets with defaults to handle new widgets
 */
function mergeWithDefaults(storedWidgets: DashboardWidget[]): DashboardWidget[] {
  const storedMap = new Map(storedWidgets.map((w) => [w.id, w]));
  const merged: DashboardWidget[] = [];

  // Add stored widgets first (maintaining their order)
  storedWidgets.forEach((widget) => {
    const defaultWidget = DEFAULT_DASHBOARD_WIDGETS.find((w) => w.id === widget.id);
    if (defaultWidget) {
      merged.push({
        ...defaultWidget,
        ...widget,
      });
    }
  });

  // Add any new default widgets that aren't in stored
  DEFAULT_DASHBOARD_WIDGETS.forEach((defaultWidget) => {
    if (!storedMap.has(defaultWidget.id)) {
      merged.push({
        ...defaultWidget,
        position: merged.length,
      });
    }
  });

  return merged;
}
