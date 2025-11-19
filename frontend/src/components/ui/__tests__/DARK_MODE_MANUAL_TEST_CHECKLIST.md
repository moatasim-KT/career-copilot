# Dark Mode Manual Testing Checklist

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

This document provides a comprehensive checklist for manually testing dark mode across all pages and components.

## Test Environment Setup

- [ ] Clear browser cache and localStorage
- [ ] Test in Chrome, Firefox, Safari, and Edge
- [ ] Test on desktop (1920x1080) and mobile (375x667)
- [ ] Have WebAIM Contrast Checker ready: https://webaim.org/resources/contrastchecker/

## Theme Toggle Functionality

### Basic Toggle
- [ ] Click theme toggle button in navigation
- [ ] Verify theme switches from light to dark
- [ ] Click again to verify it switches back to light
- [ ] Verify smooth transition animation (200ms)
- [ ] Verify icon changes (Sun ↔ Moon)

### Keyboard Shortcut
- [ ] Press Cmd+D (Mac) or Ctrl+D (Windows/Linux)
- [ ] Verify theme toggles
- [ ] Press again to verify it toggles back

### Persistence
- [ ] Toggle to dark mode
- [ ] Refresh the page
- [ ] Verify dark mode persists
- [ ] Check localStorage has `theme: "dark"`

### System Preference
- [ ] Set system to dark mode
- [ ] Clear localStorage
- [ ] Load application
- [ ] Verify it starts in dark mode
- [ ] Change system to light mode
- [ ] Verify application updates automatically

### Cross-tab Synchronization
- [ ] Open application in two browser tabs
- [ ] Toggle theme in tab 1
- [ ] Verify tab 2 updates automatically
- [ ] Toggle in tab 2
- [ ] Verify tab 1 updates

## Page Testing

### Dashboard Page (`/dashboard`)
- [ ] Navigate to dashboard
- [ ] Toggle to dark mode
- [ ] Verify all cards have dark backgrounds
- [ ] Verify all text is readable (good contrast)
- [ ] Verify stat cards display correctly
- [ ] Verify charts render in dark mode
- [ ] Verify loading states work in dark mode
- [ ] Check hover states on interactive elements

### Jobs Page (`/jobs`)
- [ ] Navigate to jobs page
- [ ] Toggle to dark mode
- [ ] Verify job cards have dark backgrounds
- [ ] Verify job list/table renders correctly
- [ ] Verify search input works in dark mode
- [ ] Verify filters display correctly
- [ ] Verify pagination controls are visible
- [ ] Check hover states on job cards
- [ ] Verify "Save job" button works
- [ ] Check empty state if no jobs

### Applications Page (`/applications`)
- [ ] Navigate to applications page
- [ ] Toggle to dark mode
- [ ] Verify application cards render correctly
- [ ] Verify status badges are visible
- [ ] Verify table view works in dark mode
- [ ] Verify filters and search work
- [ ] Check status dropdown styling
- [ ] Verify timeline/progress indicators
- [ ] Check hover and active states

### Recommendations Page (`/recommendations`)
- [ ] Navigate to recommendations page
- [ ] Toggle to dark mode
- [ ] Verify recommendation cards display correctly
- [ ] Verify match percentage indicators
- [ ] Verify action buttons are visible
- [ ] Check hover states
- [ ] Verify empty state if no recommendations

### Analytics Page (`/analytics`)
- [ ] Navigate to analytics page
- [ ] Toggle to dark mode
- [ ] Verify all charts render in dark mode
- [ ] Check chart colors are visible
- [ ] Verify chart tooltips work
- [ ] Verify chart legends are readable
- [ ] Check stat cards
- [ ] Verify date range picker works

## Navigation Component

### Desktop Navigation
- [ ] Toggle to dark mode
- [ ] Verify navigation bar background is dark
- [ ] Verify logo is visible
- [ ] Verify all navigation links are readable
- [ ] Verify active link highlighting works
- [ ] Hover over each link and verify hover state
- [ ] Verify theme toggle button is visible
- [ ] Check border colors

### Mobile Navigation
- [ ] Resize to mobile (< 768px)
- [ ] Toggle to dark mode
- [ ] Open hamburger menu
- [ ] Verify menu background is dark
- [ ] Verify all links are readable
- [ ] Verify active state works
- [ ] Close menu and verify backdrop
- [ ] Check theme toggle in mobile view

## Modal Components

### Modal2
- [ ] Open any modal (e.g., create job, edit application)
- [ ] Toggle to dark mode
- [ ] Verify modal background is dark
- [ ] Verify modal content is readable
- [ ] Verify close button is visible
- [ ] Verify backdrop is properly styled
- [ ] Check modal header styling
- [ ] Verify modal footer buttons
- [ ] Check focus ring on interactive elements

### Drawer2
- [ ] Open a drawer component
- [ ] Toggle to dark mode
- [ ] Verify drawer background is dark
- [ ] Verify content is readable
- [ ] Verify close button works
- [ ] Check backdrop styling
- [ ] Verify slide animation works

### Popovers/Tooltips
- [ ] Hover over elements with tooltips
- [ ] Toggle to dark mode
- [ ] Verify tooltip background is dark
- [ ] Verify tooltip text is readable
- [ ] Check tooltip arrow/pointer
- [ ] Verify positioning is correct

## Form Components

### Input2
- [ ] Toggle to dark mode
- [ ] Verify input background is dark
- [ ] Verify input text is readable
- [ ] Verify placeholder text is visible
- [ ] Focus on input and check focus ring
- [ ] Type text and verify it's readable
- [ ] Check disabled state styling
- [ ] Verify error state (red border/text)
- [ ] Check success state if applicable

### Select2
- [ ] Toggle to dark mode
- [ ] Verify select background is dark
- [ ] Click to open dropdown
- [ ] Verify dropdown background is dark
- [ ] Verify options are readable
- [ ] Hover over options and check hover state
- [ ] Select an option
- [ ] Verify selected value is readable

### MultiSelect2
- [ ] Toggle to dark mode
- [ ] Verify component background is dark
- [ ] Open dropdown
- [ ] Verify options are readable
- [ ] Select multiple options
- [ ] Verify selected tags/chips are visible
- [ ] Check remove button on tags
- [ ] Verify search input works

### Textarea2
- [ ] Toggle to dark mode
- [ ] Verify textarea background is dark
- [ ] Verify text is readable
- [ ] Focus and check focus ring
- [ ] Type multiple lines
- [ ] Verify scrollbar styling (if applicable)
- [ ] Check resize handle visibility

### DatePicker2
- [ ] Toggle to dark mode
- [ ] Click to open date picker
- [ ] Verify calendar background is dark
- [ ] Verify dates are readable
- [ ] Verify current date highlighting
- [ ] Hover over dates and check hover state
- [ ] Select a date
- [ ] Verify selected date styling

### PasswordInput2
- [ ] Toggle to dark mode
- [ ] Verify input background is dark
- [ ] Type password (verify dots/asterisks)
- [ ] Click show/hide password button
- [ ] Verify button icon is visible
- [ ] Check focus ring

## Button Components

### Button2 Variants
- [ ] Toggle to dark mode
- [ ] Verify primary button styling
- [ ] Verify secondary button styling
- [ ] Verify ghost button styling
- [ ] Verify outline button styling
- [ ] Verify destructive button styling
- [ ] Check hover states for all variants
- [ ] Check active/pressed states
- [ ] Check disabled states
- [ ] Verify loading state spinner

### Button Sizes
- [ ] Check small button in dark mode
- [ ] Check medium button in dark mode
- [ ] Check large button in dark mode
- [ ] Verify icon-only buttons

## Card Components

### Card2
- [ ] Toggle to dark mode
- [ ] Verify card background is dark
- [ ] Verify card border is visible
- [ ] Verify card content is readable
- [ ] Hover over card and check hover effect
- [ ] Check card shadow in dark mode
- [ ] Verify card header styling
- [ ] Verify card footer styling

### Card Variants
- [ ] Check default card
- [ ] Check elevated card
- [ ] Check outlined card
- [ ] Check interactive card (clickable)

## Loading States

### Spinner2
- [ ] Toggle to dark mode
- [ ] Verify spinner is visible
- [ ] Check spinner color
- [ ] Verify animation works

### Skeleton Loaders
- [ ] Toggle to dark mode
- [ ] Verify skeleton backgrounds are visible
- [ ] Check skeleton animation (shimmer)
- [ ] Verify skeleton shapes match content

### Progress Bars
- [ ] Toggle to dark mode
- [ ] Verify progress bar background
- [ ] Verify progress fill color
- [ ] Check progress percentage text

## Color Contrast Testing

Use WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

### Text Contrast (WCAG AA: 4.5:1 minimum)
- [ ] Body text on page background
- [ ] Heading text on page background
- [ ] Link text on page background
- [ ] Button text on button background
- [ ] Input text on input background
- [ ] Card text on card background
- [ ] Modal text on modal background
- [ ] Navigation text on navigation background

### Interactive Element Contrast
- [ ] Primary button text/background
- [ ] Secondary button text/background
- [ ] Link hover state
- [ ] Active navigation item
- [ ] Selected dropdown option
- [ ] Checkbox/radio checked state
- [ ] Toggle switch active state

### Status Colors
- [ ] Success text/background (green)
- [ ] Warning text/background (yellow)
- [ ] Error text/background (red)
- [ ] Info text/background (blue)

### Specific Elements to Check
1. **Dashboard Stats**
   - [ ] Stat value text
   - [ ] Stat label text
   - [ ] Stat icon color

2. **Job Cards**
   - [ ] Job title
   - [ ] Company name
   - [ ] Location text
   - [ ] Salary text
   - [ ] Tags/badges

3. **Application Cards**
   - [ ] Application title
   - [ ] Status badge
   - [ ] Date text
   - [ ] Action buttons

4. **Charts**
   - [ ] Chart labels
   - [ ] Chart values
   - [ ] Legend text
   - [ ] Tooltip text

5. **Forms**
   - [ ] Label text
   - [ ] Input text
   - [ ] Placeholder text
   - [ ] Error message text
   - [ ] Helper text

## Edge Cases

### Rapid Toggling
- [ ] Toggle theme rapidly 10 times
- [ ] Verify no visual glitches
- [ ] Verify no console errors
- [ ] Verify localStorage updates correctly

### Page Transitions
- [ ] Toggle to dark mode
- [ ] Navigate between pages
- [ ] Verify theme persists across navigation
- [ ] Check for flash of wrong theme

### Browser Refresh
- [ ] Set dark mode
- [ ] Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
- [ ] Verify no flash of light theme
- [ ] Verify dark mode loads immediately

### Nested Components
- [ ] Open modal in dark mode
- [ ] Open popover within modal
- [ ] Verify both are styled correctly
- [ ] Close and verify cleanup

### Long Content
- [ ] Load page with long scrollable content
- [ ] Toggle to dark mode
- [ ] Scroll through entire page
- [ ] Verify consistent styling throughout

## Accessibility Testing

### Keyboard Navigation
- [ ] Toggle to dark mode
- [ ] Tab through all interactive elements
- [ ] Verify focus indicators are visible
- [ ] Verify focus ring contrast meets WCAG
- [ ] Use arrow keys in dropdowns/menus
- [ ] Press Enter/Space on buttons

### Screen Reader
- [ ] Enable screen reader (VoiceOver/NVDA)
- [ ] Toggle to dark mode
- [ ] Navigate through page
- [ ] Verify theme toggle is announced
- [ ] Verify all content is readable
- [ ] Check ARIA labels are present

## Performance Testing

### Initial Load
- [ ] Clear cache
- [ ] Load page in dark mode
- [ ] Verify no flash of unstyled content
- [ ] Check Network tab for theme-related requests
- [ ] Verify theme loads before first paint

### Theme Toggle Performance
- [ ] Open DevTools Performance tab
- [ ] Record while toggling theme
- [ ] Verify transition completes in < 200ms
- [ ] Check for layout shifts
- [ ] Verify no unnecessary re-renders

## Browser-Specific Testing

### Chrome
- [ ] Test all features in Chrome
- [ ] Check DevTools for console errors
- [ ] Verify CSS custom properties work

### Firefox
- [ ] Test all features in Firefox
- [ ] Check for rendering differences
- [ ] Verify transitions work smoothly

### Safari
- [ ] Test all features in Safari
- [ ] Check for webkit-specific issues
- [ ] Verify backdrop-filter works

### Edge
- [ ] Test all features in Edge
- [ ] Verify compatibility
- [ ] Check for any edge cases (pun intended)

## Mobile Testing

### iOS Safari
- [ ] Test on iPhone (various sizes)
- [ ] Verify touch interactions work
- [ ] Check safe area insets
- [ ] Test in portrait and landscape

### Android Chrome
- [ ] Test on Android device
- [ ] Verify touch interactions
- [ ] Check for rendering issues
- [ ] Test different screen sizes

## Issues Found

Document any issues found during testing:

| Issue | Page/Component | Severity | Description | Status |
| ----- | -------------- | -------- | ----------- | ------ |
|       |                |          |             |        |

## Sign-off

- [ ] All critical issues resolved
- [ ] All pages tested in dark mode
- [ ] All components tested in dark mode
- [ ] Color contrast verified (4.5:1 minimum)
- [ ] System preference detection works
- [ ] Cross-browser testing complete
- [ ] Mobile testing complete
- [ ] Accessibility testing complete

**Tested by:** _______________  
**Date:** _______________  
**Browser versions:** _______________  
**Notes:** _______________
