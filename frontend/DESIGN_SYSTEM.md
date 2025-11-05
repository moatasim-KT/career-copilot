# Career Copilot Design System

This document outlines the design system for the Career Copilot frontend application.

## Color Palette

### Light Theme

| Variable | Color | Usage |
|----------|-------|-------|
| `--background` | `#ffffff` | Main background color |
| `--foreground` | `#171717` | Main text color |
| `--primary` | `#2563eb` | Primary brand color (blue) |
| `--primary-foreground` | `#ffffff` | Text on primary background |
| `--secondary` | `#f1f5f9` | Secondary background color |
| `--secondary-foreground` | `#0f172a` | Text on secondary background |
| `--muted` | `#f8fafc` | Muted background color |
| `--muted-foreground` | `#64748b` | Muted text color |
| `--accent` | `#f1f5f9` | Accent color |
| `--accent-foreground` | `#0f172a` | Text on accent background |
| `--destructive` | `#ef4444` | Error/destructive color (red) |
| `--destructive-foreground` | `#ffffff` | Text on destructive background |
| `--border` | `#e2e8f0` | Border color |
| `--input` | `#e2e8f0` | Input border color |
| `--ring` | `#2563eb` | Focus ring color |
| `--success` | `#10b981` | Success color (green) |
| `--warning` | `#f59e0b` | Warning color (orange) |
| `--info` | `#3b82f6` | Info color (blue) |

### Dark Theme

| Variable | Color | Usage |
|----------|-------|-------|
| `--background` | `#0a0a0a` | Main background color |
| `--foreground` | `#ededed` | Main text color |
| `--primary` | `#3b82f6` | Primary brand color (blue) |
| `--primary-foreground` | `#ffffff` | Text on primary background |
| `--secondary` | `#1e293b` | Secondary background color |
| `--secondary-foreground` | `#f8fafc` | Text on secondary background |
| `--muted` | `#1e293b` | Muted background color |
| `--muted-foreground` | `#94a3b8` | Muted text color |
| `--accent` | `#1e293b` | Accent color |
| `--accent-foreground` | `#f8fafc` | Text on accent background |
| `--destructive` | `#ef4444` | Error/destructive color (red) |
| `--destructive-foreground` | `#ffffff` | Text on destructive background |
| `--border` | `#334155` | Border color |
| `--input` | `#334155` | Input border color |
| `--ring` | `#3b82f6` | Focus ring color |
| `--success` | `#10b981` | Success color (green) |
| `--warning` | `#f59e0b` | Warning color (orange) |
| `--info` | `#3b82f6` | Info color (blue) |

## Typography

We use the system font stack for optimal performance and native appearance:

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Font Sizes

| Class | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `text-xs` | 0.75rem (12px) | 1rem | Small labels, captions |
| `text-sm` | 0.875rem (14px) | 1.25rem | Body text, form inputs |
| `text-base` | 1rem (16px) | 1.5rem | Default body text |
| `text-lg` | 1.125rem (18px) | 1.75rem | Large body text, subheadings |
| `text-xl` | 1.25rem (20px) | 1.75rem | Section headings |
| `text-2xl` | 1.5rem (24px) | 2rem | Page headings |
| `text-3xl` | 1.875rem (30px) | 2.25rem | Large headings |
| `text-4xl` | 2.25rem (36px) | 2.5rem | Display headings |

### Font Weights

| Class | Weight | Usage |
|-------|--------|-------|
| `font-normal` | 400 | Default body text |
| `font-medium` | 500 | Emphasized text, labels |
| `font-semibold` | 600 | Subheadings, buttons |
| `font-bold` | 700 | Headings, important text |

## Spacing

We use a consistent spacing scale based on 0.25rem (4px) increments:

| Class | Size | Pixels | Usage |
|-------|------|--------|-------|
| `p-1` / `m-1` | 0.25rem | 4px | Minimal spacing |
| `p-2` / `m-2` | 0.5rem | 8px | Tight spacing |
| `p-3` / `m-3` | 0.75rem | 12px | Comfortable spacing |
| `p-4` / `m-4` | 1rem | 16px | Default spacing |
| `p-6` / `m-6` | 1.5rem | 24px | Generous spacing |
| `p-8` / `m-8` | 2rem | 32px | Large spacing |
| `p-12` / `m-12` | 3rem | 48px | Extra large spacing |

## Border Radius

| Class | Size | Usage |
|-------|------|-------|
| `rounded-sm` | 0.125rem (2px) | Subtle roundness |
| `rounded` | 0.25rem (4px) | Default border radius |
| `rounded-md` | 0.375rem (6px) | Moderate roundness |
| `rounded-lg` | 0.5rem (8px) | Large roundness for cards |
| `rounded-xl` | 0.75rem (12px) | Extra large roundness |
| `rounded-full` | 9999px | Circular elements |

## Shadows

| Class | Shadow | Usage |
|-------|--------|-------|
| `shadow-sm` | 0 1px 2px rgba(0, 0, 0, 0.05) | Subtle depth |
| `shadow` | 0 1px 3px rgba(0, 0, 0, 0.1) | Default shadow |
| `shadow-md` | 0 4px 6px rgba(0, 0, 0, 0.1) | Moderate elevation |
| `shadow-lg` | 0 10px 15px rgba(0, 0, 0, 0.1) | High elevation |
| `shadow-xl` | 0 20px 25px rgba(0, 0, 0, 0.1) | Extra high elevation |

## Components

### Button

Buttons come in 5 variants and 3 sizes:

**Variants:**
- `primary`: Main action buttons (blue background)
- `secondary`: Secondary actions (gray background)
- `outline`: Bordered buttons (transparent background)
- `ghost`: Minimal buttons (no background)
- `destructive`: Dangerous actions (red background)

**Sizes:**
- `sm`: Small buttons (px-3 py-1.5 text-sm)
- `md`: Medium buttons (px-4 py-2 text-sm)
- `lg`: Large buttons (px-6 py-3 text-base)

### Card

Cards provide content containers with optional hover effects:

**Padding:**
- `sm`: 1rem (16px)
- `md`: 1.5rem (24px)
- `lg`: 2rem (32px)

**Components:**
- `Card`: Main container
- `CardHeader`: Header section
- `CardTitle`: Title text
- `CardContent`: Main content area

### Input

Form inputs with label, error, and helper text support:

**States:**
- Default
- Focus (blue border and ring)
- Error (red border and error message)
- Disabled (gray background)

### Select

Dropdown select with custom styling:

**Features:**
- Custom chevron icon
- Label support
- Error state
- Helper text

### Modal

Dialog overlays with multiple sizes:

**Sizes:**
- `sm`: max-w-md (28rem / 448px)
- `md`: max-w-lg (32rem / 512px)
- `lg`: max-w-2xl (42rem / 672px)
- `xl`: max-w-4xl (56rem / 896px)

## Accessibility

All components follow WCAG 2.1 AA guidelines:

- Color contrast ratio of at least 4.5:1 for normal text
- Color contrast ratio of at least 3:1 for large text
- Focus indicators on interactive elements
- Keyboard navigation support
- ARIA attributes where applicable
- Semantic HTML elements

## Animation Guidelines

Use subtle, purposeful animations:

- **Duration**: 150ms-300ms for most transitions
- **Easing**: Use ease-in-out for smooth transitions
- **Properties**: Focus on opacity, transform, and color changes
- **Respect**: Honor `prefers-reduced-motion` settings

## Best Practices

1. **Consistency**: Use design tokens (CSS variables) instead of hardcoded values
2. **Accessibility**: Test with keyboard navigation and screen readers
3. **Responsive**: Design mobile-first, enhance for larger screens
4. **Performance**: Use CSS over JavaScript for animations when possible
5. **Dark Mode**: Test all components in both light and dark themes
6. **Component Composition**: Build complex UIs from simple, reusable components

## Storybook

View all components in Storybook:

```bash
npm run storybook
```

This will start Storybook on http://localhost:6006 where you can:
- Browse all components
- View different states and variants
- Test accessibility
- Copy code examples
- Check responsive behavior
