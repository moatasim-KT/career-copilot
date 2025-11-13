# ExportDropdown

**File:** `frontend/src/components/ui/ExportDropdown.tsx`



## Props


### `data`
- **Type:** `T[]`
- **Required:** Yes

- **Description:** Data to export


### `selectedIds`
- **Type:** `(string | number)[]`
- **Required:** No

- **Description:** Selected row IDs (for selected export)


### `filename`
- **Type:** `string`
- **Required:** Yes

- **Description:** Filename base (without extension)


### `csvColumns`
- **Type:** `Array<{ key: keyof T; header: string }>`
- **Required:** No

- **Description:** CSV column configuration


### `pdfColumns`
- **Type:** `PDFColumn<T>[]`
- **Required:** No

- **Description:** PDF column configuration


### `pdfOptions`
- **Type:** `{
    title?: string;
    subtitle?: string;
    theme?: 'striped' | 'grid' | 'plain';
  }`
- **Required:** No

- **Description:** PDF export options


### `options`
- **Type:** `ExportOption[]`
- **Required:** No

- **Description:** Custom export options


### `onExportStart`
- **Type:** `(type: string) => void`
- **Required:** No

- **Description:** Callback when export starts


### `onExportComplete`
- **Type:** `(type: string) => void`
- **Required:** No

- **Description:** Callback when export completes


### `onExportError`
- **Type:** `(error: Error) => void`
- **Required:** No

- **Description:** Callback when export fails


### `variant`
- **Type:** `'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success' | 'link' | 'gradient'`
- **Required:** No

- **Description:** Button variant


### `size`
- **Type:** `'sm' | 'md' | 'lg'`
- **Required:** No

- **Description:** Button size


### `className`
- **Type:** `string`
- **Required:** No

- **Description:** Custom className



## Dependencies

- `./Button2`




---
*Auto-generated from component source*
