# Storybook Component Documentation Guide

This guide explains how to document components in Storybook for Career Copilot.

## Table of Contents

- [Overview](#overview)
- [Running Storybook](#running-storybook)
- [Creating Stories](#creating-stories)
- [Documentation Standards](#documentation-standards)
- [Component Migration Guide](#component-migration-guide)
- [Accessibility Testing](#accessibility-testing)
- [Best Practices](#best-practices)

## Overview

Storybook is our component development and documentation tool. It allows us to:
- Develop components in isolation
- Document component APIs and usage
- Test components visually
- Ensure accessibility compliance
- Share component library with team

## Running Storybook

```bash
# Start Storybook development server
npm run storybook

# Build Storybook for deployment
npm run build-storybook
```

Storybook will be available at `http://localhost:6006`

## Creating Stories

### Basic Story Structure

```typescript
// components/ui/Button2.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button2 } from './Button2';

const meta: Meta<typeof Button2> = {
  title: 'UI/Button2',
  component: Button2,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile button component with multiple variants and sizes.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline', 'ghost', 'danger'],
      description: 'The visual style of the button',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'primary' },
      },
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'The size of the button',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'md' },
      },
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the button is disabled',
    },
    isLoading: {
      control: 'boolean',
      description: 'Whether the button is in loading state',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button2>;

// Default story
export const Primary: Story = {
  args: {
    children: 'Button',
    variant: 'primary',
    size: 'md',
  },
};

// Variant stories
export const Secondary: Story = {
  args: {
    children: 'Button',
    variant: 'secondary',
  },
};

export const Outline: Story = {
  args: {
    children: 'Button',
    variant: 'outline',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Button',
    variant: 'ghost',
  },
};

export const Danger: Story = {
  args: {
    children: 'Delete',
    variant: 'danger',
  },
};

// Size stories
export const Small: Story = {
  args: {
    children: 'Button',
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    children: 'Button',
    size: 'lg',
  },
};

// State stories
export const Disabled: Story = {
  args: {
    children: 'Button',
    disabled: true,
  },
};

export const Loading: Story = {
  args: {
    children: 'Button',
    isLoading: true,
  },
};

// Complex example
export const WithIcon: Story = {
  args: {
    children: (
      <>
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Add Item
      </>
    ),
  },
};
```

### Advanced Story with Multiple Scenarios

```typescript
// components/ui/Card2.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Card2, CardHeader2, CardContent2, CardFooter2 } from './Card2';
import { Button2 } from './Button2';

const meta: Meta<typeof Card2> = {
  title: 'UI/Card2',
  component: Card2,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
A flexible card component with header, content, and footer sections.
Supports multiple elevation levels and interactive states.

## Usage

\`\`\`tsx
<Card2 elevation={2}>
  <CardHeader2>
    <h3>Card Title</h3>
  </CardHeader2>
  <CardContent2>
    <p>Card content goes here</p>
  </CardContent2>
  <CardFooter2>
    <Button2>Action</Button2>
  </CardFooter2>
</Card2>
\`\`\`

## Accessibility

- Uses semantic HTML elements
- Supports keyboard navigation when interactive
- Proper ARIA labels for interactive cards
        `,
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Card2>;

export const Default: Story = {
  render: () => (
    <Card2>
      <CardHeader2>
        <h3 className="text-lg font-semibold">Card Title</h3>
      </CardHeader2>
      <CardContent2>
        <p>This is the card content. It can contain any React elements.</p>
      </CardContent2>
    </Card2>
  ),
};

export const WithFooter: Story = {
  render: () => (
    <Card2>
      <CardHeader2>
        <h3 className="text-lg font-semibold">Card with Footer</h3>
      </CardHeader2>
      <CardContent2>
        <p>This card includes a footer with actions.</p>
      </CardContent2>
      <CardFooter2>
        <Button2 variant="outline" size="sm">Cancel</Button2>
        <Button2 size="sm">Save</Button2>
      </CardFooter2>
    </Card2>
  ),
};

export const Elevated: Story = {
  render: () => (
    <div className="space-y-4">
      {[1, 2, 3, 4, 5].map((level) => (
        <Card2 key={level} elevation={level as any}>
          <CardContent2>
            <p>Elevation Level {level}</p>
          </CardContent2>
        </Card2>
      ))}
    </div>
  ),
};

export const Interactive: Story = {
  render: () => (
    <Card2 interactive onClick={() => alert('Card clicked!')}>
      <CardContent2>
        <p>Click me! I'm an interactive card.</p>
      </CardContent2>
    </Card2>
  ),
};
```

## Documentation Standards

### Required Documentation

Every component story must include:

1. **Component Description**
   - What the component does
   - When to use it
   - Key features

2. **Props Table**
   - Automatically generated from TypeScript types
   - Include descriptions for each prop
   - Specify default values

3. **Usage Examples**
   - Basic usage
   - Common variations
   - Complex scenarios

4. **Accessibility Notes**
   - Keyboard navigation
   - Screen reader support
   - ARIA attributes
   - Color contrast

### Props Documentation

```typescript
argTypes: {
  variant: {
    control: 'select',
    options: ['primary', 'secondary', 'outline'],
    description: 'The visual style of the button',
    table: {
      type: { summary: 'string' },
      defaultValue: { summary: 'primary' },
      category: 'Appearance',
    },
  },
  size: {
    control: 'select',
    options: ['sm', 'md', 'lg'],
    description: 'The size of the button',
    table: {
      type: { summary: 'string' },
      defaultValue: { summary: 'md' },
      category: 'Appearance',
    },
  },
  onClick: {
    action: 'clicked',
    description: 'Callback fired when button is clicked',
    table: {
      type: { summary: '() => void' },
      category: 'Events',
    },
  },
  disabled: {
    control: 'boolean',
    description: 'Whether the button is disabled',
    table: {
      type: { summary: 'boolean' },
      defaultValue: { summary: 'false' },
      category: 'State',
    },
  },
}
```

### MDX Documentation

For complex components, use MDX for rich documentation:

```mdx
{/* components/ui/Button2.stories.mdx */}
import { Meta, Story, Canvas, ArgsTable } from '@storybook/blocks';
import { Button2 } from './Button2';

<Meta title="UI/Button2" component={Button2} />

# Button2

A versatile button component with multiple variants and sizes.

## Overview

The Button2 component is the primary interactive element in our design system.
It supports multiple visual styles, sizes, and states.

<Canvas>
  <Story name="Default">
    <Button2>Click me</Button2>
  </Story>
</Canvas>

## Variants

### Primary

Use for primary actions like "Save", "Submit", "Continue".

<Canvas>
  <Story name="Primary">
    <Button2 variant="primary">Primary Button</Button2>
  </Story>
</Canvas>

### Secondary

Use for secondary actions like "Cancel", "Back".

<Canvas>
  <Story name="Secondary">
    <Button2 variant="secondary">Secondary Button</Button2>
  </Story>
</Canvas>

## Props

<ArgsTable of={Button2} />

## Accessibility

- Supports keyboard navigation (Enter/Space to activate)
- Proper focus indicators
- Disabled state prevents interaction
- Loading state announces to screen readers

## Usage Guidelines

### Do's
- Use clear, action-oriented labels
- Provide visual feedback on interaction
- Maintain consistent button hierarchy

### Don'ts
- Don't use too many primary buttons on one page
- Don't use buttons for navigation (use links instead)
- Don't make buttons too small (minimum 44x44px for touch)
```

## Component Migration Guide

### Old Component → New Component

When migrating from old components to new design system components:

```typescript
// OLD: Button.tsx
<Button
  color="primary"
  size="medium"
  onClick={handleClick}
>
  Click me
</Button>

// NEW: Button2.tsx
<Button2
  variant="primary"  // color → variant
  size="md"          // medium → md
  onClick={handleClick}
>
  Click me
</Button2>
```

### Migration Checklist

- [ ] Create new component with "2" suffix
- [ ] Implement all variants from old component
- [ ] Create comprehensive Storybook stories
- [ ] Document props and usage
- [ ] Add accessibility notes
- [ ] Create migration guide in story
- [ ] Update components using old version
- [ ] Deprecate old component

### Migration Story Example

```typescript
export const MigrationGuide: Story = {
  parameters: {
    docs: {
      description: {
        story: `
## Migrating from Button to Button2

### Prop Changes

| Old Prop | New Prop | Notes |
|----------|----------|-------|
| \`color\` | \`variant\` | Renamed for clarity |
| \`size="medium"\` | \`size="md"\` | Shortened |
| \`loading\` | \`isLoading\` | Boolean prefix |

### Example Migration

\`\`\`tsx
// Before
<Button color="primary" size="medium" loading={true}>
  Save
</Button>

// After
<Button2 variant="primary" size="md" isLoading={true}>
  Save
</Button2>
\`\`\`

### Breaking Changes

- Removed \`fullWidth\` prop (use className="w-full" instead)
- Removed \`rounded\` prop (all buttons are rounded by default)
        `,
      },
    },
  },
  render: () => (
    <div className="space-y-4">
      <div>
        <h4 className="font-semibold mb-2">Old Button (Deprecated)</h4>
        {/* Old button example */}
      </div>
      <div>
        <h4 className="font-semibold mb-2">New Button2</h4>
        <Button2 variant="primary">Save</Button2>
      </div>
    </div>
  ),
};
```

## Accessibility Testing

Storybook includes the a11y addon for accessibility testing.

### Running Accessibility Tests

1. Open Storybook
2. Navigate to a component story
3. Click the "Accessibility" tab
4. Review violations and warnings
5. Fix issues in component code

### Common Accessibility Issues

```typescript
// ❌ Bad: Missing alt text
<img src="logo.png" />

// ✅ Good: Descriptive alt text
<img src="logo.png" alt="Company Logo" />

// ❌ Bad: Non-semantic button
<div onClick={handleClick}>Click me</div>

// ✅ Good: Semantic button
<button onClick={handleClick}>Click me</button>

// ❌ Bad: Low contrast
<button className="text-gray-400 bg-gray-300">Button</button>

// ✅ Good: Sufficient contrast
<button className="text-white bg-primary">Button</button>
```

### Accessibility Checklist

- [ ] Proper semantic HTML elements
- [ ] Keyboard navigation support
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] ARIA labels for icon-only buttons
- [ ] Screen reader announcements for dynamic content
- [ ] Form labels associated with inputs
- [ ] Error messages accessible

## Best Practices

### Story Organization

```
components/
├── ui/
│   ├── Button2.tsx
│   ├── Button2.stories.tsx
│   ├── Button2.test.tsx
│   ├── Card2.tsx
│   ├── Card2.stories.tsx
│   └── Card2.test.tsx
```

### Story Naming

```typescript
// ✅ Good: Descriptive names
export const Primary: Story = { ... };
export const WithIcon: Story = { ... };
export const LoadingState: Story = { ... };

// ❌ Bad: Generic names
export const Story1: Story = { ... };
export const Test: Story = { ... };
export const Example: Story = { ... };
```

### Story Categories

Organize stories by category:

```typescript
const meta: Meta<typeof Button2> = {
  title: 'UI/Button2',  // Category/Component
  // or
  title: 'Forms/Input2',
  // or
  title: 'Layout/Card2',
};
```

### Interactive Stories

Use actions and controls for interactive stories:

```typescript
export const Interactive: Story = {
  args: {
    onClick: () => console.log('Clicked!'),
  },
  argTypes: {
    onClick: { action: 'clicked' },
  },
};
```

### Dark Mode Support

Test components in both light and dark modes:

```typescript
export const DarkMode: Story = {
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
  decorators: [
    (Story) => (
      <div className="dark">
        <Story />
      </div>
    ),
  ],
};
```

## Additional Resources

- [Storybook Documentation](https://storybook.js.org/docs)
- [Storybook Best Practices](https://storybook.js.org/docs/react/writing-stories/introduction)
- [Accessibility Addon](https://storybook.js.org/addons/@storybook/addon-a11y)
- [Component Story Format](https://storybook.js.org/docs/react/api/csf)

---

For questions or issues, contact the development team or open a GitHub issue.
