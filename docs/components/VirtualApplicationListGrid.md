# VirtualApplicationListGrid

**File:** `frontend/src/components/applications/VirtualApplicationList.tsx`

## Description

VirtualApplicationList Component

Renders a virtualized list of application cards for optimal performance with large datasets.
Only renders items that are visible in the viewport plus a configurable overscan.



## Props


### `applications`
- **Type:** `Application[]`
- **Required:** Yes

- **Description:** Array of applications to display


### `onApplicationClick`
- **Type:** `(applicationId: number) => void`
- **Required:** Yes

- **Description:** Callback when an application is clicked


### `selectedApplicationIds`
- **Type:** `number[]`
- **Required:** Yes

- **Description:** Array of selected application IDs


### `onSelectApplication`
- **Type:** `(applicationId: number) => void`
- **Required:** Yes

- **Description:** Callback when an application is selected/deselected


### `estimatedSize`
- **Type:** `number`
- **Required:** No

- **Description:** Estimated height of each application card in pixels (default: 220)


### `overscan`
- **Type:** `number`
- **Required:** No

- **Description:** Number of items to render outside the visible area (default: 5)


### `className`
- **Type:** `string`
- **Required:** No

- **Description:** Custom className for the container


### `emptyMessage`
- **Type:** `string`
- **Required:** No

- **Description:** Custom empty state message


### `variant`
- **Type:** `'default' | 'compact' | 'detailed'`
- **Required:** No

- **Description:** Card variant to use


### `columns`
- **Type:** `{
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  }`
- **Required:** No

- **Description:** Number of columns per breakpoint


### `applications`
- **Type:** `Application[]`
- **Required:** Yes

- **Description:** Array of applications to display


### `onApplicationClick`
- **Type:** `(applicationId: number) => void`
- **Required:** Yes

- **Description:** Callback when an application is clicked


### `selectedApplicationIds`
- **Type:** `number[]`
- **Required:** Yes

- **Description:** Array of selected application IDs


### `onSelectApplication`
- **Type:** `(applicationId: number) => void`
- **Required:** Yes

- **Description:** Callback when an application is selected/deselected


### `estimatedSize`
- **Type:** `number`
- **Required:** No

- **Description:** Estimated height of each application card in pixels (default: 220)


### `overscan`
- **Type:** `number`
- **Required:** No

- **Description:** Number of items to render outside the visible area (default: 5)


### `className`
- **Type:** `string`
- **Required:** No

- **Description:** Custom className for the container


### `emptyMessage`
- **Type:** `string`
- **Required:** No

- **Description:** Custom empty state message


### `variant`
- **Type:** `'default' | 'compact' | 'detailed'`
- **Required:** No

- **Description:** Card variant to use


### `columns`
- **Type:** `{
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  }`
- **Required:** No

- **Description:** Number of columns per breakpoint






---
*Auto-generated from component source*
