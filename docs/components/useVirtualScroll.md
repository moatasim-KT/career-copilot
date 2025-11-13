# useVirtualScroll

**File:** `frontend/src/components/common/VirtualScroll.tsx`

## Description

Use Virtual Scroll Hook

Lower-level hook for building custom virtual scroll implementations



## Props


### `items`
- **Type:** `T[]`
- **Required:** Yes

- **Description:** Array of items to render


### `itemHeight`
- **Type:** `number`
- **Required:** Yes

- **Description:** Height of each item in pixels


### `containerHeight`
- **Type:** `number`
- **Required:** Yes

- **Description:** Height of the scrollable container


### `overscan`
- **Type:** `number`
- **Required:** No

- **Description:** Number of items to render above and below visible area


### `renderItem`
- **Type:** `(item: T, index: number) => React.ReactNode`
- **Required:** Yes

- **Description:** Render function for each item


### `keyExtractor`
- **Type:** `(item: T, index: number) => string | number`
- **Required:** Yes

- **Description:** Unique key extractor for each item


### `className`
- **Type:** `string`
- **Required:** No

- **Description:** Optional className for the container


### `scrollClassName`
- **Type:** `string`
- **Required:** No

- **Description:** Optional className for the scroll container


### `onScroll`
- **Type:** `(scrollTop: number) => void`
- **Required:** No

- **Description:** Callback when scroll position changes


### `loadingComponent`
- **Type:** `React.ReactNode`
- **Required:** No

- **Description:** Optional loading indicator


### `emptyComponent`
- **Type:** `React.ReactNode`
- **Required:** No

- **Description:** Optional empty state component


### `isLoading`
- **Type:** `boolean`
- **Required:** No

- **Description:** Whether the list is loading


### `onLoadMore`
- **Type:** `() => void`
- **Required:** No

- **Description:** Callback when scrolled near bottom (for infinite scroll)


### `loadMoreThreshold`
- **Type:** `number`
- **Required:** No

- **Description:** Threshold in pixels from bottom to trigger onLoadMore


### `items`
- **Type:** `T[]`
- **Required:** Yes

- **Description:** Array of items to render


### `itemHeight`
- **Type:** `number`
- **Required:** Yes

- **Description:** Height of each item in pixels


### `containerHeight`
- **Type:** `number`
- **Required:** Yes

- **Description:** Height of the scrollable container


### `overscan`
- **Type:** `number`
- **Required:** No

- **Description:** Number of items to render above and below visible area


### `renderItem`
- **Type:** `(item: T, index: number) => React.ReactNode`
- **Required:** Yes

- **Description:** Render function for each item


### `keyExtractor`
- **Type:** `(item: T, index: number) => string | number`
- **Required:** Yes

- **Description:** Unique key extractor for each item


### `className`
- **Type:** `string`
- **Required:** No

- **Description:** Optional className for the container


### `scrollClassName`
- **Type:** `string`
- **Required:** No

- **Description:** Optional className for the scroll container


### `onScroll`
- **Type:** `(scrollTop: number) => void`
- **Required:** No

- **Description:** Callback when scroll position changes


### `loadingComponent`
- **Type:** `React.ReactNode`
- **Required:** No

- **Description:** Optional loading indicator


### `emptyComponent`
- **Type:** `React.ReactNode`
- **Required:** No

- **Description:** Optional empty state component


### `isLoading`
- **Type:** `boolean`
- **Required:** No

- **Description:** Whether the list is loading


### `onLoadMore`
- **Type:** `() => void`
- **Required:** No

- **Description:** Callback when scrolled near bottom (for infinite scroll)


### `loadMoreThreshold`
- **Type:** `number`
- **Required:** No

- **Description:** Threshold in pixels from bottom to trigger onLoadMore






---
*Auto-generated from component source*
