# ErrorFallback

**File:** `frontend/src/lib/sentry.tsx`

## Description

Error boundary fallback component



## Props


### `config`
- **Type:** `SentryConfig`
- **Required:** Yes




### `user`
- **Type:** `{
  id: string;
  email?: string;
  username?: string;
  [key: string]: any;
}`
- **Required:** Yes




### `name`
- **Type:** `string`
- **Required:** Yes




### `context`
- **Type:** `Record<string, any>`
- **Required:** Yes




### `error`
- **Type:** `Error`
- **Required:** Yes




### `context`
- **Type:** `{
    tags?: Record<string, string>;
    extra?: Record<string, any>;
    level?: string;
  }`
- **Required:** No




### `message`
- **Type:** `string`
- **Required:** Yes




### `context`
- **Type:** `{
    tags?: Record<string, string>;
    extra?: Record<string, any>;
    level?: string;
  }`
- **Required:** No




### `name`
- **Type:** `string`
- **Required:** Yes




### `op`
- **Type:** `string`
- **Required:** Yes




### `data`
- **Type:** `Record<string, any>`
- **Required:** No




### `breadcrumb`
- **Type:** `{
  category: string;
  message: string;
  level?: string;
  data?: Record<string, any>;
}`
- **Required:** Yes








---
*Auto-generated from component source*
