# Contextual Help Integration Guide

This guide shows how to add contextual help to various features throughout the application.

## Quick Start

Import the help components you need:

```tsx
import { HelpIcon, InlineHelp } from '@/components/ui/HelpIcon';
import { CommandPaletteHelp, AdvancedSearchHelp } from '@/components/help/ContextualHelp';
```

## Integration Examples

### 1. Adding Help Icons to Page Headers

```tsx
// In JobsPage.tsx
import { AdvancedSearchHelp } from '@/components/help/ContextualHelp';

export function JobsPage() {
  return (
    <div>
      <div className="flex items-center gap-2">
        <h1>Jobs</h1>
        <AdvancedSearchHelp />
      </div>
      {/* Rest of the page */}
    </div>
  );
}
```

### 2. Adding Help to Form Fields

```tsx
// In ProfileForm.tsx
import { InlineHelp } from '@/components/ui/HelpIcon';
import { EmailFieldHelp, PasswordFieldHelp } from '@/components/help/ContextualHelp';

export function ProfileForm() {
  return (
    <form>
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" />
        <EmailFieldHelp />
      </div>
      
      <div>
        <label htmlFor="password">Password</label>
        <input id="password" type="password" />
        <PasswordFieldHelp />
      </div>
    </form>
  );
}
```

### 3. Adding Help to Complex Features

```tsx
// In AdvancedSearch.tsx
import { HelpIcon } from '@/components/ui/HelpIcon';

export function AdvancedSearch() {
  return (
    <div>
      <div className="flex items-center gap-2">
        <h2>Query Builder</h2>
        <HelpIcon
          title="Query Builder"
          content={
            <div>
              <p>Build complex search queries with AND/OR logic.</p>
              <ul>
                <li>Click "Add Rule" to add a filter</li>
                <li>Click "Add Group" for nested logic</li>
                <li>Toggle between AND/OR operators</li>
              </ul>
            </div>
          }
          docsLink="/help#query-builder"
        />
      </div>
      {/* Query builder UI */}
    </div>
  );
}
```

### 4. Adding Tooltips to Buttons

```tsx
// In BulkActionBar.tsx
import { tooltipMessages } from '@/components/help/ContextualHelp';

export function BulkActionBar() {
  return (
    <div>
      <button title={tooltipMessages.delete} aria-label={tooltipMessages.delete}>
        <TrashIcon />
      </button>
      <button title={tooltipMessages.export} aria-label={tooltipMessages.export}>
        <DownloadIcon />
      </button>
    </div>
  );
}
```

### 5. Adding Helpful Placeholders

```tsx
// In SearchInput.tsx
import { helpfulPlaceholders } from '@/components/help/ContextualHelp';

export function SearchInput() {
  return (
    <input
      type="text"
      placeholder={helpfulPlaceholders.searchJobs}
      aria-label="Search jobs"
    />
  );
}
```

### 6. Adding First-Time Hints

```tsx
// In CommandPalette.tsx
import { useFirstTimeHint } from '@/hooks/useFirstTimeHint';

export function CommandPalette() {
  const { shouldShow, dismiss } = useFirstTimeHint('command-palette');
  
  return (
    <div>
      {shouldShow && (
        <div className="hint-tooltip">
          <p>Press ⌘K to open the command palette anytime!</p>
          <button onClick={dismiss}>Got it</button>
        </div>
      )}
      {/* Command palette UI */}
    </div>
  );
}
```

### 7. Adding Help to Settings Pages

```tsx
// In NotificationSettings.tsx
import { NotificationsHelp, NotificationPreferencesHelp } from '@/components/help/ContextualHelp';

export function NotificationSettings() {
  return (
    <div>
      <div className="flex items-center gap-2">
        <h2>Notification Preferences</h2>
        <NotificationsHelp />
      </div>
      
      <p className="text-sm text-neutral-600">
        Choose how and when you want to receive notifications.
      </p>
      
      <div className="mt-4">
        {/* Notification toggles */}
      </div>
      
      <NotificationPreferencesHelp />
    </div>
  );
}
```

### 8. Adding Help to Dashboard Widgets

```tsx
// In DashboardWidget.tsx
import { DashboardWidgetsHelp } from '@/components/help/ContextualHelp';

export function Dashboard() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <h1>Dashboard</h1>
        <DashboardWidgetsHelp />
      </div>
      {/* Dashboard widgets */}
    </div>
  );
}
```

### 9. Adding Help to Data Tables

```tsx
// In DataTable.tsx
import { HelpIcon } from '@/components/ui/HelpIcon';

export function DataTable() {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <button>Bulk Actions</button>
        <HelpIcon
          title="Bulk Actions"
          content="Select multiple rows using checkboxes, then choose an action from the toolbar."
          size="sm"
        />
      </div>
      {/* Table */}
    </div>
  );
}
```

### 10. Adding Help to Modals

```tsx
// In ExportModal.tsx
import { DataExportHelp } from '@/components/help/ContextualHelp';

export function ExportModal() {
  return (
    <Modal>
      <div className="flex items-center gap-2">
        <h2>Export Data</h2>
        <DataExportHelp />
      </div>
      {/* Export options */}
    </Modal>
  );
}
```

## Best Practices

### 1. When to Use Help Icons

- **Complex features**: Advanced search, query builders, bulk operations
- **New features**: Features users might not be familiar with
- **Settings**: Configuration options that need explanation
- **Forms**: Fields that require specific formats or have constraints

### 2. When to Use Inline Help

- **Form fields**: Provide guidance on what to enter
- **Validation**: Explain requirements (e.g., password strength)
- **Optional fields**: Clarify what the field is used for
- **Format examples**: Show expected input format

### 3. When to Use Tooltips

- **Icon buttons**: Buttons without text labels
- **Abbreviations**: Explain shortened terms
- **Status indicators**: Explain what each status means
- **Quick hints**: Brief, one-line explanations

### 4. When to Use First-Time Hints

- **Keyboard shortcuts**: Teach users about shortcuts
- **Hidden features**: Features that aren't immediately visible
- **Power user features**: Advanced functionality
- **New features**: Recently added features

### 5. Writing Good Help Content

**Do:**
- Be concise and clear
- Use simple language
- Provide examples
- Include keyboard shortcuts when relevant
- Link to full documentation for complex topics

**Don't:**
- Use technical jargon
- Write long paragraphs
- Assume prior knowledge
- Duplicate information that's already visible
- Overwhelm users with too much help

### 6. Accessibility Considerations

Always include:
- `aria-label` for icon buttons
- `title` attribute for tooltips
- Keyboard navigation support
- Screen reader announcements
- Focus management

Example:
```tsx
<button
  onClick={handleHelp}
  aria-label="Get help with advanced search"
  title="Get help"
>
  <HelpCircle />
</button>
```

## Testing Checklist

- [ ] Help icons are visible and clickable
- [ ] Popovers appear on hover/click
- [ ] Content is readable in both light and dark modes
- [ ] Links to documentation work
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Screen readers announce help content
- [ ] Mobile: Help icons are tappable (44x44px minimum)
- [ ] First-time hints can be dismissed
- [ ] Dismissed hints don't reappear

## Common Patterns

### Pattern 1: Section Header with Help

```tsx
<div className="flex items-center gap-2 mb-4">
  <h2 className="text-xl font-bold">Section Title</h2>
  <HelpIcon
    title="Section Title"
    content="Explanation of what this section does..."
    docsLink="/help#section"
  />
</div>
```

### Pattern 2: Form Field with Help

```tsx
<div className="space-y-1">
  <label htmlFor="field" className="flex items-center gap-2">
    Field Label
    <HelpIcon
      content="Brief explanation of this field"
      size="sm"
    />
  </label>
  <input id="field" type="text" placeholder="Example input..." />
  <InlineHelp>
    Additional guidance or format requirements
  </InlineHelp>
</div>
```

### Pattern 3: Feature with First-Time Hint

```tsx
const { shouldShow, dismiss } = useFirstTimeHint('feature-id');

return (
  <div className="relative">
    <FeatureComponent />
    
    {shouldShow && (
      <div className="absolute top-full mt-2 p-3 bg-primary-50 rounded-lg">
        <p className="text-sm">💡 Tip: You can do X by pressing Y</p>
        <button onClick={dismiss} className="text-xs">Got it</button>
      </div>
    )}
  </div>
);
```

## Integration Checklist

For each major feature, ensure:

- [ ] Page header has help icon (if complex feature)
- [ ] Form fields have inline help or placeholders
- [ ] Buttons have tooltips (if icon-only)
- [ ] Complex UI has help icons
- [ ] First-time users see hints
- [ ] Links to full documentation
- [ ] Error messages are helpful
- [ ] Success messages are clear
- [ ] Loading states are informative

## Resources

- [Help Center](/help) - Full documentation
- [Feature Tour](/help#tour) - Interactive walkthrough
- [Keyboard Shortcuts](/help#shortcuts) - All shortcuts
- [Video Tutorials](/help#videos) - Visual guides
