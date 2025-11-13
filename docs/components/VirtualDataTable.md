# VirtualDataTable

**File:** `frontend/src/components/ui/DataTable/VirtualDataTable.tsx`

## Description

Performance Monitor Hook
Tracks FPS and render performance



## Props


### `columns`
- **Type:** `ColumnDef<TData, TValue>[]`
- **Required:** Yes




### `data`
- **Type:** `TData[]`
- **Required:** Yes




### `isLoading`
- **Type:** `boolean`
- **Required:** No




### `renderSubComponent`
- **Type:** `(row: TData) => React.ReactNode`
- **Required:** No




### `estimatedRowHeight`
- **Type:** `number`
- **Required:** No

- **Description:** Estimated height of each row in pixels (default: 53)


### `overscan`
- **Type:** `number`
- **Required:** No

- **Description:** Number of rows to render outside the visible area (default: 5)


### `enableVirtualization`
- **Type:** `boolean`
- **Required:** No

- **Description:** Enable virtualization (default: auto-enabled for 100+ rows)


### `enablePerformanceMonitoring`
- **Type:** `boolean`
- **Required:** No

- **Description:** Enable performance monitoring


### `enabled`
- **Type:** `boolean`
- **Required:** Yes




### `columns`
- **Type:** `ColumnDef<TData, TValue>[]`
- **Required:** Yes




### `data`
- **Type:** `TData[]`
- **Required:** Yes




### `isLoading`
- **Type:** `boolean`
- **Required:** No




### `renderSubComponent`
- **Type:** `(row: TData) => React.ReactNode`
- **Required:** No




### `estimatedRowHeight`
- **Type:** `number`
- **Required:** No

- **Description:** Estimated height of each row in pixels (default: 53)


### `overscan`
- **Type:** `number`
- **Required:** No

- **Description:** Number of rows to render outside the visible area (default: 5)


### `enableVirtualization`
- **Type:** `boolean`
- **Required:** No

- **Description:** Enable virtualization (default: auto-enabled for 100+ rows)


### `enablePerformanceMonitoring`
- **Type:** `boolean`
- **Required:** No

- **Description:** Enable performance monitoring



## Dependencies

- `./ColumnFilter`




---
*Auto-generated from component source*
