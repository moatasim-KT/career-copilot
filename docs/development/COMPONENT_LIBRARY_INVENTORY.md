
# Component Library Inventory

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Migration Guide
- [[DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

## Overview

This document provides a comprehensive inventory of all UI components in the Career Copilot design system, organized by category with usage examples and implementation notes.

**Total Components**: 115+ components
**Base Library**: Shadcn/UI with custom extensions
**Location**: `frontend/src/components/ui/`

## Component Categories

### 1. Core UI Components

#### Buttons

| Component            | Status    | Description                         | Usage                     |
| -------------------- | --------- | ----------------------------------- | ------------------------- |
| `Button2.tsx`        | ✅ Primary | Main button component with variants | Actions, forms, CTAs      |
| `Button.tsx`         | 🟡 Legacy  | Original button (deprecated)        | Use Button2               |
| `IconButton.tsx`     | ✅ Active  | Icon-only button                    | Toolbars, compact actions |
| `CommandPalette.tsx` | ✅ Active  | Keyboard-driven command menu        | Quick actions, shortcuts  |

**Example:**
```tsx
import { Button2, IconButton } from '@/components/ui';

<Button2 variant="default" size="md">Submit</Button2>
<IconButton icon={<X />} aria-label="Close" />
```

#### Cards

| Component             | Status    | Description                | Usage                  |
| --------------------- | --------- | -------------------------- | ---------------------- |
| `Card2.tsx`           | ✅ Primary | Main card component        | Content containers     |
| `Card.tsx`            | 🟡 Legacy  | Original card (deprecated) | Use Card2              |
| `InfoCard.tsx`        | ✅ Active  | Informational card variant | Static information     |
| `InteractiveCard.tsx` | ✅ Active  | Clickable card             | Navigation, selections |
| `GlassCard.tsx`       | ✅ Active  | Glassmorphism effect card  | Hero sections          |

**Example:**
```tsx
import { Card2, InteractiveCard } from '@/components/ui';

<Card2>
  <Card2.Header>
    <Card2.Title>Title</Card2.Title>
  </Card2.Header>
  <Card2.Content>Content</Card2.Content>
</Card2>

<InteractiveCard onClick={handleClick}>
  Clickable content
</InteractiveCard>
```

### 2. Form Components

#### Inputs

| Component            | Status    | Description                   | Usage                   |
| -------------------- | --------- | ----------------------------- | ----------------------- |
| `Input2.tsx`         | ✅ Primary | Text input with label/error   | Forms, search           |
| `Input.tsx`          | 🟡 Legacy  | Original input                | Use Input2              |
| `Textarea2.tsx`      | ✅ Primary | Multi-line text input         | Long text, descriptions |
| `PasswordInput2.tsx` | ✅ Primary | Password input with show/hide | Authentication          |
| `SearchInput.tsx`    | ✅ Active  | Search input with icon        | Search functionality    |
| `FileUpload.tsx`     | ✅ Active  | File upload with drag-drop    | Resume, documents       |

**Example:**
```tsx
import { Input2, Textarea2, PasswordInput2 } from '@/components/ui';

<Input2 
  label="Email" 
  type="email"
  error={errors.email}
/>

<Textarea2 
  label="Description" 
  rows={4}
/>

<PasswordInput2 
  label="Password"
  showStrength
/>
```

#### Selects & Dropdowns

| Component          | Status    | Description              | Usage              |
| ------------------ | --------- | ------------------------ | ------------------ |
| `Select2.tsx`      | ✅ Primary | Dropdown select          | Single selection   |
| `MultiSelect.tsx`  | ✅ Active  | Multi-selection dropdown | Tags, filters      |
| `Combobox.tsx`     | ✅ Active  | Searchable select        | Large option lists |
| `NativeSelect.tsx` | ✅ Active  | Native HTML select       | Simple dropdowns   |

**Example:**
```tsx
import { Select2, MultiSelect, Combobox } from '@/components/ui';

<Select2 
  label="Status"
  options={statusOptions}
  value={status}
  onChange={setStatus}
/>

<MultiSelect 
  label="Skills"
  options={skillOptions}
  value={selectedSkills}
  onChange={setSelectedSkills}
/>
```

#### Checkboxes & Radio

| Component           | Status   | Description         | Usage              |
| ------------------- | -------- | ------------------- | ------------------ |
| `Checkbox.tsx`      | ✅ Active | Single checkbox     | Boolean inputs     |
| `CheckboxGroup.tsx` | ✅ Active | Multiple checkboxes | Multi-select       |
| `RadioGroup.tsx`    | ✅ Active | Radio button group  | Single selection   |
| `Switch.tsx`        | ✅ Active | Toggle switch       | Settings, features |

**Example:**
```tsx
import { Checkbox, RadioGroup, Switch } from '@/components/ui';

<Checkbox label="Remember me" />

<RadioGroup 
  label="Job Type"
  options={[
    { value: 'full-time', label: 'Full-time' },
    { value: 'part-time', label: 'Part-time' },
  ]}
/>

<Switch label="Email notifications" />
```

#### Date & Time

| Component             | Status    | Description          | Usage              |
| --------------------- | --------- | -------------------- | ------------------ |
| `DatePicker2.tsx`     | ✅ Primary | Calendar date picker | Date selection     |
| `DatePicker.tsx`      | 🟡 Legacy  | Original date picker | Use DatePicker2    |
| `DateRangePicker.tsx` | ✅ Active  | Date range selector  | Filtering, reports |
| `Calendar.tsx`        | ✅ Active  | Calendar component   | Event scheduling   |

**Example:**
```tsx
import { DatePicker2, DateRangePicker } from '@/components/ui';

<DatePicker2 
  label="Application Date"
  value={date}
  onChange={setDate}
/>

<DateRangePicker 
  startDate={startDate}
  endDate={endDate}
  onChange={handleRangeChange}
/>
```

#### Form Utilities

| Component        | Status   | Description                    | Usage             |
| ---------------- | -------- | ------------------------------ | ----------------- |
| `Form.tsx`       | ✅ Active | Form wrapper with validation   | All forms         |
| `FormField.tsx`  | ✅ Active | Field wrapper with label/error | Form fields       |
| `Label.tsx`      | ✅ Active | Form label                     | Input labels      |
| `FieldError.tsx` | ✅ Active | Error message display          | Validation errors |

### 3. Layout Components

| Component       | Status   | Description               | Usage                |
| --------------- | -------- | ------------------------- | -------------------- |
| `Container.tsx` | ✅ Active | Max-width container       | Page layouts         |
| `Grid.tsx`      | ✅ Active | Responsive grid           | Multi-column layouts |
| `Stack.tsx`     | ✅ Active | Vertical/horizontal stack | Component spacing    |
| `Separator.tsx` | ✅ Active | Divider line              | Section separation   |
| `Divider.tsx`   | ✅ Active | Visual divider            | Content separation   |
| `Spacer.tsx`    | ✅ Active | Empty spacing component   | Layout spacing       |

**Example:**
```tsx
import { Container, Grid, Stack, Separator } from '@/components/ui';

<Container>
  <Grid cols={3} gap={4}>
    <Card2>Column 1</Card2>
    <Card2>Column 2</Card2>
    <Card2>Column 3</Card2>
  </Grid>
  
  <Separator className="my-6" />
  
  <Stack spacing={4}>
    <div>Item 1</div>
    <div>Item 2</div>
  </Stack>
</Container>
```

### 4. Overlay Components

#### Modals & Dialogs

| Component          | Status    | Description         | Usage                   |
| ------------------ | --------- | ------------------- | ----------------------- |
| `Modal2.tsx`       | ✅ Primary | Full-featured modal | Forms, detailed content |
| `Modal.tsx`        | 🟡 Legacy  | Original modal      | Use Modal2              |
| `Dialog2.tsx`      | ✅ Primary | Lightweight dialog  | Simple confirmations    |
| `Dialog.tsx`       | 🟡 Legacy  | Original dialog     | Use Dialog2             |
| `AlertDialog2.tsx` | ✅ Primary | Confirmation dialog | Destructive actions     |
| `AlertDialog.tsx`  | 🟡 Legacy  | Original alert      | Use AlertDialog2        |
| `Sheet.tsx`        | ✅ Active  | Side panel overlay  | Settings, filters       |
| `Drawer2.tsx`      | ✅ Primary | Slide-in drawer     | Mobile navigation       |

**Example:**
```tsx
import { Modal2, AlertDialog2, Sheet } from '@/components/ui';

<Modal2 open={isOpen} onClose={onClose}>
  <Modal2.Header>Title</Modal2.Header>
  <Modal2.Body>Content</Modal2.Body>
  <Modal2.Footer>Actions</Modal2.Footer>
</Modal2>

<AlertDialog2
  open={showConfirm}
  title="Delete Application?"
  onConfirm={handleDelete}
  onCancel={() => setShowConfirm(false)}
/>

<Sheet side="right">
  Filter options
</Sheet>
```

#### Popovers & Tooltips

| Component          | Status   | Description        | Usage               |
| ------------------ | -------- | ------------------ | ------------------- |
| `Popover.tsx`      | ✅ Active | Popup content      | Contextual info     |
| `Tooltip.tsx`      | ✅ Active | Hover tooltip      | Explanations, hints |
| `HoverCard.tsx`    | ✅ Active | Rich hover content | Previews            |
| `ContextMenu.tsx`  | ✅ Active | Right-click menu   | Actions             |
| `DropdownMenu.tsx` | ✅ Active | Dropdown menu      | Navigation, actions |

**Example:**
```tsx
import { Popover, Tooltip, DropdownMenu } from '@/components/ui';

<Tooltip content="Click to copy">
  <IconButton icon={<Copy />} />
</Tooltip>

<Popover>
  <Popover.Trigger>
    <Button2>Options</Button2>
  </Popover.Trigger>
  <Popover.Content>
    Filter options
  </Popover.Content>
</Popover>

<DropdownMenu>
  <DropdownMenu.Trigger>
    <Button2>Menu</Button2>
  </DropdownMenu.Trigger>
  <DropdownMenu.Content>
    <DropdownMenu.Item>Edit</DropdownMenu.Item>
    <DropdownMenu.Item>Delete</DropdownMenu.Item>
  </DropdownMenu.Content>
</DropdownMenu>
```

### 5. Feedback Components

#### Status Indicators

| Component             | Status   | Description        | Usage               |
| --------------------- | -------- | ------------------ | ------------------- |
| `Badge.tsx`           | ✅ Active | Status badge       | Labels, counts      |
| `StatusIndicator.tsx` | ✅ Active | Colored status dot | Online/offline      |
| `Chip.tsx`            | ✅ Active | Removable tag      | Filters, selections |
| `Tag.tsx`             | ✅ Active | Static label       | Categories          |

**Example:**
```tsx
import { Badge, StatusIndicator, Chip } from '@/components/ui';

<Badge variant="success">Applied</Badge>
<Badge variant="warning" count={5}>Pending</Badge>

<StatusIndicator status="online" />

<Chip onRemove={handleRemove}>React</Chip>
```

#### Loading States

| Component               | Status    | Description        | Usage            |
| ----------------------- | --------- | ------------------ | ---------------- |
| `Spinner2.tsx`          | ✅ Primary | Loading spinner    | Async operations |
| `Spinner.tsx`           | 🟡 Legacy  | Original spinner   | Use Spinner2     |
| `DotsLoader.tsx`        | ✅ Active  | Three-dot loader   | Inline loading   |
| `LoadingOverlay.tsx`    | ✅ Active  | Full-page overlay  | Page loading     |
| `LoadingTransition.tsx` | ✅ Active  | Smooth transitions | Content loading  |
| `ProgressBar.tsx`       | ✅ Active  | Progress indicator | File uploads     |
| `ProgressCircle.tsx`    | ✅ Active  | Circular progress  | Completion %     |

**Example:**
```tsx
import { 
  Spinner2, 
  LoadingTransition, 
  LoadingOverlay, 
  ProgressBar 
} from '@/components/ui';

<Spinner2 size="md" />

<LoadingTransition loading={isLoading}>
  <DataTable data={data} />
</LoadingTransition>

<LoadingOverlay loading={isLoading} />

<ProgressBar value={progress} max={100} />
```

#### Skeleton Loaders

| Component             | Status    | Description            | Usage             |
| --------------------- | --------- | ---------------------- | ----------------- |
| `Skeleton2.tsx`       | ✅ Primary | Basic skeleton         | Generic loading   |
| `Skeleton.tsx`        | 🟡 Legacy  | Original skeleton      | Use Skeleton2     |
| `SkeletonCard2.tsx`   | ✅ Primary | Card skeleton          | Card loading      |
| `SkeletonCard.tsx`    | 🟡 Legacy  | Original card skeleton | Use SkeletonCard2 |
| `SkeletonTable2.tsx`  | ✅ Primary | Table skeleton         | Table loading     |
| `SkeletonAvatar2.tsx` | ✅ Primary | Avatar skeleton        | Avatar loading    |

**Example:**
```tsx
import { Skeleton2, SkeletonCard2, SkeletonTable2 } from '@/components/ui';

{isLoading ? (
  <>
    <Skeleton2 className="h-8 w-48" />
    <SkeletonCard2 />
    <SkeletonTable2 rows={5} columns={4} />
  </>
) : (
  <ActualContent />
)}
```

#### Messages & Alerts

| Component           | Status    | Description         | Usage              |
| ------------------- | --------- | ------------------- | ------------------ |
| `Alert2.tsx`        | ✅ Primary | Alert message       | Notifications      |
| `Toast.tsx`         | ✅ Active  | Toast notification  | Temporary messages |
| `Banner.tsx`        | ✅ Active  | Full-width banner   | Announcements      |
| `ErrorBoundary.tsx` | ✅ Active  | Error boundary      | Error handling     |
| `EmptyState.tsx`    | ✅ Active  | Empty state message | No data states     |

**Example:**
```tsx
import { Alert2, Toast, EmptyState } from '@/components/ui';

<Alert2 variant="info">
  Your application was submitted successfully
</Alert2>

{data.length === 0 && (
  <EmptyState 
    title="No applications"
    description="Start applying to jobs"
    action={<Button2>Browse Jobs</Button2>}
  />
)}
```

### 6. Navigation Components

| Component            | Status   | Description       | Usage             |
| -------------------- | -------- | ----------------- | ----------------- |
| `Tabs.tsx`           | ✅ Active | Tabbed navigation | Content sections  |
| `Breadcrumb.tsx`     | ✅ Active | Breadcrumb trail  | Page hierarchy    |
| `Pagination.tsx`     | ✅ Active | Page navigation   | Large data sets   |
| `NavigationMenu.tsx` | ✅ Active | Main navigation   | Header navigation |
| `Sidebar.tsx`        | ✅ Active | Side navigation   | Dashboard nav     |
| `PrefetchLink.tsx`   | ✅ Active | Prefetching link  | Fast navigation   |

**Example:**
```tsx
import { Tabs, Breadcrumb, Pagination } from '@/components/ui';

<Tabs defaultValue="all">
  <Tabs.List>
    <Tabs.Trigger value="all">All</Tabs.Trigger>
    <Tabs.Trigger value="active">Active</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="all">Content</Tabs.Content>
</Tabs>

<Breadcrumb>
  <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
  <Breadcrumb.Item href="/jobs">Jobs</Breadcrumb.Item>
  <Breadcrumb.Item>Details</Breadcrumb.Item>
</Breadcrumb>

<Pagination 
  currentPage={page}
  totalPages={total}
  onPageChange={setPage}
/>
```

### 7. Data Display Components

#### Tables

| Component              | Status   | Description         | Usage          |
| ---------------------- | -------- | ------------------- | -------------- |
| `DataTable`            | ✅ Active | Full-featured table | Data grids     |
| `VirtualDataTable.tsx` | ✅ Active | Virtualized table   | Large datasets |
| `DataTableHeader.tsx`  | ✅ Active | Table header        | Column headers |
| `DataTableRow.tsx`     | ✅ Active | Table row           | Data rows      |
| `Table.tsx`            | ✅ Active | Basic table         | Simple data    |

**Example:**
```tsx
import { DataTable } from '@/components/ui';

<DataTable
  columns={[
    { key: 'name', label: 'Name', sortable: true },
    { key: 'status', label: 'Status' },
  ]}
  data={applications}
  sortable
  filterable
  pageSize={20}
  onRowClick={handleRowClick}
/>
```

#### Lists

| Component         | Status   | Description      | Usage        |
| ----------------- | -------- | ---------------- | ------------ |
| `List.tsx`        | ✅ Active | Generic list     | Simple lists |
| `ListItem.tsx`    | ✅ Active | List item        | List entries |
| `VirtualList.tsx` | ✅ Active | Virtualized list | Long lists   |

#### Media

| Component         | Status   | Description      | Usage          |
| ----------------- | -------- | ---------------- | -------------- |
| `Avatar.tsx`      | ✅ Active | User avatar      | Profile images |
| `AvatarGroup.tsx` | ✅ Active | Multiple avatars | Team members   |
| `Image.tsx`       | ✅ Active | Optimized image  | Images         |
| `Logo.tsx`        | ✅ Active | Application logo | Branding       |

**Example:**
```tsx
import { Avatar, AvatarGroup } from '@/components/ui';

<Avatar src={user.avatar} alt={user.name} />

<AvatarGroup max={3}>
  <Avatar src={user1.avatar} />
  <Avatar src={user2.avatar} />
  <Avatar src={user3.avatar} />
</AvatarGroup>
```

### 8. Specialized Components

#### Dashboard Widgets

| Component             | Status   | Description      | Usage            |
| --------------------- | -------- | ---------------- | ---------------- |
| `Widget.tsx`          | ✅ Active | Dashboard widget | Metrics, charts  |
| `WidgetGrid.tsx`      | ✅ Active | Widget layout    | Dashboard layout |
| `MetricCard.tsx`      | ✅ Active | Metric display   | KPIs             |
| `QuickActionCard.tsx` | ✅ Active | Action card      | Quick tasks      |
| `StatCard.tsx`        | ✅ Active | Statistic card   | Numbers          |

**Example:**
```tsx
import { WidgetGrid, MetricCard, QuickActionCard } from '@/components/ui';

<WidgetGrid>
  <MetricCard 
    title="Applications"
    value={42}
    change="+12%"
    trend="up"
  />
  
  <QuickActionCard
    title="Add Job"
    icon={<Plus />}
    onClick={handleAddJob}
  />
</WidgetGrid>
```

#### Job Management

| Component              | Status   | Description      | Usage                |
| ---------------------- | -------- | ---------------- | -------------------- |
| `JobCard.tsx`          | ✅ Active | Job listing card | Job displays         |
| `ApplicationCard.tsx`  | ✅ Active | Application card | Application displays |
| `ApplicationList.tsx`  | ✅ Active | Application list | Application views    |
| `ActivityTimeline.tsx` | ✅ Active | Activity feed    | Timeline             |

**Example:**
```tsx
import { JobCard, ApplicationCard, ActivityTimeline } from '@/components/ui';

<JobCard
  title="Senior Developer"
  company="Acme Corp"
  location="Berlin"
  salary="€80k-100k"
  onApply={handleApply}
/>

<ApplicationCard
  job={job}
  status="interview"
  appliedDate={date}
/>

<ActivityTimeline activities={activities} />
```

#### Utilities

| Component                | Status   | Description         | Usage              |
| ------------------------ | -------- | ------------------- | ------------------ |
| `ThemeToggle.tsx`        | ✅ Active | Dark mode toggle    | Theme switching    |
| `ConnectionStatus.tsx`   | ✅ Active | Network status      | Online indicator   |
| `OfflineBanner.tsx`      | ✅ Active | Offline message     | Offline mode       |
| `NotificationCenter.tsx` | ✅ Active | Notification system | Alerts             |
| `CookieConsent.tsx`      | ✅ Active | Cookie banner       | GDPR compliance    |
| `ScrollToTop.tsx`        | ✅ Active | Scroll button       | Page navigation    |
| `CommandPalette.tsx`     | ✅ Active | Command menu        | Keyboard shortcuts |

### 9. Widget Components

| Component                | Status   | Description            | Usage     |
| ------------------------ | -------- | ---------------------- | --------- |
| `ApplicationStats.tsx`   | ✅ Active | Application statistics | Dashboard |
| `RecentActivity.tsx`     | ✅ Active | Recent activity feed   | Dashboard |
| `UpcomingInterviews.tsx` | ✅ Active | Interview list         | Dashboard |
| `JobRecommendations.tsx` | ✅ Active | Job suggestions        | Dashboard |
| `SkillGap.tsx`           | ✅ Active | Skill analysis         | Profile   |

## Component Status Key

- ✅ **Active**: Current, recommended for use
- ✅ **Primary**: Main version of a component
- 🟡 **Legacy**: Deprecated, migrate to newer version
- 🚧 **WIP**: Work in progress, not ready
- 🔄 **Refactoring**: Being updated

## Component Versioning

### Version 2 Components (Primary)

These are the latest, recommended versions:
- `Button2.tsx` → Replaces `Button.tsx`
- `Card2.tsx` → Replaces `Card.tsx`
- `Input2.tsx` → Replaces `Input.tsx`
- `Modal2.tsx` → Replaces `Modal.tsx`
- `Dialog2.tsx` → Replaces `Dialog.tsx`
- `AlertDialog2.tsx` → Replaces `AlertDialog.tsx`
- `DatePicker2.tsx` → Replaces `DatePicker.tsx`
- `Spinner2.tsx` → Replaces `Spinner.tsx`
- `Skeleton2.tsx` → Replaces `Skeleton.tsx`
- `SkeletonCard2.tsx` → Replaces `SkeletonCard.tsx`

### Migration Strategy

When encountering legacy components:

1. **Identify the version 2 equivalent**
2. **Update imports**: `import { Button } from '@/components/ui'` → `import { Button2 } from '@/components/ui'`
3. **Review API changes**: Check for prop differences
4. **Test thoroughly**: Ensure functionality is maintained
5. **Update tests**: Update test files to reference new components

## Testing

### Component Tests

Tests are located in:
- `frontend/src/components/ui/__tests__/`
- Co-located `*.test.tsx` files

**Example test structure:**
```tsx
describe('Button2', () => {
  it('renders correctly', () => {
    render(<Button2>Click me</Button2>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button2 onClick={handleClick}>Click</Button2>);
    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### Storybook

Component stories are in:
- `frontend/src/components/ui/__stories__/`


## Related Documentation

- [[DESIGN_SYSTEM.md]] – Design tokens and guidelines
- [[NAMING_CONVENTIONS.md]] – Naming standards
- [[ACCESSIBILITY_GUIDE.md]] – Accessibility best practices
- [[DEVELOPER_GUIDE]] – Development setup

## Contribution Guidelines

When adding new components:

1. **Follow naming conventions** (see NAMING_CONVENTIONS.md)
2. **Use design tokens** from tailwind.config.ts
3. **Include TypeScript types** for all props
4. **Write tests** for all functionality
5. **Add Storybook story** for documentation
6. **Support dark mode** with `dark:` variants
7. **Include accessibility** features (ARIA labels, keyboard nav)
8. **Document usage** in this inventory

---

**Last Updated**: Auto-generated from component directory
**Total Components**: 115+
**Component Library**: Shadcn/UI + Custom Extensions
