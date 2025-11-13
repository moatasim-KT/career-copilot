# dynamicImport

**File:** `frontend/src/lib/lazyLoad.tsx`

## Description

Dynamic Import with Loading State

Enhanced dynamic import with loading and error states



## Props


### `options`
- **Type:** `LazyLoadOptions`
- **Required:** No




### `urls`
- **Type:** `string[]`
- **Required:** Yes




### `href`
- **Type:** `string`
- **Required:** Yes




### `importFn`
- **Type:** `() => Promise<{ default: T }>`
- **Required:** Yes




### `options`
- **Type:** `{
    loading?: React.ComponentType;
    error?: React.ComponentType<{ error: Error }>;
  }`
- **Required:** No








---
*Auto-generated from component source*
