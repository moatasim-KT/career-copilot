# Dark Mode Verification for Form Components

This document provides a manual testing checklist for verifying dark mode implementation in all form components.

## Components Updated

All form components have been updated with comprehensive dark mode support:

1. **Input2** - Text input component
2. **Select2** - Dropdown select component  
3. **MultiSelect2** - Multi-selection dropdown
4. **Textarea2** - Multi-line text input
5. **DatePicker2** - Date selection component

## Dark Mode Classes Added

### Background Colors
- `dark:bg-neutral-800` - Main input/select backgrounds
- `dark:bg-neutral-700` - Filled variant backgrounds
- `dark:bg-neutral-900/20` - Selected state backgrounds (MultiSelect2)

### Border Colors
- `dark:border-neutral-700` - Default borders
- `dark:border-neutral-600` - Hover states
- `dark:focus:border-primary-400` - Focus state borders

### Text Colors
- `dark:text-neutral-100` - Input text
- `dark:text-neutral-300` - Labels and secondary text
- `dark:text-neutral-400` - Helper text and character counts
- `dark:text-neutral-500` - Placeholder text and icons

### Focus Rings
- `dark:focus:ring-primary-400/20` - Focus ring with 20% opacity

### Interactive Elements
- `dark:hover:bg-neutral-700` - Hover states for dropdowns
- `dark:hover:bg-neutral-800` - Hover states for ghost variant
- `dark:hover:text-neutral-300` - Icon hover states

## Manual Testing Checklist

### Input2 Component

#### Default Variant
- [ ] Background is dark gray (neutral-800) in dark mode
- [ ] Border is lighter gray (neutral-700) in dark mode
- [ ] Placeholder text is muted (neutral-500) in dark mode
- [ ] Input text is light (neutral-100) in dark mode
- [ ] Focus ring is visible with primary-400 color
- [ ] Prefix/suffix icons are properly colored (neutral-500)
- [ ] Clear button hover state works in dark mode
- [ ] Loading spinner is visible in dark mode

#### Filled Variant
- [ ] Background is neutral-700 in dark mode
- [ ] Focus changes background to neutral-800
- [ ] Focus ring is visible

#### Outlined Variant
- [ ] Border is neutral-700 in dark mode
- [ ] Focus border changes to primary-400
- [ ] Background remains transparent

#### Ghost Variant
- [ ] Hover background is neutral-800
- [ ] Focus background is neutral-800

### Select2 Component

- [ ] Background is neutral-800 in dark mode
- [ ] Border is neutral-700 in dark mode
- [ ] Text is neutral-100 in dark mode
- [ ] Chevron icon is neutral-500 in dark mode
- [ ] Focus ring is visible with primary-400 color
- [ ] Prefix icon (if present) is properly colored
- [ ] Dropdown options are readable in dark mode

### MultiSelect2 Component

#### Container
- [ ] Background is neutral-800 in dark mode
- [ ] Border is neutral-700 in dark mode
- [ ] Placeholder is neutral-500 in dark mode
- [ ] Focus ring is visible with primary-400 color

#### Selected Chips
- [ ] Chip background is primary-900/30 in dark mode
- [ ] Chip text is primary-300 in dark mode
- [ ] Remove button hover state works

#### Dropdown
- [ ] Dropdown background is neutral-800 in dark mode
- [ ] Dropdown border is neutral-700 in dark mode
- [ ] Search input has proper dark mode styling
- [ ] Action buttons (Select All, Clear All) are readable
- [ ] Option hover state is neutral-700
- [ ] Selected option background is primary-900/20
- [ ] Checkboxes are properly styled
- [ ] "No options found" text is readable

### Textarea2 Component

- [ ] Background is neutral-800 in dark mode
- [ ] Border is neutral-700 in dark mode
- [ ] Placeholder is neutral-500 in dark mode
- [ ] Text is neutral-100 in dark mode
- [ ] Focus ring is visible with primary-400 color
- [ ] Character count is neutral-400 in dark mode
- [ ] All variants (default, filled, outlined) work correctly

### DatePicker2 Component

#### Input
- [ ] Background is neutral-800 in dark mode
- [ ] Border is neutral-700 in dark mode
- [ ] Placeholder is neutral-500 in dark mode
- [ ] Text is neutral-100 in dark mode
- [ ] Calendar icon is neutral-500 in dark mode
- [ ] Clear button hover state works
- [ ] Focus ring is visible with primary-400 color

#### Calendar Popup
- [ ] Calendar background is neutral-800 in dark mode
- [ ] Calendar border is neutral-700 in dark mode
- [ ] Month/year text is neutral-300 in dark mode
- [ ] Navigation buttons hover state is neutral-700
- [ ] Day of week labels are neutral-400 in dark mode
- [ ] Day numbers are neutral-300 in dark mode
- [ ] Today indicator border is primary-400
- [ ] Selected day background is primary-600
- [ ] Date range background is primary-900/30
- [ ] Hover state is primary-900/20
- [ ] Disabled dates are properly styled

### Common Elements

#### Labels
- [ ] All component labels are neutral-300 in dark mode
- [ ] Required asterisk (*) is visible

#### Error Messages
- [ ] Error text color is readable in dark mode
- [ ] Error border color is visible

#### Helper Text
- [ ] Helper text is neutral-400 in dark mode

## Testing in Browser

To test these components in dark mode:

1. Open Storybook: `npm run storybook`
2. Navigate to each form component story
3. Toggle dark mode in your browser or OS
4. Verify all checklist items above
5. Test focus states by tabbing through inputs
6. Test hover states by moving mouse over interactive elements
7. Test error states by triggering validation
8. Test disabled states

## Automated Testing

The automated tests in `FormComponents.darkmode.test.tsx` verify that:
- Dark mode classes are present in the DOM
- All variants have appropriate dark mode styling
- Icons and interactive elements have dark mode colors
- Focus rings use the correct dark mode colors

## Browser Compatibility

Dark mode classes should work in:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Android)

## Notes

- All dark mode classes use Tailwind's `dark:` prefix
- Colors follow the neutral palette (neutral-100 to neutral-900)
- Primary colors use the primary-400/500/600 range for better contrast
- Focus rings maintain 4.5:1 contrast ratio minimum
- All interactive elements have visible hover/focus states
