
# Career Copilot Design System

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

## Overview

The Career Copilot design system provides a consistent, accessible, and maintainable foundation for building user interfaces. It is built on top of Tailwind CSS with custom design tokens and integrates Shadcn/UI components.

## Design Tokens

Design tokens are the visual design atoms of the system — specifically, they are named entities that store visual design attributes.

### Color Palette

#### Primary Colors (Blue)
Professional blue palette for primary actions and branding.

```css
--color-primary-50: rgb(239 246 255)   /* Lightest */
--color-primary-100: rgb(219 234 254)
--color-primary-200: rgb(191 219 254)
--color-primary-300: rgb(147 197 253)
--color-primary-400: rgb(96 165 250)
--color-primary-500: rgb(59 130 246)   /* Main brand color */
--color-primary-600: rgb(37 99 235)
--color-primary-700: rgb(29 78 216)
--color-primary-800: rgb(30 64 175)
--color-primary-900: rgb(30 58 138)
--color-primary-950: rgb(23 37 84)     /* Darkest */
```

**Usage:**
- Primary buttons, links, and interactive elements
- Focus states and active indicators
- Brand elements and highlights

```tsx
// Example usage
<button className="bg-primary-500 hover:bg-primary-600 text-white">
  Apply Now
</button>
```

#### Neutral Colors (Blue-Gray)
Neutral palette for text, backgrounds, and UI elements.

```css
--color-neutral-50: rgb(248 250 252)   /* Backgrounds */
--color-neutral-100: rgb(241 245 249)  /* Subtle backgrounds */
--color-neutral-200: rgb(226 232 240)  /* Borders */
--color-neutral-300: rgb(203 213 225)  /* Dividers */
--color-neutral-400: rgb(148 163 184)  /* Placeholder text */
--color-neutral-500: rgb(100 116 139)  /* Secondary text */
--color-neutral-600: rgb(71 85 105)    /* Body text */
--color-neutral-700: rgb(51 65 85)     /* Headings */
--color-neutral-800: rgb(30 41 59)     /* Emphasis */
--color-neutral-900: rgb(15 23 42)     /* High contrast */
--color-neutral-950: rgb(2 6 23)       /* Maximum contrast */
```

**Usage:**
- Text hierarchy (900 for headings, 600 for body, 400 for placeholders)
- Backgrounds (50-100 for surfaces)
- Borders and dividers (200-300)

#### Semantic Colors

**Success (Green)**
```css
--color-success-50: rgb(240 253 244)
--color-success-500: rgb(34 197 94)    /* Main */
--color-success-600: rgb(22 163 74)    /* Hover */
--color-success-700: rgb(21 128 61)    /* Active */
```

**Warning (Orange)**
```css
--color-warning-50: rgb(255 247 237)
--color-warning-500: rgb(251 146 60)   /* Main */
--color-warning-600: rgb(234 88 12)    /* Hover */
--color-warning-700: rgb(194 65 12)    /* Active */
```

**Error (Red)**
```css
--color-error-50: rgb(254 242 242)
--color-error-500: rgb(239 68 68)      /* Main */
--color-error-600: rgb(220 38 38)      /* Hover */
--color-error-700: rgb(185 28 28)      /* Active */
```

**Info (Blue)**
```css
--color-info-50: rgb(239 246 255)
--color-info-500: rgb(59 130 246)
--color-info-600: rgb(37 99 235)
--color-info-700: rgb(29 78 216)
```

### Spacing Scale

8px-based spacing system for consistent rhythm.

```css
--space-0: 0        (0px)
--space-1: 0.25rem  (4px)   /* Tight spacing */
--space-2: 0.5rem   (8px)   /* Default gap */
--space-3: 0.75rem  (12px)
--space-4: 1rem     (16px)  /* Standard padding */
--space-5: 1.25rem  (20px)
--space-6: 1.5rem   (24px)  /* Section spacing */
--space-8: 2rem     (32px)
--space-10: 2.5rem  (40px)
--space-12: 3rem    (48px)
--space-16: 4rem    (64px)  /* Large spacing */
--space-20: 5rem    (80px)
--space-24: 6rem    (96px)
```

**Usage:**
```tsx
<div className="p-4">      {/* 16px padding */}
  <div className="mb-6">   {/* 24px margin bottom */}
    <h2 className="mb-2">  {/* 8px margin bottom */}
```

### Typography

#### Font Families
```css
--font-inter: 'Inter', system-ui, sans-serif  /* Main font */
--font-mono: ui-monospace, SFMono-Regular, monospace
```

#### Font Sizes
```css
--text-xs: 0.75rem     (12px) - Small labels
--text-sm: 0.875rem    (14px) - Secondary text
--text-base: 1rem      (16px) - Body text
--text-lg: 1.125rem    (18px) - Large text
--text-xl: 1.25rem     (20px) - Small headings
--text-2xl: 1.5rem     (24px) - H3
--text-3xl: 1.875rem   (30px) - H2
--text-4xl: 2.25rem    (36px) - H1
--text-5xl: 3rem       (48px) - Display
```

#### Line Heights
```css
--leading-tight: 1.25    /* Headings */
--leading-normal: 1.5    /* Body text */
--leading-relaxed: 1.75  /* Long-form content */
```

#### Font Weights
```css
--font-normal: 400
--font-medium: 500
--font-semibold: 600
--font-bold: 700
```

**Usage:**
```tsx
<h1 className="text-4xl font-bold leading-tight text-neutral-900">
  Dashboard
</h1>
<p className="text-base leading-normal text-neutral-600">
  Welcome back!
</p>
```

### Border Radius

```css
--radius-sm: 0.25rem    (4px)  /* Subtle rounding */
--radius-base: 0.375rem (6px)  /* Default */
--radius-md: 0.5rem     (8px)  /* Standard cards */
--radius-lg: 0.75rem    (12px) /* Large cards */
--radius-xl: 1rem       (16px) /* Hero sections */
--radius-2xl: 1.5rem    (24px) /* Special elements */
--radius-full: 9999px          /* Fully rounded */
```

**Usage:**
```tsx
<div className="rounded-md">    {/* Cards */}
<button className="rounded-lg"> {/* Buttons */}
<img className="rounded-full">  {/* Avatars */}
```

### Shadows

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1)
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25)
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)
--shadow-primary: 0 4px 14px 0 rgba(59, 130, 246, 0.39)
```

**Usage:**
```tsx
<div className="shadow-sm">   {/* Subtle elevation */}
<div className="shadow-md">   {/* Cards */}
<div className="shadow-lg">   {/* Modals, dropdowns */}
```

### Transitions

```css
--duration-fast: 150ms     /* Micro-interactions */
--duration-base: 200ms     /* Default */
--duration-slow: 300ms     /* Page transitions */
--duration-slower: 500ms   /* Animations */
```

**Usage:**
```tsx
<button className="transition-colors duration-200">
<div className="transition-all duration-slow">
```

## Component Library

### Core Components (Shadcn/UI Based)

#### Buttons

**Button2.tsx** - Primary button component

Variants:
- `default` - Primary action button
- `secondary` - Secondary actions
- `outline` - Tertiary actions
- `ghost` - Minimal actions
- `destructive` - Dangerous actions
- `link` - Text link style

Sizes:
- `sm` - Compact buttons (32px height)
- `md` - Standard buttons (40px height)
- `lg` - Large buttons (48px height)

```tsx
import { Button2 } from '@/components/ui/Button2';

<Button2 variant="default" size="md">
  Apply Now
</Button2>

<Button2 variant="outline" size="sm">
  Cancel
</Button2>

<Button2 variant="destructive" size="lg">
  Delete Application
</Button2>
```

#### Cards

**Card2.tsx** - Container component for content

```tsx
import { Card2 } from '@/components/ui/Card2';

<Card2>
  <Card2.Header>
    <Card2.Title>Job Title</Card2.Title>
    <Card2.Description>Company Name</Card2.Description>
  </Card2.Header>
  <Card2.Content>
    {/* Card content */}
  </Card2.Content>
  <Card2.Footer>
    {/* Card actions */}
  </Card2.Footer>
</Card2>
```

#### Form Components

**Input2.tsx** - Text input field
**Textarea2.tsx** - Multi-line text input
**Select2.tsx** - Dropdown select
**Checkbox.tsx** - Checkbox input
**PasswordInput2.tsx** - Password input with show/hide

```tsx
import { Input2, Textarea2, Select2, Checkbox } from '@/components/ui';

<Input2 
  label="Email" 
  placeholder="you@example.com"
  error="Invalid email"
/>

<Textarea2 
  label="Description" 
  rows={4}
/>

<Select2 
  label="Status"
  options={[
    { value: 'applied', label: 'Applied' },
    { value: 'interview', label: 'Interview' },
  ]}
/>

<Checkbox label="Remember me" />
```

#### Modals & Dialogs

**Modal2.tsx** - Full-featured modal
**Dialog2.tsx** - Lightweight dialog
**AlertDialog2.tsx** - Confirmation dialog
**Drawer2.tsx** - Side panel

```tsx
import { Modal2, AlertDialog2, Drawer2 } from '@/components/ui';

<Modal2 open={isOpen} onClose={() => setIsOpen(false)}>
  <Modal2.Header>Add Job</Modal2.Header>
  <Modal2.Body>
    {/* Form content */}
  </Modal2.Body>
  <Modal2.Footer>
    <Button2 onClick={handleSubmit}>Submit</Button2>
  </Modal2.Footer>
</Modal2>

<AlertDialog2
  open={confirmDelete}
  title="Delete Application?"
  description="This action cannot be undone."
  onConfirm={handleDelete}
  onCancel={() => setConfirmDelete(false)}
/>
```

#### Feedback Components

**Badge.tsx** - Status indicators
**StatusIndicator.tsx** - Visual status markers
**Spinner2.tsx** - Loading spinner
**ProgressBar.tsx** - Progress indicator
**EmptyState.tsx** - Empty state messages

```tsx
import { Badge, StatusIndicator, Spinner2, EmptyState } from '@/components/ui';

<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Rejected</Badge>

<StatusIndicator status="online" />
<StatusIndicator status="offline" />

<Spinner2 size="md" />

<EmptyState
  icon="📋"
  title="No applications yet"
  description="Start by browsing available jobs"
  action={<Button2>Browse Jobs</Button2>}
/>
```

#### Data Display

**DataTable** - Sortable, filterable table with virtualization
**Pagination.tsx** - Page navigation
**Tabs.tsx** - Tabbed navigation

```tsx
import { DataTable, Pagination, Tabs } from '@/components/ui';

<DataTable
  columns={columns}
  data={jobs}
  sortable
  filterable
  pageSize={20}
/>

<Pagination
  currentPage={page}
  totalPages={totalPages}
  onPageChange={setPage}
/>

<Tabs defaultValue="all">
  <Tabs.List>
    <Tabs.Trigger value="all">All</Tabs.Trigger>
    <Tabs.Trigger value="active">Active</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="all">
    {/* Content */}
  </Tabs.Content>
</Tabs>
```

### Loading States

**Skeleton Components** - For loading UI

```tsx
import { 
  Skeleton2, 
  SkeletonCard2, 
  SkeletonTable2,
  SkeletonAvatar2 
} from '@/components/ui';

<Skeleton2 className="h-8 w-48" />

<SkeletonCard2 />

<SkeletonTable2 rows={5} columns={4} />
```

**LoadingTransition.tsx** - Smooth loading transitions

```tsx
import { LoadingTransition } from '@/components/ui';

<LoadingTransition loading={isLoading}>
  <DataTable data={jobs} />
</LoadingTransition>
```

### Specialized Components

**JobCard.tsx** - Job listing card
**ApplicationCard.tsx** - Application card
**MetricCard.tsx** - Dashboard metric card
**QuickActionCard.tsx** - Action card for quick tasks
**ActivityTimeline.tsx** - Timeline for activity feed
**NotificationCenter.tsx** - Notification system
**ConnectionStatus.tsx** - Online/offline indicator
**OfflineBanner.tsx** - Offline mode banner

## Component Composition Patterns

### Card with Loading State

```tsx
<LoadingTransition loading={isLoading}>
  <Card2>
    <Card2.Header>
      <Card2.Title>Recent Applications</Card2.Title>
    </Card2.Header>
    <Card2.Content>
      {applications.length === 0 ? (
        <EmptyState 
          title="No applications" 
          description="Start applying to jobs"
        />
      ) : (
        <DataTable data={applications} columns={columns} />
      )}
    </Card2.Content>
  </Card2>
</LoadingTransition>
```

### Form with Validation

```tsx
<Form onSubmit={handleSubmit}>
  <Input2
    label="Company Name"
    name="company"
    required
    error={errors.company}
  />
  
  <Textarea2
    label="Job Description"
    name="description"
    rows={4}
    error={errors.description}
  />
  
  <div className="flex gap-2 justify-end">
    <Button2 variant="outline" onClick={onCancel}>
      Cancel
    </Button2>
    <Button2 type="submit" loading={isSubmitting}>
      Submit
    </Button2>
  </div>
</Form>
```

### Modal with Confirmation

```tsx
const [showConfirm, setShowConfirm] = useState(false);

<Modal2 open={isOpen} onClose={onClose}>
  <Modal2.Header>Delete Application</Modal2.Header>
  <Modal2.Body>
    <p>Are you sure you want to delete this application?</p>
  </Modal2.Body>
  <Modal2.Footer>
    <Button2 variant="outline" onClick={onClose}>
      Cancel
    </Button2>
    <Button2 
      variant="destructive" 
      onClick={() => setShowConfirm(true)}
    >
      Delete
    </Button2>
  </Modal2.Footer>
</Modal2>

<AlertDialog2
  open={showConfirm}
  title="Confirm Deletion"
  description="This cannot be undone."
  onConfirm={handleDelete}
  onCancel={() => setShowConfirm(false)}
/>
```

## Dark Mode

The system supports dark mode via Tailwind's `dark:` variant.

### Theme Toggle

```tsx
import { ThemeToggle } from '@/components/ui/ThemeToggle';

<ThemeToggle />
```

### Dark Mode Colors

Dark mode automatically switches color palettes:

```css
.dark {
  --background: 15 23 42;        /* Dark surface */
  --foreground: 248 250 252;     /* Light text */
  --muted: 30 41 59;             /* Dark muted */
  --border: 51 65 85;            /* Dark borders */
}
```

### Usage

```tsx
<div className="bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-50">
  Content adapts to theme
</div>
```

## Accessibility

### ARIA Labels

Always provide accessible labels:

```tsx
<Button2 aria-label="Close modal">
  <X />
</Button2>

<Input2 
  label="Email" 
  aria-describedby="email-error"
/>
```

### Keyboard Navigation

All interactive components support keyboard navigation:
- `Tab` / `Shift+Tab` - Navigate between elements
- `Enter` / `Space` - Activate buttons
- `Escape` - Close modals/dialogs
- Arrow keys - Navigate lists, tabs, dropdowns

### Focus Indicators

```tsx
<button className="focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
  Visible focus indicator
</button>
```

## Animation Guidelines

### Micro-interactions (150ms)

```tsx
<button className="transition-colors duration-fast hover:bg-primary-600">
```

### Standard transitions (200ms)

```tsx
<div className="transition-all duration-200">
```

### Page transitions (300ms)

```tsx
<div className="transition-opacity duration-slow">
```

### Available Animations

```tsx
className="animate-fade-in"     // Fade in
className="animate-slide-in"    // Slide from left
className="animate-slide-up"    // Slide from bottom
className="animate-scale-in"    // Scale from center
className="animate-shimmer"     // Loading shimmer
```

## Best Practices

### 1. Use Design Tokens

❌ **Don't:**
```tsx
<div style={{ backgroundColor: '#3B82F6' }}>
```

✅ **Do:**
```tsx
<div className="bg-primary-500">
```

### 2. Maintain Consistent Spacing

❌ **Don't:**
```tsx
<div style={{ marginBottom: '18px' }}>
```

✅ **Do:**
```tsx
<div className="mb-4">  {/* 16px from design system */}
```

### 3. Use Semantic Components

❌ **Don't:**
```tsx
<div className="bg-red-500 text-white px-4 py-2 rounded">
  Delete
</div>
```

✅ **Do:**
```tsx
<Button2 variant="destructive">
  Delete
</Button2>
```

### 4. Provide Loading States

❌ **Don't:**
```tsx
{isLoading ? <p>Loading...</p> : <DataTable />}
```

✅ **Do:**
```tsx
<LoadingTransition loading={isLoading}>
  <DataTable />
</LoadingTransition>
```

### 5. Handle Empty States

❌ **Don't:**
```tsx
{data.length === 0 && <p>No data</p>}
```

✅ **Do:**
```tsx
{data.length === 0 ? (
  <EmptyState 
    title="No applications yet"
    description="Start by browsing jobs"
    action={<Button2>Browse Jobs</Button2>}
  />
) : (
  <DataTable data={data} />
)}
```

## Component File Structure

```
components/ui/
├── Button2.tsx          # Primary button
├── Card2.tsx            # Card container
├── Input2.tsx           # Form input
├── Modal2.tsx           # Modal dialog
├── Badge.tsx            # Status badge
├── Skeleton2.tsx        # Loading skeleton
├── EmptyState.tsx       # Empty state message
├── DataTable/           # Complex table component
│   ├── VirtualDataTable.tsx
│   ├── DataTableHeader.tsx
│   └── DataTableRow.tsx
└── __tests__/           # Component tests
```


## Related Files

- [`frontend/tailwind.config.ts`](../frontend/tailwind.config.ts) – Tailwind Config
- [`frontend/src/app/globals.css`](../frontend/src/app/globals.css) – Global Styles
- [`frontend/src/components/ui/index.ts`](../frontend/src/components/ui/index.ts) – Component Index
- [`frontend/src/components/ui/__stories__/`](../frontend/src/components/ui/__stories__) – Storybook

## Migration Guide

When refactoring existing components to use the design system:

1. **Replace inline styles** with Tailwind classes
2. **Use design token classes** (e.g., `bg-primary-500` instead of `bg-blue-500`)
3. **Migrate to semantic components** (e.g., `Button2` instead of custom buttons)
4. **Add loading states** using `LoadingTransition` or `Skeleton`
5. **Add empty states** using `EmptyState`
6. **Ensure accessibility** with proper ARIA labels and keyboard support
7. **Test in dark mode** to ensure proper theming

---


**For questions or contributions**, see [[DEVELOPER_GUIDE]] or open an issue on GitHub.
