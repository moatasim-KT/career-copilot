# BulkOperations

**File:** `frontend/src/components/bulk/BulkOperations.tsx`

## Description

Bulk Operations Component

Features:
- Multi-select with select all
- Configurable bulk actions
- Progress tracking
- Undo support
- Keyboard shortcuts (Ctrl+A for select all)
- Accessibility compliant



## Props


### `items`
- **Type:** `T[]`
- **Required:** Yes




### `selectedIds`
- **Type:** `(string | number)[]`
- **Required:** Yes




### `onSelectionChange`
- **Type:** `(ids: (string | number)[]) => void`
- **Required:** Yes




### `actions`
- **Type:** `BulkAction[]`
- **Required:** Yes




### `renderItem`
- **Type:** `(item: T, isSelected: boolean, onToggle: () => void) => React.ReactNode`
- **Required:** Yes




### `onUndo`
- **Type:** `() => void`
- **Required:** No




### `canUndo`
- **Type:** `boolean`
- **Required:** No








---
*Auto-generated from component source*
