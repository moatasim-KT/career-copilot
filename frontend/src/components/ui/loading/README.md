# Loading State Components

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

Comprehensive loading state components with smooth animations and transitions for the Career Copilot application.

## Overview

This collection provides a complete set of loading indicators and transitions to create a polished, professional user experience. All components feature:

- Smooth animations with custom easing curves
- Dark mode support
- Accessibility with ARIA labels
- TypeScript type safety
- Storybook documentation

## Components

### 1. Spinner2

A rotating spinner with multiple variants and smooth easing curves.

**Features:**
- Multiple sizes (xs, sm, md, lg, xl)
- Three animation variants (default, smooth, pulsing)
- Color options (primary, secondary, white, current)
- Optional label display
- Accessible with ARIA attributes

**Usage:**
```tsx
import { Spinner2 } from '@/components/ui/Spinner2';

// Basic spinner
<Spinner2 />

// Large smooth spinner with label
<Spinner2 size="lg" variant="smooth" showLabel label="Loading data..." />

// Pulsing spinner for emphasis
<Spinner2 variant="pulsing" color="primary" />
```

### 2. DotsLoader

Three-dot bouncing animation for a more subtle loading indicator.

**Features:**
- Multiple sizes (sm, md, lg)
- Color options
- Smooth bouncing animation
- Perfect for inline use

**Usage:**
```tsx
import { DotsLoader } from '@/components/ui/DotsLoader';

// Basic dots loader
<DotsLoader />

// Inline with text
<div className="flex items-center gap-2">
  <span>Loading</span>
  <DotsLoader size="sm" />
</div>
```

### 3. LoadingTransition

Smooth crossfade transition from skeleton to actual content.

**Features:**
- Prevents layout shift
- Customizable timing
- Smooth opacity transitions
- Works with any skeleton component

**Usage:**
```tsx
import { LoadingTransition } from '@/components/ui/LoadingTransition';
import { Skeleton2 } from '@/components/ui/Skeleton2';

<LoadingTransition
  loading={isLoading}
  skeleton={
    <div className="space-y-3">
      <Skeleton2 height={24} width="60%" />
      <Skeleton2 height={16} width="100%" />
    </div>
  }
>
  <div>Actual content here</div>
</LoadingTransition>
```

### 4. StaggerReveal

Sequential reveal animation for multiple items.

**Features:**
- Fast and normal speed options
- Customizable stagger delay
- Smooth fade and slide animations
- Perfect for lists and grids

**Usage:**
```tsx
import { StaggerReveal, StaggerRevealItem } from '@/components/ui/StaggerReveal';

<StaggerReveal speed="fast">
  {items.map(item => (
    <StaggerRevealItem key={item.id}>
      <Card>{item.content}</Card>
    </StaggerRevealItem>
  ))}
</StaggerReveal>
```

### 5. LoadingOverlay

Full-screen or container-relative loading overlay with backdrop blur.

**Features:**
- Full-screen or container positioning
- Multiple indicator types (spinner, dots, custom)
- Optional loading message
- Backdrop blur effect
- Customizable opacity

**Usage:**
```tsx
import { LoadingOverlay } from '@/components/ui/LoadingOverlay';

// Full-screen overlay
<LoadingOverlay visible={isLoading} message="Loading your data..." />

// Container-relative overlay
<div className="relative">
  <LoadingOverlay
    visible={isLoading}
    fullScreen={false}
    indicator="dots"
  />
  <div>Container content</div>
</div>
```

### 6. ProgressBar

Determinate and indeterminate progress indicator.

**Features:**
- Determinate progress with percentage
- Smooth indeterminate animation
- Multiple sizes and colors
- Optional percentage label
- Accessible with ARIA attributes

**Usage:**
```tsx
import { ProgressBar } from '@/components/ui/ProgressBar';

// Indeterminate progress
<ProgressBar />

// Determinate progress with label
<ProgressBar value={65} showLabel label="Upload progress" />

// Success state
<ProgressBar value={100} color="success" showLabel />
```

## Animation Variants

All loading animations use custom easing curves defined in `@/lib/animations.ts`:

### Skeleton to Content Crossfade
```typescript
skeletonToContentVariants
contentFromSkeletonVariants
```

### Stagger Reveal
```typescript
staggerRevealContainer
staggerRevealItem
fastStaggerContainer
fastStaggerItem
```

### Spinners
```typescript
spinnerVariants          // Linear rotation
smoothSpinnerVariants    // Cubic-bezier easing
pulsingSpinnerVariants   // Rotation + scale pulse
```

### Progress
```typescript
progressBarVariants      // Indeterminate animation
```

### Overlay
```typescript
loadingOverlayVariants   // Fade with backdrop blur
```

## Best Practices

### When to Use Each Component

1. **Spinner2**
   - Quick operations (< 2 seconds)
   - Unknown duration
   - Inline loading states

2. **DotsLoader**
   - Subtle loading indication
   - Inline with text
   - Button loading states

3. **LoadingTransition**
   - Content that takes time to load
   - Prevents layout shift
   - Smooth user experience

4. **StaggerReveal**
   - Lists and grids
   - Multiple items appearing
   - Visual interest on page load

5. **LoadingOverlay**
   - Long operations (> 3 seconds)
   - Blocking user interaction
   - Full-page or section loading

6. **ProgressBar**
   - Operations with known duration
   - File uploads/downloads
   - Multi-step processes

### Accessibility

All components include:
- `role="status"` for loading indicators
- `aria-label` for screen readers
- `aria-live="polite"` for overlays
- `aria-busy` for loading states
- Screen reader only text with `.sr-only`

### Performance

- Components use Framer Motion for GPU-accelerated animations
- Minimal re-renders with proper memoization
- Lazy loading for heavy components
- Optimized animation curves for 60fps

### Dark Mode

All components automatically adapt to dark mode using Tailwind's `dark:` variants:
- Skeleton backgrounds adjust opacity
- Spinner colors maintain contrast
- Overlay backgrounds blend properly

## Examples

See `LoadingStatesDemo.tsx` for a comprehensive demonstration of all components in action.

View Storybook stories for interactive examples:
- `Spinner2.stories.tsx`
- `DotsLoader.stories.tsx`
- `LoadingTransition.stories.tsx`
- `StaggerReveal.stories.tsx`
- `LoadingOverlay.stories.tsx`
- `ProgressBar.stories.tsx`

## Testing

All components are tested for:
- Rendering with different props
- Animation behavior
- Accessibility compliance
- Dark mode appearance
- Responsive behavior

Run tests:
```bash
npm test -- --testPathPattern=loading
```

## Migration from Old Components

If you're using older loading components:

```tsx
// Old
<Spinner />

// New
<Spinner2 variant="smooth" />

// Old
<LoadingSpinner />

// New
<Spinner2 size="lg" showLabel label="Loading..." />
```

## Contributing

When adding new loading states:
1. Follow the existing animation patterns
2. Add TypeScript types
3. Include Storybook stories
4. Ensure accessibility
5. Test in dark mode
6. Document usage examples
