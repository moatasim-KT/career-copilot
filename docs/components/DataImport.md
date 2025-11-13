# DataImport

**File:** `frontend/src/components/features/DataImport.tsx`



## Props


### `onImport`
- **Type:** `(data: any[]) => Promise<void>`
- **Required:** Yes

- **Description:** Callback when import is complete


### `templateUrl`
- **Type:** `string`
- **Required:** No

- **Description:** CSV template URL for download


### `columns`
- **Type:** `DataImportColumn[]`
- **Required:** Yes

- **Description:** Column definitions


### `validator`
- **Type:** `(data: any[]) => { valid: boolean; errors: string[] }`
- **Required:** No

- **Description:** Validation function


### `title`
- **Type:** `string`
- **Required:** No

- **Description:** Title


### `description`
- **Type:** `string`
- **Required:** No

- **Description:** Description






---
*Auto-generated from component source*
