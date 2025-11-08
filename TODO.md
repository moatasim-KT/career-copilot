

---

## Phase 1: Design System Foundation (Week 1-2)

### ✅ Task 1.1: Design Token System [COMPLETE]
- [x] Update `frontend/src/app/globals.css` with comprehensive design token system
- [x] Update `frontend/tailwind.config.ts` to use the new design tokens
- [x] Create test page at `frontend/src/app/design-system/page.tsx`
- [x] Verify all color palettes (primary, neutral, semantic)
- [x] Verify spacing, typography, shadows, transitions, z-index scales

### ✅ Task 1.2: Core Components (Button2, Card2) [COMPLETE]
- [x] Create enhanced Button component at `frontend/src/components/ui/Button2.tsx`
  - 7 variants, 5 sizes, loading states, icon positioning, animations
- [x] Create enhanced Card component at `frontend/src/components/ui/Card2.tsx`
  - 5 elevation levels, padding options, hover effects, gradient support
- [x] Add components to design-system test page

### ✅ Task 1.3: Install Dependencies [COMPLETE]
- [x] Install @tanstack/react-table, cmdk, react-hook-form, @hookform/resolvers, @formkit/auto-animate
- [x] Verify dependencies in `frontend/package.json`

---

### ✅ Task 1.4: Migrate Existing Components [COMPLETE]

**Priority: URGENT** - The design system exists but isn't being used in the application yet.

#### 1.4.1: Update Component Imports (15 files)
- [x] `frontend/src/components/pages/AdvancedFeaturesPage.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/pages/RecommendationsPage.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/pages/JobsPage.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/pages/ApplicationsPage.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/common/WebSocketTest.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/common/ResponsiveDemo.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/recommendations/SmartRecommendations.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/social/SocialFeatures.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/features/ContentGeneration.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/features/ResumeUpload.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/features/InterviewPractice.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/ui/Modal.stories.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/ui/Tooltip.stories.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/ui/EmptyState.stories.tsx` - Change `Button` → `Button2`
- [x] `frontend/src/components/ui/Button.stories.tsx` - Update to use `Button2`

#### 1.4.2: Migrate Navigation Component
- [x] `frontend/src/components/layout/Navigation.tsx`
  - Replace `bg-white` → `bg-background`
  - Replace `border-gray-200` → `border-border`
  - Replace `text-gray-900` → `text-foreground`
  - Replace `text-blue-600` → `text-primary-600`
  - Replace `hover:bg-gray-50` → `hover:bg-neutral-50`
  - Test navigation in light/dark mode

#### 1.4.3: Migrate JobTableView Component
- [x] `frontend/src/components/pages/JobTableView.tsx`
  - [x] Replace `bg-gray-50` → `bg-neutral-50` (20+ instances)
  - [x] Replace `text-gray-500` → `text-neutral-500`
  - [x] Replace `text-gray-900` → `text-neutral-900`
  - [x] Replace `hover:bg-gray-50` → `hover:bg-neutral-50`
  - [x] Test table rendering and interactions

#### 1.4.4: Migrate ErrorBoundary Component
- [x] `frontend/src/components/ErrorBoundary.tsx`
  - Replace `text-gray-900` → `text-foreground`
  - Replace `text-gray-600` → `text-neutral-600`
  - Test error state display

#### 1.4.5: Migrate NotificationSystem Component
- [x] `frontend/src/components/notifications/NotificationSystem.tsx`
  - Replace `text-gray-900` → `text-foreground`
  - Replace `text-gray-600` → `text-neutral-600`
  - Replace `text-gray-400` → `text-neutral-400`
  - Replace `text-gray-500` → `text-neutral-500`
  - Test notification display

#### 1.4.6: Comprehensive Migration Sweep
- [x] Run grep search for all remaining `bg-gray-*` patterns
- [x] Run grep search for all remaining `text-gray-*` patterns
- [x] Replace hard-coded blue colors with `primary-*` tokens
- [x] Replace hard-coded red colors with `error-*` tokens
- [x] Replace hard-coded green colors with `success-*` tokens
- [x] Visual regression test entire application

---

### ✅ Task 1.5: Enhanced Loading Skeletons [COMPLETE]

#### 1.5.1: Upgrade Base Skeleton Component
- [x] Update `frontend/src/components/ui/Skeleton2.tsx` (enterprise version)
  - Replaced `bg-gray-200` → `bg-neutral-200`
  - Added dark mode support with `dark:bg-neutral-700`
  - Added animation speed variants (fast, normal, slow)
  - Exported as default and named export

#### 1.5.2: Create Skeleton Variants
- [x] Created `frontend/src/components/ui/SkeletonText2.tsx` (single/multi-line, width variants)
- [x] Created `frontend/src/components/ui/SkeletonCard2.tsx` (header + content layout)
- [x] Created `frontend/src/components/ui/SkeletonAvatar2.tsx` (circle/square, sizes)
- [x] Created `frontend/src/components/ui/SkeletonTable2.tsx` (rows/columns config)

#### 1.5.3: Integrate Skeletons into Loading States
- [x] All skeleton variants available for integration (see new files in `ui/`)

---

### ✅ Task 1.6: Input Component Suite [COMPLETE]

#### 1.6.1: Text Input Component
- [x] Created `frontend/src/components/ui/Input2.tsx` (label, placeholder, helper, error, disabled, sizes, icons, counter)

#### 1.6.2: Select/Dropdown Component
- [x] Created `frontend/src/components/ui/Select2.tsx` (single select, search, keyboard nav, portal, loading, error, custom options)

#### 1.6.3: Multi-Select Component
- [x] Created `frontend/src/components/ui/MultiSelect2.tsx` (chip display, search, select all, max limit, clear all)

#### 1.6.4: Date Picker Component
- [x] Created `frontend/src/components/ui/DatePicker2.tsx` (single/range, min/max, disabled, formatting, keyboard nav)

#### 1.6.5: File Upload Component
- [x] Created `frontend/src/components/ui/FileUpload2.tsx` (drag/drop, type/size validation, multi-file, preview, progress, remove)

#### 1.6.6: Password Input Component
- [x] Created `frontend/src/components/ui/PasswordInput2.tsx` (show/hide, strength, checklist, copy-paste prevention)

#### 1.6.7: Textarea Component
- [x] Created `frontend/src/components/ui/Textarea2.tsx` (auto-resize, counter, min/max height, error)

---

### ✅ Task 1.7: Modal & Dialog System [COMPLETE]

#### 1.7.1: Modal Component
- [x] Created `frontend/src/components/ui/Modal2.tsx` (backdrop, focus trap, ESC, click outside, sizes, animation)

#### 1.7.2: Dialog Component
- [x] Created `frontend/src/components/ui/Dialog2.tsx` (title, message, confirm/cancel, destructive)

#### 1.7.3: Drawer Component
- [x] Created `frontend/src/components/ui/Drawer2.tsx` (slide from edges, sheet overlay)

#### 1.7.4: AlertDialog Component
- [x] Created `frontend/src/components/ui/AlertDialog2.tsx` (variants, dismissible, icon, actions)

#### 1.7.5: All Modal/Dialog Variants
- [x] All modal/dialog variants available for integration (see new files in `ui/`)

#### 1.7.6: Enterprise Modal/Dialog Suite
- [x] All enterprise modal/dialog components complete and production-ready

---

### ✅ Task 1.8: Modal/Dialog System [COMPLETE]

#### 1.8.1: Base Modal Component
- [x] Created `frontend/src/components/ui/Modal.tsx` (backdrop, focus trap, ESC, click outside, sizes, animation)
- [x] Added to design-system test page

#### 1.8.2: Modal Variants
- [x] Created `frontend/src/components/ui/ConfirmDialog.tsx` (title, message, confirm/cancel, destructive)
- [x] Created `frontend/src/components/ui/Drawer.tsx` (slide from edges, sheet overlay)
- [x] Added to design-system test page

#### 1.8.3: Popover Component
- [x] Created `frontend/src/components/ui/Popover.tsx` (positioning, arrow, click/hover, portal)
- [x] Added to design-system test page

#### 1.8.4: Tooltip Component
- [x] Enhanced `frontend/src/components/ui/Tooltip.tsx` (design tokens, arrow, delay, max width)
- [x] Updated Tooltip.stories.tsx

---

### ✅ Task 1.9: Form Validation & Patterns [COMPLETE]

#### 1.9.1: Form Component with react-hook-form
- [x] Created `frontend/src/components/ui/Form.tsx` (integration, wrappers, error display)
- [x] Created example form in design-system test page

#### 1.9.2: Validation Schemas
- [x] Created `frontend/src/lib/validation.ts` (Zod schemas: email, password, phone, URL, profile)
- [x] Documented validation patterns

#### 1.9.3: Form Examples
- [x] Created login, registration, profile edit, and job application form examples

---

### ❌ Task 1.10: Storybook Documentation [NOT STARTED]

#### 1.10.1: Setup Storybook
- [ ] Verify Storybook installation (already in package.json)
- [ ] Run `npm run storybook` to test
- [ ] Configure Storybook with Tailwind and design tokens
- [ ] Set up dark mode toggle in Storybook

#### 1.10.2: Create Component Stories
- [ ] Button2.stories.tsx - All variants, sizes, states
- [ ] Card2.stories.tsx - All elevations, interactions
- [ ] Input.stories.tsx - All states and configurations
- [ ] Select.stories.tsx - Single and multi-select examples
- [ ] Modal.stories.tsx - All modal types
- [ ] Form.stories.tsx - Complete form examples

#### 1.10.3: Design Token Documentation
- [ ] Create color palette showcase
- [ ] Create typography scale showcase
- [ ] Create spacing scale showcase
- [ ] Create shadow system showcase
- [ ] Create animation/transition examples

---

### ❌ Task 1.11: Accessibility Audit [NOT STARTED]

#### 1.11.1: Automated Testing
- [ ] Install @axe-core/react
- [ ] Run accessibility audit on all components
- [ ] Fix color contrast issues (WCAG 2.1 AA minimum 4.5:1)
- [ ] Document audit results

#### 1.11.2: Keyboard Navigation
- [ ] Test all interactive elements with Tab/Shift+Tab
- [ ] Verify focus indicators are visible
- [ ] Test modal/dialog focus trapping
- [ ] Test dropdown/select keyboard controls
- [ ] Test form submission with Enter key

#### 1.11.3: Screen Reader Testing
- [ ] Add ARIA labels to all interactive elements
- [ ] Test with VoiceOver (macOS) or NVDA (Windows)
- [ ] Verify heading hierarchy (h1 → h2 → h3)
- [ ] Add alt text to all images
- [ ] Test form field announcements

#### 1.11.4: ARIA Patterns
- [ ] Implement ARIA for custom dropdowns
- [ ] Implement ARIA for modals/dialogs
- [ ] Implement ARIA for tabs
- [ ] Implement ARIA for accordions
- [ ] Document ARIA usage patterns

---

## Phase 2: Visual Polish & Modern Design (Week 3-4)

### Task 2.1: Animations & Micro-interactions

#### 2.1.1: Animation Library Setup
- [ ] Create `frontend/src/lib/animations.ts`
  - Export Framer Motion variants for: fade, slide, scale, rotate
  - Page transition variants (fadeIn, slideIn from edges)
  - Stagger container and item variants
  - Spring configurations (gentle, bouncy, stiff)
  - Duration constants (fast: 150ms, normal: 200ms, slow: 300ms)
  
#### 2.1.2: Page Transitions
- [ ] Add page transition wrapper to `frontend/src/app/layout.tsx`
  - Fade in/out on route change
  - Use `AnimatePresence` from Framer Motion
  - Add loading indicator during transition
  - Test all route transitions

#### 2.1.3: Button Micro-interactions
- [ ] Update `frontend/src/components/ui/Button2.tsx`
  - Add whileHover scale: 1.02 (already has 1.02, verify)
  - Add whileTap scale: 0.98 (already has 0.98, verify)
  - Add ripple effect on click (optional)
  - Add success state animation (checkmark bounce)
  - Test all variants

#### 2.1.4: Card Animations
- [ ] Update `frontend/src/components/ui/Card2.tsx`
  - Add hover lift animation (already has, verify)
  - Add entrance animation when scrolling into view
  - Add stagger animation for card grids
  - Test with Dashboard cards

#### 2.1.5: List & Grid Animations
- [ ] Update `frontend/src/components/pages/JobsPage.tsx`
  - Add stagger animation for job list items
  - Animate items when filtering/sorting changes
  - Add exit animations when removing items
- [ ] Update `frontend/src/components/pages/ApplicationsPage.tsx`
  - Add stagger animation for application cards
  - Animate status changes with color transitions
- [ ] Update `frontend/src/components/pages/Dashboard.tsx`
  - Stagger animate dashboard widgets on load

#### 2.1.6: Form Animations
- [ ] Add focus animations to all input components
  - Border color transition
  - Label slide up animation
  - Error message slide down with shake
- [ ] Add form submission animations
  - Button loading spinner
  - Success checkmark animation
  - Error shake animation

#### 2.1.7: Modal & Dialog Animations
- [ ] Update modal entrance/exit animations
  - Backdrop fade in/out
  - Content scale + fade in from center
  - Slide in from bottom on mobile
- [ ] Add drawer slide animations (left, right, top, bottom)

#### 2.1.8: Loading State Transitions
- [ ] Animate skeleton → content transition
  - Crossfade effect
  - Stagger reveal for multiple items
- [ ] Add progress indicators with smooth animations
- [ ] Spinner with easing curves

---

### Task 2.2: Complete Dark Mode Implementation

#### 2.2.1: Dark Mode Color Audit
- [ ] Audit all component files for hard-coded colors
  - Search for hex colors (#000000, #FFFFFF, etc.)
  - Search for rgb() values
  - List all files needing updates
- [ ] Create dark mode color checklist spreadsheet

#### 2.2.2: Component Dark Mode Updates
- [ ] Update `frontend/src/components/layout/Navigation.tsx`
  - Background: `dark:bg-neutral-900`
  - Border: `dark:border-neutral-800`
  - Text: `dark:text-neutral-100`
  - Active states in dark mode
- [ ] Update `frontend/src/components/pages/Dashboard.tsx`
  - Card backgrounds: `dark:bg-neutral-800`
  - Stat cards with proper dark contrast
  - Chart colors for dark theme
- [ ] Update all form components
  - Input backgrounds: `dark:bg-neutral-800`
  - Input borders: `dark:border-neutral-700`
  - Placeholder text: `dark:placeholder-neutral-500`
  - Focus rings in dark mode
- [ ] Update all button variants (verify Button2 dark support)
- [ ] Update all card variants (verify Card2 dark support)
- [ ] Update table components
  - Header: `dark:bg-neutral-800`
  - Rows: `dark:hover:bg-neutral-700`
  - Borders: `dark:border-neutral-700`

#### 2.2.3: Dark Mode Toggle Component
- [ ] Create `frontend/src/components/ui/ThemeToggle.tsx`
  - Sun/Moon icons (lucide-react)
  - Smooth icon transition animation
  - Accessible button with ARIA label
  - Keyboard support
  - Tooltip: "Toggle theme (⌘/Ctrl + D)"
- [ ] Add ThemeToggle to Navigation header (top-right)
- [ ] Style toggle button for both themes

#### 2.2.4: Dark Mode Persistence & Logic
- [ ] Create `frontend/src/hooks/useDarkMode.ts`
  - Read from localStorage ('theme' key)
  - Read from system preference (prefers-color-scheme)
  - Priority: localStorage > system > default (light)
  - Return: { isDark, toggle, setDark, setLight }
- [ ] Update `frontend/src/app/layout.tsx`
  - Add `suppressHydrationWarning` to `<html>` tag
  - Add script to prevent flash of wrong theme (in <head>)
  - Apply `dark` class to `<html>` element based on preference
- [ ] Test theme persistence across page reloads

#### 2.2.5: Dark Mode Transitions
- [ ] Add CSS transition for theme switching
  - In globals.css: `* { transition: background-color 200ms, border-color 200ms, color 200ms; }`
  - Exclude: animations, transforms, opacity (keep instant)
- [ ] Test smooth transition when toggling

#### 2.2.6: Image Handling in Dark Mode
- [ ] Identify images that need dark variants
- [ ] Add `dark:invert` or `dark:opacity-80` to logos if needed
- [ ] Ensure charts have dark-friendly colors

#### 2.2.7: Dark Mode Testing
- [ ] Test all pages in dark mode
  - Dashboard, Jobs, Applications, Recommendations, Analytics
- [ ] Test all modals and popovers in dark mode
- [ ] Test forms and inputs in dark mode
- [ ] Test color contrast with WebAIM Contrast Checker
- [ ] Fix any readability issues (contrast < 4.5:1)
- [ ] Test automatic theme switching based on system preference

---

### Task 2.3: Gradient & Visual Enhancements

#### 2.3.1: Hero Section Gradients
- [ ] Update dashboard hero/header section
  - Add mesh gradient background (use `.gradient-mesh` utility from globals.css)
  - Add subtle animated gradient (optional)
  - Ensure text contrast on gradient
- [ ] Update empty states with subtle gradients
- [ ] Add gradient to onboarding wizard backgrounds

#### 2.3.2: Mesh Gradient Utility
- [ ] Verify `.gradient-mesh` class in globals.css (already exists)
- [ ] Create variations: `gradient-mesh-blue`, `gradient-mesh-purple`, `gradient-mesh-green`
- [ ] Document in Storybook design tokens

#### 2.3.3: Glass Morphism Effects
- [ ] Verify `.glass` utility class in globals.css (already exists)
- [ ] Apply glass effect to:
  - Modal backdrops
  - Popover backgrounds
  - Floating action buttons
  - Sticky navigation (when scrolled)
- [ ] Test glass effect on various backgrounds
- [ ] Ensure readability with backdrop-blur

#### 2.3.4: Card Enhancement
- [ ] Add hover shadow transitions to cards
  - Smooth shadow expansion on hover
  - Lift effect (already in Card2, verify)
  - Glow effect for featured/premium cards
- [ ] Add gradient borders option to Card component
  - `gradientBorder` prop
  - Use `before` pseudo-element with gradient
- [ ] Add shine/shimmer effect for featured cards (optional)

#### 2.3.5: Button Glow Effects
- [ ] Add glow effect to primary CTAs
  - Box-shadow with primary color at low opacity
  - Increase glow on hover
  - Animate glow pulse for critical actions (e.g., "Apply Now")
- [ ] Add gradient buttons variant
  - `gradient-primary` class from globals.css
  - Ensure text contrast

#### 2.3.6: Background Patterns for Empty States
- [ ] Create SVG pattern library in `frontend/public/patterns/`
  - Dot grid pattern
  - Line pattern
  - Wave pattern
- [ ] Apply subtle patterns to empty state components
  - "No jobs found" state
  - "No applications yet" state
  - Low opacity (5-10%) for subtlety

#### 2.3.7: Accent Colors & Highlights
- [ ] Add accent color highlights to active navigation items
  - Left border or bottom border with primary color
  - Smooth transition
- [ ] Add colored status indicators
  - Success: green dot with glow
  - Warning: yellow/orange dot with glow
  - Error: red dot with glow
  - Animate pulse effect

---

### Task 2.4: Responsive Design Refinement

#### 2.4.1: Mobile Audit (320px - 480px)
- [ ] Test on iPhone SE (375x667)
- [ ] Test on small Android (360x640)
- [ ] Navigation issues:
  - Hamburger menu functionality
  - Logo size on small screens
  - Menu item spacing
- [ ] Dashboard layout:
  - Stack cards vertically
  - Reduce padding on small screens
  - Font sizes appropriate for mobile
- [ ] Job list/cards:
  - Full-width cards on mobile
  - Reduce content density
  - Ensure tap targets are 44x44px minimum
- [ ] Forms:
  - Stack form fields vertically
  - Full-width inputs
  - Larger input heights for touch (min 44px)
  - Proper input types (email, tel, number) for mobile keyboards

#### 2.4.2: Tablet Audit (768px - 1024px)
- [ ] Test on iPad (768x1024)
- [ ] Test on iPad Pro (1024x1366)
- [ ] Navigation:
  - Show full navigation (not mobile menu)
  - Adjust spacing for tablet width
- [ ] Dashboard:
  - 2-column grid for cards
  - Optimize spacing
- [ ] Tables:
  - Show all columns or horizontal scroll
  - Adjust column widths
- [ ] Forms:
  - Consider 2-column layout for wider forms

#### 2.4.3: Mobile Navigation Enhancements
- [ ] Update `frontend/src/components/layout/Navigation.tsx`
  - Improve hamburger menu animation (slide in from right)
  - Add backdrop overlay when menu open
  - Close menu on navigation
  - Smooth open/close transitions
  - Add close button (X) in mobile menu
- [ ] Test menu on all mobile breakpoints

#### 2.4.4: Table Responsive Behavior
- [ ] Update `frontend/src/components/pages/JobTableView.tsx`
  - Add horizontal scroll for tables on mobile
  - Alternatively: Switch to card view on mobile (<768px)
  - Add "View as: Table | Cards" toggle
  - Sticky table headers on desktop
  - Test with 10, 50, 100 rows
- [ ] Create responsive DataTable component (Phase 3 Task)

#### 2.4.5: Form Responsive Layouts
- [ ] Audit all forms for mobile usability
  - Full-width inputs on mobile
  - Stack labels above inputs (not side-by-side)
  - Larger button sizes on mobile (min 44px height)
  - Proper spacing between fields (min 16px)
- [ ] Test forms on mobile devices:
  - Login form
  - Job application form
  - Profile edit form
  - Settings forms

#### 2.4.6: Touch Target Optimization
- [ ] Audit all interactive elements
  - Buttons: min 44x44px
  - Links: min 44x44px tap area (add padding if needed)
  - Checkboxes/radios: min 44x44px
  - Icons: min 44x44px tap area
- [ ] Add `@media (hover: none)` styles for touch devices
  - Remove hover states on touch
  - Add active/pressed states instead
- [ ] Test with Chrome DevTools touch emulation

#### 2.4.7: Responsive Typography
- [ ] Create responsive typography scale
  - Base: 16px on mobile, 16px on desktop
  - H1: 28px mobile → 48px desktop
  - H2: 24px mobile → 36px desktop
  - H3: 20px mobile → 28px desktop
- [ ] Use Tailwind responsive classes: `text-2xl md:text-4xl`
- [ ] Ensure readability on all screen sizes

#### 2.4.8: Real Device Testing
- [ ] Test on physical iOS device (iPhone)
  - Safari browser
  - Touch interactions
  - Scroll behavior
  - Form inputs (keyboard appears correctly)
- [ ] Test on physical Android device
  - Chrome browser
  - Touch interactions
  - Back button behavior
- [ ] Document any device-specific issues

---

### Task 2.5: Typography & Spacing Polish

#### 2.5.1: Heading Hierarchy Implementation
- [ ] Audit all pages for proper heading structure
  - One H1 per page (page title)
  - H2 for major sections
  - H3 for subsections
  - No skipped levels (H1 → H3 without H2)
- [ ] Create heading components in `frontend/src/components/ui/Typography.tsx`
  - `<H1>`, `<H2>`, `<H3>`, `<H4>` components
  - Consistent styling across app
  - Proper semantic HTML
  - Responsive sizing

#### 2.5.2: Line Height & Readability
- [ ] Verify line-height tokens in globals.css (already exist)
- [ ] Apply proper line-height to body text
  - Body text: `leading-relaxed` (1.75)
  - Headings: `leading-tight` (1.25)
  - Buttons/UI: `leading-normal` (1.5)
- [ ] Ensure comfortable reading experience

#### 2.5.3: Content Width Optimization
- [ ] Add max-width to text-heavy content
  - Create `.prose` utility or use Tailwind Typography
  - Max-width: 65-75 characters (~700px)
  - Center align on large screens
- [ ] Apply to:
  - Blog posts (if any)
  - Long-form content
  - Help/documentation pages
  - Form instructions

#### 2.5.4: Spacing System Implementation
- [ ] Verify spacing tokens in globals.css (already exist: --space-1 to --space-24)
- [ ] Create spacing utilities documentation
- [ ] Apply consistent spacing between sections
  - Section padding: `py-12 md:py-16` (48px → 64px)
  - Card spacing: `p-6` (24px)
  - Component spacing: `space-y-4` or `gap-4` (16px)
- [ ] Remove inconsistent spacing values

#### 2.5.5: Text Color Hierarchy
- [ ] Define text color usage patterns
  - Primary text: `text-foreground` (neutral-900 / neutral-100 dark)
  - Secondary text: `text-neutral-600 dark:text-neutral-400`
  - Muted text: `text-neutral-500 dark:text-neutral-500`
  - Disabled text: `text-neutral-400 dark:text-neutral-600`
- [ ] Apply consistently across all components
- [ ] Document in Storybook

#### 2.5.6: Font Weight Consistency
- [ ] Define font weight usage
  - Headings: font-semibold (600) or font-bold (700)
  - Body: font-normal (400)
  - Emphasis: font-medium (500)
  - Labels: font-medium (500)
- [ ] Apply consistently
- [ ] Update Button component to use font-medium (already set)

#### 2.5.7: Letter Spacing (Tracking)
- [ ] Add letter spacing to uppercase text
  - Uppercase labels: `tracking-wide` (0.025em)
  - Uppercase buttons: `tracking-wider` (0.05em)
- [ ] Add negative tracking to large headings (optional)
  - H1/H2: `tracking-tight` (-0.025em)
- [ ] Test readability

#### 2.5.8: Typography Testing
- [ ] Visual review of all pages
- [ ] Check heading hierarchy with accessibility tools
- [ ] Verify readability on mobile vs desktop
- [ ] Get feedback on typography from team/users

---

## Phase 3: Advanced Features & Components (Week 5-6)

### Task 3.1: Enterprise Data Table with @tanstack/react-table

#### 3.1.1: Base DataTable Component
- [ ] Create `frontend/src/components/ui/DataTable/DataTable.tsx`
  - Install/verify @tanstack/react-table in package.json
  - Create base table component with proper types
  - Add table styling using design tokens
  - Support generic data type: `DataTable<T>`
  - Add empty state component
  - Add loading skeleton state
- [ ] Create `frontend/src/components/ui/DataTable/index.ts` (barrel export)

#### 3.1.2: Column Sorting
- [ ] Implement single-column sorting
  - Add sort indicators (↑↓ icons) in column headers
  - Click to sort ascending → descending → no sort
  - Persist sort state in URL query params
- [ ] Implement multi-column sorting
  - Hold Shift + click for multi-column
  - Show sort order numbers (1, 2, 3) on multiple sorted columns
  - Add "Clear all sorts" button
- [ ] Add default sort configuration prop
- [ ] Test with string, number, date columns

#### 3.1.3: Column Filtering
- [ ] Create filter UI components
  - Text filter: input with debounce (300ms)
  - Select filter: dropdown with options
  - Multi-select filter: checkboxes
  - Date range filter: date picker (start/end)
  - Number range filter: min/max inputs
- [ ] Add filter button/icon to column headers
- [ ] Show active filter count badge on column header
- [ ] Create `ColumnFilter.tsx` component for each type
- [ ] Add "Clear filters" button for each column
- [ ] Persist filters in URL query params

#### 3.1.4: Global Search
- [ ] Add global search input above table
  - Debounced search (300ms delay)
  - Search placeholder: "Search across all columns..."
  - Search icon (lucide-react)
  - Clear button (X) when text entered
- [ ] Implement search across all visible columns
- [ ] Highlight search matches in cells (optional)
- [ ] Show search result count: "Showing 24 of 156 results"

#### 3.1.5: Pagination
- [ ] Create pagination controls component
  - Previous/Next buttons
  - Page number buttons (show 1, 2, 3, ..., last)
  - "Go to page" input
  - Rows per page dropdown (10, 25, 50, 100)
- [ ] Show pagination info: "Showing 1-25 of 156"
- [ ] Support server-side pagination (optional prop)
- [ ] Persist page state in URL query params
- [ ] Add keyboard shortcuts (arrow keys for prev/next)

#### 3.1.6: Row Selection
- [ ] Add checkbox column for row selection
  - Checkbox in header for select all (on current page)
  - Checkboxes in each row
  - Indeterminate state when some rows selected
  - Keyboard support (Shift + click for range selection)
- [ ] Show selection count: "3 of 25 selected"
- [ ] Add "Select all X rows" button (if more than page size)
- [ ] Add "Clear selection" button
- [ ] Expose selected rows via callback prop

#### 3.1.7: Expandable Rows
- [ ] Add expand/collapse icon column
  - Chevron right (collapsed) / down (expanded)
  - Smooth expansion animation
- [ ] Support custom expanded row content (render prop)
- [ ] Allow expanding multiple rows or single row
- [ ] Keyboard support (Enter to expand/collapse)
- [ ] Persist expanded state

#### 3.1.8: Column Visibility Toggle
- [ ] Create column visibility dropdown
  - Dropdown button: "Columns" with column icon
  - Checklist of all columns
  - Show/hide checkboxes for each column
  - "Show all" / "Hide all" buttons
- [ ] Prevent hiding all columns (at least 1 required)
- [ ] Persist visibility state in localStorage
- [ ] Add "Reset to default" button

#### 3.1.9: Column Resizing
- [ ] Add resize handles between column headers
  - Vertical divider line
  - Cursor changes to resize indicator
  - Drag to resize column width
  - Double-click to auto-fit width
- [ ] Set min/max column widths
- [ ] Persist column widths in localStorage
- [ ] Add "Reset column widths" button

#### 3.1.10: Column Reordering (Drag & Drop)
- [ ] Install/verify @dnd-kit/core in package.json
- [ ] Make column headers draggable
  - Drag handle icon in header
  - Visual feedback during drag (ghost element)
  - Drop indicators between columns
- [ ] Update column order on drop
- [ ] Persist column order in localStorage
- [ ] Add "Reset column order" button

#### 3.1.11: Export to CSV
- [ ] Create export utility function
  - Export current view (filtered/sorted data)
  - Export all data (unfiltered)
  - Export selected rows only
- [ ] Add "Export" dropdown button
  - Options: Current view, All data, Selected rows
  - Download as CSV file
  - Proper CSV formatting (escape commas, quotes)
- [ ] Show export progress for large datasets (>1000 rows)

#### 3.1.12: Responsive Mobile View
- [ ] Detect mobile viewport (<768px)
- [ ] Switch to card view on mobile
  - Each row becomes a card
  - Show key columns prominently
  - Collapsible card for additional data
- [ ] Add view toggle: "Table" | "Cards" (mobile only)
- [ ] Maintain sorting/filtering in card view
- [ ] Test on mobile devices

#### 3.1.13: DataTable Storybook Documentation
- [ ] Create `DataTable.stories.tsx`
  - Basic example with sample data
  - With sorting enabled
  - With filtering enabled
  - With row selection
  - With expandable rows
  - With all features enabled
- [ ] Document all props and callbacks

#### 3.1.14: Replace Existing Tables
- [ ] Replace `frontend/src/components/pages/JobTableView.tsx`
  - Migrate to DataTable component
  - Configure columns for job data
  - Add custom cell renderers (status badges, etc.)
  - Test all functionality
- [ ] Create `frontend/src/components/pages/ApplicationsTable.tsx`
  - Use DataTable component
  - Configure columns for application data
  - Add status column with colored badges
  - Add date formatting
  - Test all functionality

---

### Task 3.2: Command Palette (⌘K / Ctrl+K)

#### 3.2.1: Base Command Palette Component
- [ ] Verify `cmdk` package in package.json
- [ ] Create `frontend/src/components/ui/CommandPalette.tsx`
  - Use `cmdk` library (Command component)
  - Modal-style overlay with backdrop blur
  - Input at top with search icon
  - Results list below
  - Keyboard navigation (arrow keys, enter, escape)
  - Design to match Linear/Raycast/Spotlight style

#### 3.2.2: Global Keyboard Shortcut
- [ ] Create `frontend/src/hooks/useKeyboardShortcut.ts`
  - Listen for ⌘K (Mac) / Ctrl+K (Windows/Linux)
  - Prevent default browser behavior
  - Toggle command palette visibility
- [ ] Integrate in app layout
- [ ] Show keyboard hint in UI: "Press ⌘K to search"

#### 3.2.3: Command Categories & Actions
- [ ] Define command categories structure
  - Navigation: "Go to Dashboard", "Go to Jobs", etc.
  - Actions: "Create Job", "Create Application", etc.
  - Settings: "Toggle theme", "Open settings", etc.
  - Search: "Search jobs", "Search applications"
- [ ] Create command registry in `frontend/src/lib/commands.ts`
  - Array of command objects: { id, label, category, action, icon, keywords }
  - Action: function to execute or route to navigate
  - Keywords: array of search terms

#### 3.2.4: Search Functionality
- [ ] Implement fuzzy search across commands
  - Match by label and keywords
  - Rank results by relevance
  - Show top 10 results
- [ ] Add search across job titles
  - Query jobs from API (debounced 300ms)
  - Show job results in separate group
  - Click to navigate to job detail
- [ ] Add search across applications
  - Query applications from API
  - Show application results in separate group

#### 3.2.5: Recent Searches & Commands
- [ ] Store recent searches in localStorage
  - Save last 10 searches
  - Show at top when palette opens (before typing)
  - Clear history button
- [ ] Show recently used commands
  - Track command usage
  - Sort by recency

#### 3.2.6: Command Execution
- [ ] Implement command action handlers
  - Navigation commands: use Next.js router.push()
  - Theme toggle: call theme toggle function
  - Create actions: open modal or navigate to create page
- [ ] Close palette after command execution
- [ ] Add command execution feedback (toast notification)

#### 3.2.7: Visual Design & Polish
- [ ] Style command palette with design tokens
  - Glass morphism backdrop
  - Input with focus ring
  - Hover state for results
  - Keyboard-selected item highlight (different from hover)
  - Icons for each command (lucide-react)
- [ ] Add result icons based on category
- [ ] Add keyboard shortcut hints (e.g., "↵ Enter" to select)
- [ ] Add smooth animations (fade in/out, slide up)

#### 3.2.8: Accessibility
- [ ] Add ARIA labels for screen readers
- [ ] Announce result count to screen readers
- [ ] Support keyboard-only navigation
- [ ] Test with VoiceOver/NVDA

#### 3.2.9: Integration & Testing
- [ ] Add CommandPalette to `frontend/src/app/layout.tsx`
- [ ] Test keyboard shortcut globally
- [ ] Test search functionality
- [ ] Test command execution
- [ ] Test on mobile (show different trigger, no keyboard shortcut)

---

### Task 3.3: Advanced Search & Filtering

#### 3.3.1: Advanced Search UI Component
- [ ] Create `frontend/src/components/features/AdvancedSearch.tsx`
  - Slide-out panel or modal
  - Multi-field search form
  - Query builder interface
  - Live preview of results count
- [ ] Add "Advanced Search" button to Jobs and Applications pages

#### 3.3.2: Query Builder Interface
- [ ] Create query builder with AND/OR logic
  - Add rule/group buttons
  - Each rule: Field + Operator + Value
  - Operators: equals, contains, greater than, less than, between, is empty, is not empty
  - Groups with AND/OR toggle
  - Nested groups support (optional)
- [ ] Create `QueryBuilder.tsx` component
- [ ] Use visual tree structure to show logic

#### 3.3.3: Field Selection
- [ ] Define searchable fields for Jobs
  - Title, Company, Location, Salary, Experience, Skills, Date posted
- [ ] Define searchable fields for Applications
  - Job title, Company, Status, Applied date, Follow-up date
- [ ] Create field selector dropdown
  - Grouped by category
  - Icons for each field type

#### 3.3.4: Operator & Value Inputs
- [ ] Create operator selector based on field type
  - Text fields: contains, equals, starts with, ends with
  - Number fields: equals, greater than, less than, between
  - Date fields: before, after, between, in last X days
  - Boolean fields: is, is not
- [ ] Create value input based on field type
  - Text: input field with autocomplete
  - Number: number input or range
  - Date: date picker
  - Select: dropdown with options
- [ ] Add validation for value inputs

#### 3.3.5: Save & Manage Searches
- [ ] Add "Save search" button
  - Prompt for search name
  - Save to backend API and localStorage
  - Associate with user account
- [ ] Create saved searches dropdown
  - List of user's saved searches
  - Load search: populate query builder
  - Edit search
  - Delete search
  - Share search (future feature)
- [ ] Add "Saved searches" section in sidebar

#### 3.3.6: Recent Searches
- [ ] Track recent searches in localStorage
  - Save last 10 searches
  - Include search criteria and result count
- [ ] Show recent searches in dropdown
  - Click to load search
  - Clear history button

#### 3.3.7: Filter Chips Display
- [ ] Show active filters as chips above results
  - One chip per filter rule
  - Format: "Field: value"
  - Click X on chip to remove filter
  - Click chip to edit filter
- [ ] Add "Clear all filters" button
- [ ] Show filter count badge: "3 filters active"

#### 3.3.8: Integration with Jobs Page
- [ ] Add AdvancedSearch to `frontend/src/components/pages/JobsPage.tsx`
  - Button to open advanced search
  - Apply search to job list query
  - Update URL with search params
  - Show active filters
- [ ] Test search with various combinations

#### 3.3.9: Integration with Applications Page
- [ ] Add AdvancedSearch to `frontend/src/components/pages/ApplicationsPage.tsx`
  - Button to open advanced search
  - Apply search to applications query
  - Update URL with search params
  - Show active filters
- [ ] Test search functionality

---

### Task 3.4: Bulk Operations

#### 3.4.1: Bulk Selection in DataTable
- [ ] Verify DataTable row selection (Task 3.1.6)
- [ ] Add bulk selection mode toggle
  - Button: "Select items" to enter selection mode
  - Show checkboxes when in selection mode
  - Exit selection mode button

#### 3.4.2: Bulk Action Toolbar
- [ ] Create `frontend/src/components/ui/BulkActionBar.tsx`
  - Fixed position bar at bottom of screen
  - Slide up animation when items selected
  - Shows selection count: "3 items selected"
  - Action buttons based on context
  - Cancel selection button
- [ ] Style with design tokens
  - Background with backdrop blur
  - Border and shadow
  - Accent color for primary action

#### 3.4.3: Bulk Actions for Jobs
- [ ] Define bulk actions for job listings
  - Archive selected jobs
  - Add selected jobs to wishlist/saved
  - Export selected jobs to CSV
  - Mark as viewed/unviewed
- [ ] Implement action handlers
  - API calls for each action
  - Optimistic UI updates
  - Error handling

#### 3.4.4: Bulk Actions for Applications
- [ ] Define bulk actions for applications
  - Change status (dropdown: Applied, Interviewing, Offer, Rejected, Accepted)
  - Delete selected applications
  - Export selected to CSV
  - Archive selected applications
- [ ] Implement action handlers

#### 3.4.5: Confirmation Dialogs
- [ ] Create confirmation dialog for destructive actions
  - "Delete 5 applications?" with warning message
  - List items to be deleted (first 5, then "and X more")
  - Confirm button (red/destructive)
  - Cancel button
- [ ] Add checkbox: "Don't ask again" (store preference)
- [ ] Use Modal component (from Task 1.8)

#### 3.4.6: Bulk Operation Progress
- [ ] Create progress indicator for long-running bulk operations
  - Progress bar or circular spinner
  - Status text: "Processing 5 of 25 items..."
  - Cancel button (if possible)
- [ ] Show success/failure summary
  - "Successfully updated 24 items, 1 failed"
  - Show errors for failed items
  - Retry failed items button

#### 3.4.7: Undo Functionality
- [ ] Implement undo for non-destructive bulk actions
  - Toast notification with "Undo" button
  - Undo timeout: 5 seconds
  - Store previous state temporarily
- [ ] Test undo for status changes, archive, etc.

#### 3.4.8: Testing
- [ ] Test bulk selection across pages (pagination)
- [ ] Test bulk actions with 1 item, 10 items, 100+ items
- [ ] Test error handling (partial success/failure)
- [ ] Test performance with large selections

---

### Task 3.5: Advanced Notification System

#### 3.5.1: Notification Categories
- [ ] Update `frontend/src/components/notifications/NotificationSystem.tsx`
- [ ] Define notification categories
  - System: App updates, maintenance alerts
  - Job Alerts: New job matches, saved search results
  - Application Updates: Status changes, interview scheduled
  - Recommendations: AI-generated suggestions
  - Social: Comments, mentions (if social features exist)
- [ ] Add category filter in notification center
- [ ] Add category badges with icons

#### 3.5.2: Notification Center (Bell Icon)
- [ ] Create `frontend/src/components/ui/NotificationCenter.tsx`
  - Bell icon in Navigation header
  - Badge with unread count
  - Dropdown panel when clicked
  - List of recent notifications (last 20)
  - "View all" link to full notification page
- [ ] Add notification items with:
  - Icon based on category
  - Title and description
  - Timestamp (relative: "2 hours ago")
  - Read/unread indicator
  - Click to navigate or dismiss

#### 3.5.3: Notification History Page
- [ ] Create `frontend/src/app/notifications/page.tsx`
  - Full list of all notifications
  - Filters: All, Unread, Category
  - Search notifications
  - Pagination
  - Bulk actions: Mark all as read, Delete all
- [ ] Use DataTable component for notification list (optional)

#### 3.5.4: Notification Preferences Panel
- [ ] Create `frontend/src/components/settings/NotificationPreferences.tsx`
  - Toggle notifications per category
  - Email notification settings (daily digest, immediate, off)
  - Push notification settings (if supported)
  - Sound/vibration settings
  - Do Not Disturb schedule (optional)
- [ ] Add to Settings page
- [ ] Save preferences to backend API

#### 3.5.5: Push Notifications (Browser)
- [ ] Request notification permission
  - Prompt user on first visit or in settings
  - Show benefits of enabling notifications
- [ ] Implement Web Push API
  - Register service worker
  - Subscribe to push notifications
  - Store subscription on backend
- [ ] Send test notification button in settings
- [ ] Handle notification click (navigate to relevant page)

#### 3.5.6: Real-time Notifications
- [ ] Integrate with WebSocket connection (Phase 5 Task)
- [ ] Listen for notification events
- [ ] Display toast notification for new notifications
- [ ] Update notification bell badge count in real-time
- [ ] Play notification sound (optional, with user preference)

#### 3.5.7: Notification Templates
- [ ] Create notification template system
  - Job match: "New job: {jobTitle} at {company}"
  - Application update: "Your application for {jobTitle} status changed to {status}"
  - Interview scheduled: "Interview scheduled for {jobTitle} on {date}"
  - Recommendation: "We found {count} jobs matching your profile"
- [ ] Support rich content (links, buttons)
- [ ] Support images/avatars (optional)

#### 3.5.8: Mark as Read/Unread
- [ ] Add "Mark as read" action to notifications
- [ ] Auto-mark as read when viewing notification detail
- [ ] Add "Mark all as read" button
- [ ] Update unread count badge immediately

#### 3.5.9: Notification Actions
- [ ] Add inline actions to notifications
  - "View job" button
  - "View application" button
  - "Dismiss" button
  - "Remind me later" (snooze)
- [ ] Execute actions without leaving current page (modal/panel)

#### 3.5.10: Testing
- [ ] Test notification delivery in various scenarios
- [ ] Test notification center with 0, 1, 10, 100+ notifications
- [ ] Test browser push notifications
- [ ] Test notification preferences
- [ ] Test on mobile devices

---

## Phase 4: Performance & Optimization (Week 7-8)

### Task 4.1: Code Splitting & Lazy Loading

#### 4.1.1: Route-Based Code Splitting
- [ ] Audit current bundle size with Next.js build analysis
- [ ] Run `npm run build` and note bundle sizes
- [ ] Run `ANALYZE=true npm run build` 
- [ ] Identify large chunks (>200KB)
- [ ] Document route bundle sizes

#### 4.1.2: Component-Level Code Splitting
- [ ] Identify heavy components for lazy loading
- [ ] Implement `React.lazy()` for heavy components
- [ ] Wrap with `<Suspense>` and loading fallback
- [ ] Test functionality

#### 4.1.3: Dynamic Imports
- [ ] Identify conditionally used features
- [ ] Convert to dynamic imports
- [ ] Test all features

#### 4.1.4: Preload Critical Routes
- [ ] Identify critical user paths
- [ ] Add preload for critical routes
- [ ] Use `router.prefetch()` on link hover

#### 4.1.5: Bundle Size Optimization
- [ ] Run bundle analyzer
- [ ] Remove unused dependencies
- [ ] Set bundle size budget alerts

---

### Task 4.2: Image Optimization

#### 4.2.1: Next.js Image Migration
- [ ] Audit all `<img>` tags
- [ ] Replace with Next.js `<Image>` component
- [ ] Add required props

#### 4.2.2: Responsive Images
- [ ] Configure Image sizes in next.config.js
- [ ] Use `sizes` prop
- [ ] Test different screens

#### 4.2.3: Format Optimization
- [ ] Configure WebP format
- [ ] Compress source images (<100KB)
- [ ] Test image quality

#### 4.2.4: Testing
- [ ] Test on slow 3G network
- [ ] Verify blur placeholders
- [ ] Check WebP format delivery

---

### Task 4.3: List Virtualization

#### 4.3.1: Install & Setup
- [ ] Install `@tanstack/react-virtual`
- [ ] Verify installation

#### 4.3.2: Implement for Job Lists
- [ ] Create VirtualJobList component
- [ ] Configure virtualization
- [ ] Test with large datasets

#### 4.3.3: Implement for Application Lists
- [ ] Create VirtualApplicationList
- [ ] Test performance

#### 4.3.4: DataTable Virtualization
- [ ] Add virtualization to DataTable
- [ ] Test with 1000+ rows

#### 4.3.5: Performance Testing
- [ ] Benchmark rendering time
- [ ] Measure FPS (target: 60fps)
- [ ] Test on lower-end devices

---

### Task 4.4: Caching & State Management

#### 4.4.1: React Query Optimization
- [ ] Review current setup
- [ ] Optimize cache settings
- [ ] Configure per-query strategies

#### 4.4.2: Stale-While-Revalidate
- [ ] Implement SWR for key data
- [ ] Test instant cached data

#### 4.4.3: Optimistic Updates
- [ ] Implement for mutations
- [ ] Test rollback on error

#### 4.4.4: Prefetching
- [ ] Prefetch on hover/focus
- [ ] Prefetch next pagination page

---

### Task 4.5: Performance Monitoring

#### 4.5.1: Lighthouse CI
- [ ] Install Lighthouse CI
- [ ] Create config file
- [ ] Add npm script

#### 4.5.2: Core Web Vitals
- [ ] Implement Web Vitals reporting
- [ ] Send metrics to analytics

#### 4.5.3: Performance Budgets
- [ ] Define budgets (FCP, LCP, FID, CLS)
- [ ] Document budgets
- [ ] Set up alerts

#### 4.5.4: CI/CD Integration
- [ ] Add Lighthouse to GitHub Actions
- [ ] Fail build if score < 90

---

### Task 4.6: Accessibility Final Audit

#### 4.6.1: Automated Testing
- [ ] Install axe-core
- [ ] Run axe DevTools on all pages
- [ ] Document violations

#### 4.6.2: WCAG 2.1 AA Fixes
- [ ] Fix color contrast (min 4.5:1)
- [ ] Fix alt text
- [ ] Fix heading hierarchy
- [ ] Fix form labels
- [ ] Fix focus indicators

#### 4.6.3: Keyboard Navigation
- [ ] Test all pages keyboard-only
- [ ] Ensure logical tab order
- [ ] Add skip link

#### 4.6.4: Screen Reader Testing
- [ ] Test with VoiceOver/NVDA
- [ ] Fix ARIA issues

#### 4.6.5: Documentation
- [ ] Create accessibility statement
- [ ] Create ACCESSIBILITY.md
- [ ] Sign off on compliance

---

## Phase 5: Advanced UX Patterns (Week 9-10)

### Task 5.1: User Onboarding Flow

#### 5.1.1: Onboarding Wizard Component
- [ ] Create `frontend/src/components/onboarding/OnboardingWizard.tsx`
- [ ] Multi-step wizard with navigation (Next/Back/Skip)
- [ ] Progress indicator at top (1 of 5, 2 of 5, etc.)
- [ ] Smooth transitions between steps
- [ ] Save progress to allow resume later

#### 5.1.2: Step 1: Welcome & Profile Setup
- [ ] Create welcome screen with value proposition
- [ ] Collect basic info: name, email (pre-filled if signed in)
- [ ] Upload profile photo (optional)
- [ ] Job title / role
- [ ] Years of experience (dropdown: 0-1, 1-3, 3-5, 5-10, 10+)

#### 5.1.3: Step 2: Skills & Expertise
- [ ] Multi-select skill tags
- [ ] Popular skills suggestions
- [ ] Search for skills
- [ ] Add custom skills
- [ ] Select proficiency level per skill (optional)

#### 5.1.4: Step 3: Resume Upload
- [ ] File upload with drag & drop
- [ ] Support PDF, DOCX formats
- [ ] Parse resume with AI (optional)
- [ ] Auto-fill skills from resume
- [ ] Skip if no resume

#### 5.1.5: Step 4: Job Preferences
- [ ] Preferred job titles (multi-select)
- [ ] Preferred locations (city, state, or remote)
- [ ] Salary expectations (range slider)
- [ ] Work arrangement: Remote, Hybrid, On-site
- [ ] Company size preference (optional)
- [ ] Industry preference (optional)

#### 5.1.6: Step 5: Feature Tour
- [ ] Interactive tour of key features
- [ ] Highlight dashboard, jobs, applications
- [ ] Show command palette (⌘K)
- [ ] Show notification center
- [ ] Animated pointers and tooltips

#### 5.1.7: Completion & Next Steps
- [ ] Completion screen with success animation
- [ ] Show first recommended jobs
- [ ] CTA buttons: "View Dashboard", "Browse Jobs"
- [ ] Option to retake onboarding later in settings

#### 5.1.8: Skip & Resume Logic
- [ ] Allow skipping individual steps
- [ ] Allow skipping entire onboarding
- [ ] Save progress in backend
- [ ] Resume from last step if interrupted
- [ ] Show onboarding progress in profile

---

### Task 5.2: Enhanced Charts & Data Visualization

#### 5.2.1: Chart Component Library
- [ ] Create `frontend/src/components/charts/` directory
- [ ] Verify Recharts installed (already in package.json)
- [ ] Create base chart wrapper with consistent styling

#### 5.2.2: Application Status Chart
- [ ] Create `ApplicationStatusChart.tsx`
- [ ] Pie chart or donut chart showing status distribution
- [ ] Interactive tooltips with counts and percentages
- [ ] Click slice to filter applications by status
- [ ] Smooth animations on load and data changes

#### 5.2.3: Application Timeline Chart
- [ ] Create `ApplicationTimelineChart.tsx`
- [ ] Line chart showing applications over time
- [ ] X-axis: dates, Y-axis: application count
- [ ] Show trend line (optional)
- [ ] Hover tooltip with exact count and date
- [ ] Zoom/pan controls for large date ranges

#### 5.2.4: Salary Distribution Chart
- [ ] Create `SalaryDistributionChart.tsx`
- [ ] Bar chart or histogram showing salary ranges
- [ ] X-axis: salary buckets, Y-axis: job count
- [ ] Highlight user's target salary range
- [ ] Interactive tooltips

#### 5.2.5: Skills Demand Chart
- [ ] Create `SkillsDemandChart.tsx`
- [ ] Bar chart showing top skills in job postings
- [ ] Compare with user's skills (overlay)
- [ ] Clickable bars to filter jobs by skill
- [ ] Sort by: frequency, match rate, trending

#### 5.2.6: Success Rate Chart
- [ ] Create `SuccessRateChart.tsx`
- [ ] Funnel chart: Applied → Interviewed → Offer → Accepted
- [ ] Show conversion rates at each stage
- [ ] Benchmark against averages (optional)
- [ ] Interactive hover states

#### 5.2.7: Chart Interactivity
- [ ] Add zoom/pan controls to time-series charts
- [ ] Add legend toggle to show/hide datasets
- [ ] Add data export button (CSV, PNG)
- [ ] Add full-screen mode for detailed analysis
- [ ] Responsive charts (adapt to mobile)

#### 5.2.8: Chart Animations
- [ ] Entry animations for all charts
- [ ] Smooth transitions on data updates
- [ ] Hover animations (lift effect, highlight)
- [ ] Use Framer Motion for custom animations

#### 5.2.9: Chart Integration
- [ ] Add charts to Dashboard page
- [ ] Add charts to Analytics page
- [ ] Create chart grid layout (responsive)
- [ ] Add chart loading skeletons

---

### Task 5.3: Real-time Updates with WebSockets

#### 5.3.1: WebSocket Client Setup
- [ ] Create `frontend/src/lib/websocket.ts`
- [ ] Implement WebSocket client class
- [ ] Connect to backend WebSocket server
- [ ] Handle connection lifecycle (open, close, error)
- [ ] Auto-reconnect on disconnect (with exponential backoff)

#### 5.3.2: Connection Status Indicator
- [ ] Create `frontend/src/components/ui/ConnectionStatus.tsx`
- [ ] Show in Navigation header (small indicator)
- [ ] States: Connected (green), Connecting (yellow), Disconnected (red)
- [ ] Tooltip with status message
- [ ] Click to manually reconnect

#### 5.3.3: Real-time Job Recommendations
- [ ] Listen for `job:recommendation` WebSocket events
- [ ] Show toast notification when new job matches
- [ ] Update jobs list in real-time
- [ ] Badge on Jobs tab: "3 new matches"
- [ ] Smooth animation for new items appearing

#### 5.3.4: Real-time Application Status Updates
- [ ] Listen for `application:status_change` events
- [ ] Update application status in UI instantly
- [ ] Show toast notification: "Application status changed to Interviewing"
- [ ] Update dashboard stats in real-time
- [ ] Badge animation for status change

#### 5.3.5: Real-time Notifications
- [ ] Listen for `notification:new` events
- [ ] Display toast notification
- [ ] Update notification bell badge count
- [ ] Add to notification center list
- [ ] Play sound (with user preference)

#### 5.3.6: Presence & Typing Indicators (Future)
- [ ] Listen for user presence events (if multi-user features exist)
- [ ] Show who's online (optional)
- [ ] Typing indicators for comments/chat (optional)

#### 5.3.7: Reconnection Handling
- [ ] Detect network offline/online events
- [ ] Show reconnecting toast
- [ ] Retry connection with exponential backoff
- [ ] Resync data on reconnect (fetch latest)
- [ ] Handle message queue for missed events

#### 5.3.8: WebSocket Testing
- [ ] Test real-time updates in multiple browser tabs
- [ ] Test reconnection after network disruption
- [ ] Test on mobile devices
- [ ] Test with slow network

---

### Task 5.4: Drag & Drop Features

#### 5.4.1: Install Drag & Drop Library
- [ ] Install `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- [ ] Verify installation in package.json

#### 5.4.2: Draggable Dashboard Widgets
- [ ] Make dashboard cards/widgets draggable
- [ ] Allow reordering widgets
- [ ] Save widget layout to user preferences
- [ ] Add "Reset layout" button
- [ ] Visual feedback during drag (ghost element, drop zones)

#### 5.4.3: Kanban Board for Applications
- [ ] Create `frontend/src/components/pages/ApplicationKanban.tsx`
- [ ] Columns: Applied, Interviewing, Offer, Rejected
- [ ] Drag application cards between columns
- [ ] Update status on drop (with API call)
- [ ] Optimistic update + rollback on error
- [ ] Smooth animations

#### 5.4.4: Drag to Reorder Lists
- [ ] Add drag-to-reorder for custom job lists
- [ ] Add drag-to-reorder for saved searches
- [ ] Save order to backend
- [ ] Visual feedback (drag handle, drop indicator)

#### 5.4.5: File Drag & Drop
- [ ] Enhance FileUpload component with drag & drop
- [ ] Highlight drop zone on drag over
- [ ] Support multiple files
- [ ] Show upload progress per file
- [ ] Allow removing files before upload

#### 5.4.6: Accessibility
- [ ] Add keyboard support for drag & drop
  - Space to pick up, arrow keys to move, Enter to drop
- [ ] Announce drag/drop actions to screen readers
- [ ] Add ARIA live regions for status updates

#### 5.4.7: Testing
- [ ] Test drag & drop on desktop
- [ ] Test touch drag on mobile/tablet
- [ ] Test keyboard navigation
- [ ] Test with screen reader

---

### Task 5.5: Advanced Filters & Custom Views

#### 5.5.1: Save Custom Views
- [ ] Create `frontend/src/components/features/SaveView.tsx`
- [ ] Button to save current filters/sort as a view
- [ ] Prompt for view name
- [ ] Save to backend API and sync across devices
- [ ] Store: filters, sort, columns, layout preferences

#### 5.5.2: View Management
- [ ] Create `frontend/src/components/features/ViewSelector.tsx`
- [ ] Dropdown to select saved views
- [ ] Load view: apply filters, sort, layout
- [ ] Edit view (update name, filters)
- [ ] Delete view (with confirmation)
- [ ] Duplicate view

#### 5.5.3: Preset Views
- [ ] Create default preset views
  - "Applied This Week" (filter: applied_date > 7 days ago)
  - "High Priority" (filter: priority = high)
  - "Awaiting Response" (filter: status = applied, > 2 weeks)
  - "Interviews Scheduled" (filter: status = interviewing)
- [ ] Allow users to customize presets
- [ ] Pin favorite views to sidebar

#### 5.5.4: View Switcher UI
- [ ] Add view switcher to Jobs and Applications pages
- [ ] Show current view name prominently
- [ ] Quick access to recent views
- [ ] Icon for each view (optional)

#### 5.5.5: Share Views (Future Multi-user)
- [ ] Add "Share view" button
- [ ] Generate shareable link
- [ ] Allow read-only access for shared views
- [ ] Permission controls (future feature)

#### 5.5.6: View Templates
- [ ] Create view templates for common use cases
- [ ] Template gallery in settings
- [ ] One-click apply template
- [ ] Community-shared templates (future)

#### 5.5.7: Testing
- [ ] Test save/load/edit/delete views
- [ ] Test preset views apply correctly
- [ ] Test view sync across devices
- [ ] Test view performance with complex filters

---

## Phase 6: Polish & Production Ready (Week 11-12)

### Task 6.1: Error Handling & Recovery

#### 6.1.1: Enhanced Error Boundary
- [ ] Update `frontend/src/components/ErrorBoundary.tsx`
- [ ] Catch component errors with detailed logging
- [ ] Show user-friendly error UI (not technical stack trace)
- [ ] Add "Retry" button to re-render component
- [ ] Add "Report issue" button (send error to backend)
- [ ] Different error UIs for different error types

#### 6.1.2: Network Error Handling
- [ ] Create `frontend/src/lib/errorHandling.ts`
- [ ] Intercept API errors in unified API client
- [ ] Classify errors: Network, Auth, Server, Client, Unknown
- [ ] Show appropriate toast notifications
  - Network error: "Connection lost. Retrying..."
  - 401: "Session expired. Please log in."
  - 403: "You don't have permission for this action."
  - 404: "Resource not found."
  - 500: "Server error. Please try again later."

#### 6.1.3: Retry Mechanisms
- [ ] Add automatic retry for failed requests (with exponential backoff)
- [ ] Manual retry button in error messages
- [ ] Queue requests during offline mode
- [ ] Replay queued requests when back online

#### 6.1.4: Offline Mode Detection
- [ ] Listen for `online`/`offline` browser events
- [ ] Show offline banner at top of page
- [ ] Disable actions that require network
- [ ] Cache data for offline viewing (Service Worker)
- [ ] Show cached data indicator

#### 6.1.5: Custom Error Pages
- [ ] Create `frontend/src/app/404/page.tsx` (Not Found)
  - Friendly message: "Page not found"
  - Helpful links: Dashboard, Jobs, Applications
  - Search bar to find what they're looking for
- [ ] Create `frontend/src/app/500/page.tsx` (Server Error)
  - Friendly message: "Something went wrong"
  - Retry button
  - Contact support link
- [ ] Create `frontend/src/app/error.tsx` (Next.js error handling)

#### 6.1.6: Graceful Degradation
- [ ] Identify non-critical features
- [ ] Degrade gracefully if feature fails (don't crash entire app)
- [ ] Show fallback UI or hide feature
- [ ] Log non-critical errors without alerting user

#### 6.1.7: Error Logging & Monitoring
- [ ] Integrate Sentry for error tracking (already in package.json)
- [ ] Configure Sentry in `frontend/src/app/layout.tsx`
- [ ] Set up source maps for production
- [ ] Add user context to error reports
- [ ] Set up error alerting rules

---

### Task 6.2: Contextual Help & Documentation

#### 6.2.1: Tooltip Hints on First Use
- [ ] Create `frontend/src/hooks/useFirstTimeHint.ts`
- [ ] Track which features user has seen (localStorage)
- [ ] Show tooltip on first interaction
- [ ] "Got it" button to dismiss permanently
- [ ] Apply to: Command palette, drag & drop, filters, etc.

#### 6.2.2: Help Icon System
- [ ] Create `frontend/src/components/ui/HelpIcon.tsx`
- [ ] Small "?" icon next to complex features
- [ ] Popover with explanation on hover/click
- [ ] Link to full documentation
- [ ] Consistent styling

#### 6.2.3: Feature Tour Modal
- [ ] Create `frontend/src/components/help/FeatureTour.tsx`
- [ ] Multi-step modal explaining key features
- [ ] Screenshots or GIFs
- [ ] Navigation: Next, Previous, Skip
- [ ] Accessible via Help menu

#### 6.2.4: Help Center / FAQ Section
- [ ] Create `frontend/src/app/help/page.tsx`
- [ ] Organize by categories: Getting Started, Features, Troubleshooting
- [ ] Searchable FAQ
- [ ] Accordion-style Q&A
- [ ] Link to video tutorials

#### 6.2.5: Video Tutorials
- [ ] Create or embed video tutorials
  - "Getting Started with Career Copilot"
  - "How to Track Applications"
  - "Using AI Job Recommendations"
  - "Advanced Search & Filters"
- [ ] Host on YouTube or Vimeo
- [ ] Embed in Help Center
- [ ] Add video transcripts (accessibility)

#### 6.2.6: Contextual Help in Features
- [ ] Add help text to complex forms
- [ ] Add tooltips to unclear buttons/icons
- [ ] Add "Learn more" links to documentation
- [ ] Add examples/placeholders in inputs

#### 6.2.7: Feedback Widget
- [ ] Add feedback button in footer or settings
- [ ] Simple form: Rating, Comment, Screenshot option
- [ ] Send to backend for review
- [ ] Thank you message after submission

---

### Task 6.3: Export & Import Features

#### 6.3.1: Export Applications to CSV
- [ ] Create `frontend/src/lib/export/exportToCSV.ts`
- [ ] Export all applications or filtered/selected
- [ ] Include columns: Job title, Company, Status, Applied date, etc.
- [ ] Trigger download with proper filename
- [ ] Show success toast

#### 6.3.2: Export Applications to PDF
- [ ] Install `jspdf` and `jspdf-autotable`
- [ ] Create `frontend/src/lib/export/exportToPDF.ts`
- [ ] Generate PDF with table layout
- [ ] Include logo, title, date
- [ ] Proper formatting and styling
- [ ] Trigger download

#### 6.3.3: Export Jobs List
- [ ] Similar CSV/PDF export for jobs
- [ ] Include relevant job data
- [ ] Export saved jobs or search results

#### 6.3.4: Backup User Data (Full Export)
- [ ] Create "Export all data" feature in settings
- [ ] Generate JSON file with all user data
  - Profile, Applications, Saved jobs, Preferences
- [ ] Compressed zip file (if large)
- [ ] Encrypt sensitive data (optional)

#### 6.3.5: Import Jobs from CSV
- [ ] Create "Import jobs" feature
- [ ] Upload CSV file
- [ ] Parse and validate CSV
- [ ] Preview import (first 5 rows)
- [ ] Map columns to job fields
- [ ] Bulk import with progress indicator
- [ ] Show success/error summary

#### 6.3.6: Data Restore from Backup
- [ ] Upload backup JSON file
- [ ] Validate file structure
- [ ] Preview what will be restored
- [ ] Restore data with confirmation
- [ ] Show restore progress
- [ ] Success message with summary

#### 6.3.7: Export Templates
- [ ] Provide CSV templates for import
- [ ] Link in import UI: "Download template"
- [ ] Include example data

---

### Task 6.4: Settings & Preferences

#### 6.4.1: Settings Page Layout
- [ ] Create `frontend/src/app/settings/page.tsx`
- [ ] Sidebar navigation for categories
  - Profile, Appearance, Notifications, Privacy, Account, Data
- [ ] Main content area for settings
- [ ] Save button (auto-save optional)
- [ ] Changes indicator

#### 6.4.2: Profile Settings
- [ ] Edit profile info: name, email, photo
- [ ] Edit job title, experience
- [ ] Edit skills (multi-select)
- [ ] Edit bio/summary
- [ ] Save and show success message

#### 6.4.3: Appearance Settings
- [ ] Theme selector: Light, Dark, System
- [ ] UI density: Comfortable, Compact
- [ ] Language selector (future i18n)
- [ ] Font size adjustment (accessibility)

#### 6.4.4: Notification Preferences (from Task 3.5.4)
- [ ] Toggle notifications per category
- [ ] Email notifications: Immediate, Daily digest, Off
- [ ] Push notifications toggle
- [ ] Sound/vibration settings
- [ ] Do Not Disturb schedule

#### 6.4.5: Privacy Settings
- [ ] Profile visibility (future multi-user)
- [ ] Search indexing opt-out
- [ ] Data sharing preferences
- [ ] Cookie preferences

#### 6.4.6: Account Settings
- [ ] Change password
- [ ] Two-factor authentication (future)
- [ ] Connected accounts (LinkedIn, Google)
- [ ] Active sessions list
- [ ] Log out all devices

#### 6.4.7: Data Management
- [ ] Export data (link to Task 6.3.4)
- [ ] Delete specific data types (applications, jobs)
- [ ] Delete account (with confirmation)
  - Warning: "This action cannot be undone"
  - Type account email to confirm
  - 30-day grace period before permanent deletion

#### 6.4.8: Keyboard Shortcuts
- [ ] Display keyboard shortcuts reference
- [ ] Searchable shortcut list
- [ ] Customize shortcuts (optional)

---

### Task 6.5: Final QA & Testing

#### 6.5.1: Cross-Browser Testing
- [ ] Test on Chrome (latest)
- [ ] Test on Firefox (latest)
- [ ] Test on Safari (latest)
- [ ] Test on Edge (latest)
- [ ] Document browser-specific issues
- [ ] Add browser compatibility notice if needed

#### 6.5.2: Mobile Device Testing
- [ ] Test on iOS Safari (iPhone)
  - Various screen sizes (SE, 13, 14, 15)
  - Test touch interactions
  - Test Safari-specific features (add to home screen)
- [ ] Test on Android Chrome
  - Various screen sizes
  - Test touch interactions
  - Test PWA features
- [ ] Test on tablet devices (iPad, Android tablet)
- [ ] Document mobile-specific issues

#### 6.5.3: Accessibility Final Audit
- [ ] Run automated accessibility audit (axe, WAVE)
- [ ] Manual keyboard navigation test
- [ ] Screen reader test (VoiceOver, NVDA)
- [ ] Color contrast check (WebAIM)
- [ ] Verify WCAG 2.1 AA compliance
- [ ] Document accessibility conformance

#### 6.5.4: Performance Final Audit
- [ ] Run Lighthouse on all main pages
  - Target: Performance > 95, Accessibility > 95, Best Practices > 95, SEO > 90
- [ ] Measure Core Web Vitals (FCP, LCP, CLS, FID)
- [ ] Test on slow 3G network
- [ ] Test with CPU throttling
- [ ] Document performance metrics

#### 6.5.5: Security Audit
- [ ] Check for XSS vulnerabilities
- [ ] Check for CSRF protection
- [ ] Review authentication flow
- [ ] Check API security (rate limiting, input validation)
- [ ] Review environment variable handling
- [ ] Check for exposed secrets
- [ ] Run security scanning tools (Snyk, npm audit)

#### 6.5.6: Functional Testing
- [ ] Test all user flows end-to-end
  - Sign up → Onboarding → Dashboard
  - Browse jobs → Save job → Apply
  - Track application → Update status
  - View analytics
- [ ] Test all forms (submit, validation, errors)
- [ ] Test all CRUD operations
- [ ] Test error scenarios (network failure, server error)

#### 6.5.7: User Acceptance Testing (UAT)
- [ ] Recruit beta testers (5-10 users)
- [ ] Provide testing checklist
- [ ] Collect feedback via survey
- [ ] Prioritize bugs and improvements
- [ ] Fix critical issues
- [ ] Document known issues

#### 6.5.8: Load Testing (Optional)
- [ ] Test with concurrent users (10, 50, 100)
- [ ] Test with large datasets (1000+ jobs, applications)
- [ ] Identify performance bottlenecks
- [ ] Optimize slow queries/endpoints

---

### Task 6.6: Documentation

#### 6.6.1: README Update
- [ ] Update `README.md` with:
  - Project description
  - Features list with screenshots
  - Tech stack
  - Quick start guide
  - Development setup
  - Deployment instructions
  - Contributing guidelines
  - License

#### 6.6.2: User Guide
- [ ] Create `docs/USER_GUIDE.md`
- [ ] Getting started section
- [ ] Feature walkthrough with screenshots
- [ ] Common tasks and workflows
- [ ] Tips and best practices
- [ ] Troubleshooting section

#### 6.6.3: Developer Documentation
- [ ] Create `docs/DEVELOPER_GUIDE.md`
- [ ] Project structure explanation
- [ ] Architecture overview
- [ ] Coding conventions
- [ ] Component patterns
- [ ] State management approach
- [ ] API integration guide
- [ ] Testing guidelines

#### 6.6.4: Component API Documentation
- [ ] Document all reusable components in Storybook
- [ ] Props table for each component
- [ ] Usage examples
- [ ] Accessibility notes
- [ ] Migration guide (old component → new component)

#### 6.6.5: Deployment Guide
- [ ] Create `docs/DEPLOYMENT.md`
- [ ] Environment variables setup
- [ ] Build process
- [ ] Deployment platforms (Vercel, Netlify, etc.)
- [ ] CI/CD pipeline setup
- [ ] Monitoring setup
- [ ] Rollback procedures

#### 6.6.6: Changelog
- [ ] Create `CHANGELOG.md`
- [ ] Document all major changes
- [ ] Follow semantic versioning
- [ ] Include migration notes for breaking changes

#### 6.6.7: Video Documentation
- [ ] Record demo video (3-5 minutes)
- [ ] Record developer setup video
- [ ] Upload to YouTube/Vimeo
- [ ] Link in README and docs

---

## Success Metrics

### Performance Targets
- [ ] Lighthouse Performance Score: 95+
- [ ] First Contentful Paint (FCP): <1.5s
- [ ] Largest Contentful Paint (LCP): <2.5s
- [ ] Time to Interactive (TTI): <3.5s
- [ ] Cumulative Layout Shift (CLS): <0.1
- [ ] Bundle size: <250KB (gzipped)

### Accessibility Targets
- [ ] WCAG 2.1 AA Compliance: 100%
- [ ] Keyboard navigation: 100% functional
- [ ] Screen reader compatible: 100%
- [ ] Color contrast ratio: >4.5:1 (AA) or >7:1 (AAA)

### Quality Targets
- [ ] Zero console errors in production
- [ ] Test coverage: >80%
- [ ] All components documented in Storybook
- [ ] All APIs typed with TypeScript
- [ ] Zero ESLint errors

---

## Notes

- Tasks marked with [frontend] require frontend development
- Tasks marked with [parallel] can be worked on simultaneously
- Tasks marked with [test] require manual testing after implementation
- Always commit after completing a logical unit of work
- Run `npm run quality:check` before committing
- Update this TODO.md as tasks are completed