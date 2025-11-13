# VirtualJobListGrid

**File:** `frontend/src/components/jobs/VirtualJobList.tsx`

## Description

VirtualJobList Component

Renders a virtualized list of job cards for optimal performance with large datasets.
Only renders items that are visible in the viewport plus a configurable overscan.



## Props


### `jobs`
- **Type:** `Job[]`
- **Required:** Yes

- **Description:** Array of jobs to display


### `onJobClick`
- **Type:** `(jobId: number | string) => void`
- **Required:** Yes

- **Description:** Callback when a job is clicked


### `selectedJobIds`
- **Type:** `(number | string)[]`
- **Required:** Yes

- **Description:** Array of selected job IDs


### `onSelectJob`
- **Type:** `(jobId: number | string) => void`
- **Required:** Yes

- **Description:** Callback when a job is selected/deselected


### `estimatedSize`
- **Type:** `number`
- **Required:** No

- **Description:** Estimated height of each job card in pixels (default: 200)


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


### `columns`
- **Type:** `{
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  }`
- **Required:** No

- **Description:** Number of columns per breakpoint


### `jobs`
- **Type:** `Job[]`
- **Required:** Yes

- **Description:** Array of jobs to display


### `onJobClick`
- **Type:** `(jobId: number | string) => void`
- **Required:** Yes

- **Description:** Callback when a job is clicked


### `selectedJobIds`
- **Type:** `(number | string)[]`
- **Required:** Yes

- **Description:** Array of selected job IDs


### `onSelectJob`
- **Type:** `(jobId: number | string) => void`
- **Required:** Yes

- **Description:** Callback when a job is selected/deselected


### `estimatedSize`
- **Type:** `number`
- **Required:** No

- **Description:** Estimated height of each job card in pixels (default: 200)


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
