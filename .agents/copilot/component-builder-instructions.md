# GitHub Copilot - Component Builder Instructions
**Agent**: GitHub Copilot Chat  
**Branch**: `agent/copilot/phase1-components`  
**Focus**: Building new UI components with enterprise patterns

---

## Your Mission

You are building **new production-ready components** for the Career Copilot frontend upgrade. Task 1.4 (migrations) is already complete and committed.

### Key Rules
✅ **CREATE** new component files only  
✅ **USE** design tokens from `globals.css` (already set up)  
✅ **IMPORT** Button2 and Card2 (migrations already done)  
✅ **START** immediately - no waiting needed  
❌ **NEVER** modify existing component files (already migrated)  
❌ **NEVER** touch files from Task 1.4 (already committed)

---

## Your Task Queue

✅ **Task 1.4 is complete** - Start immediately with Task 1.5!

### Task 1.5: Skeleton Loading Components
Build 5 skeleton loading components:

1. **SkeletonText.tsx** - Text loading placeholder
   - Variants: heading, paragraph, caption
   - Widths: full, 3/4, 1/2, 1/4
   - Animation: pulse, shimmer

2. **SkeletonCard.tsx** - Card loading placeholder
   - Variants: simple, withImage, withAvatar
   - Sizes: sm, md, lg, xl
   - Includes header, content, footer placeholders

3. **SkeletonAvatar.tsx** - Avatar loading placeholder
   - Shapes: circle, square, rounded
   - Sizes: xs, sm, md, lg, xl, 2xl

4. **SkeletonTable.tsx** - Table loading placeholder
   - Columns: configurable (2-10)
   - Rows: configurable (3-20)
   - Includes header row

5. **Skeleton.tsx (Enhanced)** - Base skeleton component
   - Add new variants: text, circle, rectangle, custom
   - Add className support for customization
   - Add animation controls

### Task 1.6: Input & Form Components
Build 7 enterprise-grade input components:

1. **Input.tsx** - Enhanced text input
   - Variants: default, filled, outlined, ghost
   - Sizes: sm, md, lg
   - States: disabled, error, success, loading
   - Features: prefix icon, suffix icon, clear button
   - Full TypeScript typing + ARIA

2. **Select.tsx** - Dropdown select
   - Variants: default, filled, outlined
   - Sizes: sm, md, lg
   - Features: search, multi-select, groups, custom options
   - Keyboard navigation (Arrow keys, Enter, Escape)

3. **MultiSelect.tsx** - Multi-selection dropdown
   - Chip display for selected items
   - Search/filter functionality
   - Select all / Clear all buttons
   - Max selection limit

4. **DatePicker.tsx** - Date selection component
   - Calendar view with month/year navigation
   - Range selection support
   - Min/max date constraints
   - Keyboard shortcuts (today, clear)

5. **FileUpload.tsx** - File upload component
   - Drag & drop support
   - Multiple file selection
   - File type restrictions
   - Preview thumbnails for images
   - Progress indicators

6. **PasswordInput.tsx** - Specialized password input
   - Show/hide toggle
   - Strength meter (weak, fair, strong)
   - Requirements checklist
   - Copy prevention

7. **Textarea.tsx** - Multi-line text input
   - Auto-resize option
   - Character counter
   - Max length enforcement
   - Resize handle control

### Task 1.7: Modal & Dialog System
Build 4 modal/dialog components:

1. **Modal.tsx (v2)** - Enhanced modal system
   - Sizes: sm, md, lg, xl, full
   - Variants: default, danger, success, info
   - Features: backdrop, close on escape, close on outside click
   - Animations: fade, slide, zoom
   - Portal rendering

2. **Dialog.tsx** - Confirmation dialogs
   - Types: confirm, alert, prompt
   - Preset variants: delete, save, cancel
   - Custom actions (1-3 buttons)
   - Async action support with loading states

3. **Popover.tsx** - Floating content popover
   - Placements: top, bottom, left, right (+ start/end variants)
   - Triggers: click, hover, focus
   - Arrow indicator
   - Auto-positioning (flip if overflow)

4. **Dropdown.tsx** - Dropdown menu system
   - Nested menu support
   - Dividers and sections
   - Icons and shortcuts display
   - Keyboard navigation

---

## Code Standards

### File Structure
```typescript
// 1. Imports
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// 2. Variants (using cva)
const componentVariants = cva(
  'base-classes',
  {
    variants: { /* ... */ },
    defaultVariants: { /* ... */ }
  }
);

// 3. Interface
export interface ComponentProps extends VariantProps<typeof componentVariants> {
  // props
}

// 4. Component
export const Component = React.forwardRef<HTMLElement, ComponentProps>(
  ({ className, ...props }, ref) => {
    return (/* JSX */);
  }
);

Component.displayName = 'Component';
```

### Design Token Usage
```typescript
// ✅ CORRECT - Use design tokens
className="bg-background text-foreground border-border"
className="bg-primary-600 hover:bg-primary-700"

// ❌ WRONG - No hard-coded Tailwind colors
className="bg-white text-gray-900 border-gray-200"
className="bg-blue-600 hover:bg-blue-700"
```

### Component Patterns
1. **Variants with CVA**: Use `class-variance-authority` for all variants
2. **Forward Refs**: All interactive components need `React.forwardRef`
3. **TypeScript**: Full typing with exported interfaces
4. **Accessibility**: 
   - ARIA labels/descriptions
   - Keyboard navigation
   - Focus management
   - Screen reader support
5. **Animations**: Use Framer Motion for complex animations

### Accessibility Checklist
- [ ] ARIA roles (button, menu, dialog, etc.)
- [ ] ARIA labels/descriptions for interactive elements
- [ ] Keyboard navigation (Tab, Arrow keys, Enter, Escape)
- [ ] Focus visible styles
- [ ] Screen reader announcements for dynamic content
- [ ] Color contrast meets WCAG AA (4.5:1 for text)

---

## Workflow Instructions

### Before Starting Each Component

1. **Check coordination file**:
   ```bash
   cat .agents/shared/task-assignments.json
   ```
   - Verify your status is "active"
   - Check that file isn't locked by Gemini

2. **Update task assignment**:
   ```json
   {
     "agents": {
       "copilot": {
         "status": "active",
         "current_task": "1.5.1",
         "assigned_files": ["frontend/src/components/common/SkeletonText.tsx"]
       }
     }
   }
   ```

3. **Create feature branch** (if not already on it):
   ```bash
   git checkout agent/copilot/phase1-components
   ```

### While Building Component

1. **Start with interface**:
   ```typescript
   export interface SkeletonTextProps {
     variant?: 'heading' | 'paragraph' | 'caption';
     width?: 'full' | '3/4' | '1/2' | '1/4';
     animation?: 'pulse' | 'shimmer';
     className?: string;
   }
   ```

2. **Build CVA variants**:
   ```typescript
   const skeletonTextVariants = cva(
     'animate-pulse rounded bg-neutral-200 dark:bg-neutral-700',
     {
       variants: {
         variant: {
           heading: 'h-8',
           paragraph: 'h-4',
           caption: 'h-3'
         },
         width: {
           full: 'w-full',
           '3/4': 'w-3/4',
           '1/2': 'w-1/2',
           '1/4': 'w-1/4'
         }
       },
       defaultVariants: {
         variant: 'paragraph',
         width: 'full'
       }
     }
   );
   ```

3. **Implement component**:
   - Use design tokens
   - Add accessibility features
   - Support className override
   - Export with displayName

4. **Test interactively**:
   - Test all variants
   - Test in light/dark mode
   - Test keyboard navigation
   - Test with screen reader (if applicable)

### After Completing Component

1. **Create Storybook story** (if building Storybook is your task):
   ```typescript
   // SkeletonText.stories.tsx
   import type { Meta, StoryObj } from '@storybook/react';
   import { SkeletonText } from './SkeletonText';

   const meta: Meta<typeof SkeletonText> = {
     title: 'Components/Common/SkeletonText',
     component: SkeletonText,
     tags: ['autodocs'],
   };

   export default meta;
   type Story = StoryObj<typeof SkeletonText>;

   export const Default: Story = {
     args: {},
   };

   export const Heading: Story = {
     args: {
       variant: 'heading',
     },
   };
   ```

2. **Update coordination file**:
   ```json
   {
     "agents": {
       "copilot": {
         "completed_tasks": ["1.5.1"],
         "assigned_files": []
       }
     }
   }
   ```

3. **Commit with conventional format**:
   ```bash
   git add .
   git commit -m "feat(skeleton): add SkeletonText component with variants"
   ```

4. **Move to next task**:
   - Update `current_task` in coordination file
   - Start next component

---

## Common Pitfalls to Avoid

### ❌ Don't Modify Existing Files
```typescript
// WRONG - Don't touch existing components
// frontend/src/components/layout/Navigation.tsx
- import { Button } from '@/components/ui/Button';
+ import { Button2 } from '@/components/ui/Button2';
```
**Why**: Gemini CLI handles all migrations. Modifying existing files will cause conflicts.

### ❌ Don't Use Old Components
```typescript
// WRONG - Don't import old Button
import { Button } from '@/components/ui/Button';

// CORRECT - Use new Button2
import { Button2 } from '@/components/ui/Button2';
```

### ❌ Don't Hard-Code Colors
```typescript
// WRONG
className="bg-white text-gray-900 border-gray-200"

// CORRECT
className="bg-background text-foreground border-border"
```

### ❌ Don't Skip Accessibility
```typescript
// WRONG - Missing ARIA
<button onClick={handleClose}>×</button>

// CORRECT - Full accessibility
<button 
  onClick={handleClose}
  aria-label="Close modal"
  className="hover:bg-neutral-100"
>
  <X className="h-4 w-4" />
</button>
```

---

## Example: Complete Component Template

```typescript
// frontend/src/components/ui/Input.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const inputVariants = cva(
  'flex w-full rounded-md border transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'border-border bg-background hover:border-neutral-400',
        filled: 'border-transparent bg-neutral-100 dark:bg-neutral-800',
        outlined: 'border-2 border-primary-300 bg-transparent',
        ghost: 'border-transparent bg-transparent hover:bg-neutral-50'
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-5 text-lg'
      },
      state: {
        default: '',
        error: 'border-error-500 focus-visible:ring-error-500',
        success: 'border-success-500 focus-visible:ring-success-500'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      state: 'default'
    }
  }
);

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, size, state, label, error, helperText, ...props }, ref) => {
    const finalState = error ? 'error' : state;

    return (
      <div className="w-full">
        {label && (
          <label className="mb-2 block text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <input
          className={cn(inputVariants({ variant, size, state: finalState }), className)}
          ref={ref}
          aria-invalid={!!error}
          aria-describedby={error ? 'input-error' : helperText ? 'input-helper' : undefined}
          {...props}
        />
        {error && (
          <p id="input-error" className="mt-1 text-sm text-error-600" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id="input-helper" className="mt-1 text-sm text-neutral-600">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

---

## Resources

### Design Token Reference
See `frontend/src/app/globals.css`:
- Colors: `--primary-50` through `--primary-950`, `--neutral-*`, `--semantic-*`
- Spacing: `--spacing-xs` (4px) through `--spacing-6xl` (96px)
- Typography: `--text-xs` through `--text-7xl`
- Shadows: `--shadow-xs` through `--shadow-2xl`
- Transitions: `--transition-fast`, `--transition-base`, `--transition-slow`

### Existing Components to Reference
- `Button2.tsx` - Example of enterprise button with 7 variants
- `Card2.tsx` - Example of card with elevation system
- Design system demo: `/design-system-demo`

### Dependencies
```json
{
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.0.0",
  "framer-motion": "^12.23.0",
  "lucide-react": "^0.263.1"
}
```

---

## Questions? Check These First

1. **"Can I modify Navigation.tsx?"** → No, that's Gemini's Task 1.4.2
2. **"Can I create a new Navbar.tsx?"** → Yes! New files are your domain
3. **"Which button should I import?"** → Always `Button2` from `@/components/ui/Button2`
4. **"Can I use `bg-gray-50`?"** → No, use `bg-neutral-50` (design token)
5. **"Do I need ARIA labels?"** → Yes, all interactive components need accessibility

---

## Status Reporting

Update `task-assignments.json` after each component:

```json
{
  "last_updated": "2025-11-08T15:30:00Z",
  "agents": {
    "copilot": {
      "status": "active",
      "current_task": "1.5.2",
      "completed_tasks": ["1.5.1"],
      "assigned_files": ["frontend/src/components/common/SkeletonCard.tsx"],
      "notes": "SkeletonText complete, starting SkeletonCard"
    }
  }
}
```

---

**Ready to build NOW!** Task 1.4 is complete. Start with Task 1.5.1 (SkeletonText). 🚀

## Quick Start Checklist

- [x] Task 1.4 complete (all migrations done)
- [x] Design tokens ready in globals.css
- [x] Button2 and Card2 available
- [x] Git branch created: agent/copilot/phase1-components
- [ ] **YOU ARE HERE** → Checkout branch and start building!

```bash
git checkout agent/copilot/phase1-components
# Start building SkeletonText.tsx
```
