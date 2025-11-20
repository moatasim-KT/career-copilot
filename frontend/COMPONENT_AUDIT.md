# Component Audit

This document inventories the UI components in `frontend/src/components/ui` and makes a decision on which to use, deprecate, or merge.

| Component | Status | Usage (Files) | Decision | Notes |
|---|---|---|---|---|
| `ActivityTimeline.tsx` | Legacy | TBD | TBD | |
| `AlertDialog2.tsx` | New | TBD | **Standard** | |
| `ApplicationCard.tsx` | Legacy | TBD | TBD | |
| `ApplicationTimeline.tsx` | Legacy | TBD | TBD | |
| `Badge.tsx` | Legacy | TBD | TBD | |
| `BulkActionBar.tsx` | Legacy | TBD | TBD | |
| `BulkOperationProgress.tsx`| Legacy | TBD | TBD | |
| `Button.tsx` | Legacy | ~100 | **Deprecate** | Re-exports `Button2.tsx`. All usages should be replaced with `Button2`. |
| `Button2.tsx` | New | ~50 | **Standard** | The actual implementation of the button component. |
| `Card.tsx` | Legacy | ~10 | **Deprecate** | A simple card component. |
| `Card2.tsx` | New | ~30 | **Standard** | A more advanced card component. It re-exports itself as `Card`. This re-export should be removed. |
| `Checkbox.tsx` | Legacy | TBD | TBD | |
| `CommandPalette.tsx` | Legacy | TBD | TBD | |
| `ConfirmBulkAction.tsx` | Legacy | TBD | TBD | |
| `ConfirmDialog.tsx` | Legacy | TBD | TBD | |
| `ConnectionStatus.tsx` | Legacy | TBD | TBD | |
| `Container.tsx` | Legacy | TBD | TBD | |
| `DatePicker.tsx` | Legacy | 0 | **Deprecate** | Simple date picker. |
| `DatePicker2.tsx` | New | 0 | **Standard** | More advanced, custom-built date picker. |
| `dialog.tsx` | Legacy | 0 | **Deprecate** | Uses `@radix-ui/react-dialog`. |
| `Dialog2.tsx` | New | 0 | **Standard** | Custom-built, all-in-one component. More modern and flexible. |
| `DotsLoader.tsx` | Legacy | TBD | TBD | |
| `DragDropAnnouncements.tsx`| Legacy | TBD | TBD | |
| `DraggableList.tsx` | Legacy | TBD | TBD | |
| `Drawer.tsx` | Legacy | 0 | **Deprecate** | Simple drawer component. |
| `Drawer2.tsx` | New | 0 | **Standard** | More advanced, with more features and a more modern look and feel. |
| `DropdownMenu.tsx` | Legacy | TBD | TBD | |
| `EmptyState.tsx` | Legacy | TBD | TBD | |
| `EnhancedDashboardSkeleton.tsx` | Legacy | TBD | TBD | |
| `ExportDropdown.tsx` | Legacy | TBD | TBD | |
| `FeatureFallback.tsx` | Legacy | TBD | TBD | |
| `FileUpload.tsx` | Legacy | TBD | **Deprecate** | Simple file upload component. |
| `FileUpload2.tsx` | New | TBD | **Standard** | More advanced component with drag-and-drop, multiple file selection, and previews. |
| `FilterPanel.tsx` | Legacy | TBD | TBD | |
| `FilterPanelSkeleton.tsx` | Legacy | TBD | TBD | |
| `Form.tsx` | Legacy | TBD | TBD | |
| `FormExample.tsx` | Example | TBD | TBD | |
| `Grid.tsx` | Legacy | TBD | TBD | |
| `HelpIcon.tsx` | Legacy | TBD | TBD | |
| `Input.tsx` | Legacy | TBD | **Deprecate** | Simple input component. |
| `Input2.tsx` | New | TBD | **Standard** | Much more advanced component with variants, states, icons, and more. |
| `JobCard.tsx` | Legacy | TBD | TBD | |
| `JobCardSkeleton.tsx` | Legacy | TBD | TBD | |
| `label.tsx` | Legacy | TBD | TBD | |
| `LoadingOverlay.tsx` | Legacy | TBD | TBD | |
| `LoadingSkeletons.tsx` | Legacy | TBD | TBD | |
| `LoadingTransition.tsx` | Legacy | TBD | TBD | |
| `MetricCard.tsx` | Legacy | TBD | TBD | |
| `Modal.tsx` | Legacy | TBD | **Deprecate** | Simple modal component. |
| `Modal2.tsx` | New | TBD | **Standard** | More advanced component with animations and a more modern look and feel. |
| `MultiSelect2.tsx` | New | TBD | **Standard** | |
| `notification-center.tsx` | Legacy | TBD | TBD | |
| `NotificationCenter.tsx` | Legacy | TBD | TBD | |
| `OfflineBanner.tsx` | Legacy | TBD | TBD | |
| `OptimizedImage.tsx` | Legacy | TBD | TBD | |
| `Pagination.tsx` | Legacy | TBD | TBD | |
| `PasswordInput2.tsx` | New | TBD | **Standard** | |
| `Popover.tsx` | Legacy | TBD | TBD | |
| `PrefetchLink.tsx` | Legacy | TBD | TBD | |
| `progress.tsx` | Legacy | TBD | TBD | |
| `ProgressBar.tsx` | Legacy | TBD | TBD | |
| `QuickActionCard.tsx` | Legacy | TBD | TBD | |
| `QuickActionsPanel.tsx` | Legacy | TBD | TBD | |
| `Select.tsx` | Legacy | TBD | **Deprecate** | Simple select component. |
| `Select2.tsx` | New | TBD | **Standard** | More advanced component with variants, icons, and a more modern look and feel. |
| `Skeleton.tsx` | Legacy | TBD | **Deprecate** | Very basic skeleton component. |
| `Skeleton2.tsx` | New | TBD | **Standard** | Much more advanced component with variants, animations, and more customization options. |
| `SkeletonAvatar2.tsx` | New | TBD | **Standard** | |
| `SkeletonCard2.tsx` | New | TBD | **Standard** | |
| `SkeletonTable2.tsx` | New | TBD | **Standard** | |
| `SkeletonText.tsx` | Legacy | TBD | **Deprecate** | TBD |
| `Spinner2.tsx` | New | TBD | **Standard** | |
| `StaggerReveal.tsx` | Legacy | TBD | TBD | |
| `StatusIndicator.tsx` | Legacy | TBD | TBD | |
| `Tabs.tsx` | Legacy | TBD | TBD | |
| `Textarea.tsx` | Legacy | TBD | **Deprecate** | Simple textarea component. |
| `Textarea2.tsx` | New | TBD | **Standard** | More advanced component with variants, character count, auto-resize, and a more modern look and feel. |
| `ThemeToggle.tsx` | Legacy | TBD | TBD | |
| `Tooltip.tsx` | Legacy | TBD | TBD | |
| `UndoToast.tsx` | Legacy | TBD | TBD | |
| `use-toast.tsx` | Legacy | TBD | TBD | |
| `Widget.tsx` | Legacy | TBD | TBD | |
| `WidgetGrid.tsx` | Legacy | TBD | TBD | |