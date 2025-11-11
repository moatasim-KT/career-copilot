# Implementation Plan

This implementation plan converts the TODO.md remaining tasks into actionable coding tasks.

## Phase 2: Visual Polish & Modern Design

- [x] 1. Implement Animation System
- [x] 1.1 Create animation library
  - Create `frontend/src/lib/animations.ts` with Framer Motion variants
  - Export fadeVariants, slideVariants, scaleVariants, staggerContainer
  - Export springConfigs and duration constants
  - _Requirements: 1.1_

- [x] 1.2 Add page transitions
  - Update `frontend/src/app/layout.tsx` with AnimatePresence
  - Implement route change transitions
  - _Requirements: 1.1_

- [x] 1.3 Enhance Button2 with micro-interactions
  - Update `frontend/src/components/ui/Button2.tsx` with motion wrapper
  - Add whileHover, whileTap, success state animations
  - _Requirements: 1.1_

- [x] 1.4 Enhance Card2 with animations
  - Update `frontend/src/components/ui/Card2.tsx` with hover lift
  - Add entrance and stagger animations
  - _Requirements: 1.1_

- [x] 1.5 Add list animations to JobsPage
  - Update `frontend/src/components/pages/JobsPage.tsx`
  - Implement stagger animation for job list items
  - Animate filtering/sorting changes
  - _Requirements: 1.1_

- [x] 1.6 Add list animations to ApplicationsPage
  - Update `frontend/src/components/pages/ApplicationsPage.tsx`
  - Implement stagger animation for application cards
  - Animate status changes with color transitions
  - _Requirements: 1.1_

- [x] 1.7 Add form input animations
  - Update all input components with focus animations
  - Add border color transitions and label slide animations
  - Implement error message slide down with shake effect
  - _Requirements: 1.1_

- [x] 1.8 Enhance modal/dialog animations
  - Update Modal2 component with backdrop fade and content scale
  - Add slide-in from bottom on mobile
  - Update Drawer component with slide animations
  - _Requirements: 1.1_

- [x] 1.9 Add loading state transitions
  - Implement skeleton to content crossfade
  - Add stagger reveal for multiple items
  - Create smooth spinner with easing curves
  - _Requirements: 1.1_

- [x] 2. Complete Dark Mode Implementation
- [x] 2.1 Create useDarkMode hook
  - Create `frontend/src/hooks/useDarkMode.ts`
  - Implement localStorage persistence with 'theme' key
  - Read system preference with prefers-color-scheme
  - Priority: localStorage > system > default (light)
  - Return isDark, toggle, setDark, setLight, setSystem functions
  - Emit storage event for cross-tab synchronization
  - _Requirements: 1.3, 1.4_

- [x] 2.2 Create ThemeToggle component
  - Create `frontend/src/components/ui/ThemeToggle.tsx`
  - Implement Sun/Moon icon toggle with lucide-react
  - Add smooth icon transition animation using Framer Motion
  - Add accessible button with ARIA label "Toggle theme"
  - Add tooltip showing "Toggle theme (⌘/Ctrl + D)"
  - Implement keyboard shortcut support
  - _Requirements: 1.3, 1.4_

- [x] 2.3 Update app layout for dark mode
  - Update `frontend/src/app/layout.tsx`
  - Add suppressHydrationWarning to html tag
  - Add inline script in head to prevent flash of wrong theme
  - Apply 'dark' class to html element based on preference
  - Add ThemeToggle to Navigation component
  - _Requirements: 1.3, 1.4_

- [x] 2.4 Add dark mode CSS transitions
  - Update `frontend/src/app/globals.css`
  - Add transition for background-color, border-color, color (200ms)
  - Exclude animations, transforms, opacity from transition
  - Test smooth theme switching
  - _Requirements: 1.3, 1.4_

- [x] 2.5 Audit and update Navigation component
  - Update `frontend/src/components/layout/Navigation.tsx`
  - Replace remaining hard-coded colors with design tokens
  - Add dark mode classes: dark:bg-neutral-900, dark:border-neutral-800
  - Test active states in both themes
  - _Requirements: 1.3, 1.4_

- [x] 2.6 Update Dashboard for dark mode
  - Update `frontend/src/components/pages/Dashboard.tsx`
  - Add dark:bg-neutral-800 to card backgrounds
  - Update stat cards with proper dark contrast
  - Ensure chart colors work in dark theme
  - _Requirements: 1.3, 1.4_

- [x] 2.7 Update all form components for dark mode
  - Update Input2, Select2, MultiSelect2, Textarea2, DatePicker2
  - Add dark:bg-neutral-800, dark:border-neutral-700
  - Add dark:placeholder-neutral-500
  - Test focus rings in dark mode
  - _Requirements: 1.3, 1.4_

- [x] 2.8 Update table components for dark mode
  - Update JobTableView and DataTable components
  - Add dark:bg-neutral-800 to headers
  - Add dark:hover:bg-neutral-700 to rows
  - Add dark:border-neutral-700 to borders
  - _Requirements: 1.3, 1.4_

- [x] 2.9 Test dark mode across all pages
  - Test Dashboard, Jobs, Applications, Recommendations, Analytics
  - Test all modals and popovers
  - Test forms and inputs
  - Verify color contrast with WebAIM Contrast Checker (min 4.5:1)
  - Test automatic theme switching based on system preference
  - _Requirements: 1.3, 1.4_

- [ ] 3. Add Gradient & Visual Enhancements
- [x] 3.1 Update dashboard hero with gradient
  - Update dashboard header section
  - Apply gradient-mesh background from globals.css
  - Ensure text contrast on gradient (min 4.5:1)
  - Test in both light and dark modes
  - _Requirements: 1.5_

- [x] 3.2 Create gradient mesh variations
  - Add gradient-mesh-blue, gradient-mesh-purple, gradient-mesh-green to globals.css
  - Document variations in Storybook design tokens
  - _Requirements: 1.5_

- [x] 3.3 Apply glass morphism effects
  - Apply .glass utility to modal backdrops
  - Apply to popover backgrounds
  - Apply to floating action buttons
  - Apply to sticky navigation when scrolled
  - Test readability with backdrop-blur
  - _Requirements: 1.5_

- [x] 3.4 Enhance Card2 with hover effects
  - Add smooth shadow expansion on hover
  - Add glow effect for featured/premium cards
  - Add gradientBorder prop option using before pseudo-element
  - Test all card variants
  - _Requirements: 1.5_

- [x] 3.5 Add button glow effects
  - Add glow effect to primary CTAs (box-shadow with primary color)
  - Increase glow on hover
  - Add pulse animation for critical actions
  - Create gradient button variant
  - _Requirements: 1.5_

- [x] 3.6 Create SVG pattern library
  - Create `frontend/public/patterns/` directory
  - Create dot-grid.svg pattern
  - Create line-pattern.svg
  - Create wave-pattern.svg
  - Apply to empty state components at 5-10% opacity
  - _Requirements: 1.5_

- [x] 3.7 Add accent color highlights
  - Add colored left/bottom border to active navigation items
  - Add smooth transition
  - Create colored status indicators with glow (success, warning, error)
  - Add pulse animation to status dots
  - _Requirements: 1.5_

- [ ] 4. Refine Responsive Design
- [ ] 4.1 Mobile audit and fixes (320px-480px)
  - Test on iPhone SE (375x667) and small Android (360x640)
  - Fix navigation hamburger menu functionality
  - Ensure logo size appropriate on small screens
  - Stack dashboard cards vertically
  - Reduce padding on small screens
  - Ensure tap targets are minimum 44x44px
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 4.2 Update forms for mobile
  - Stack form fields vertically on mobile
  - Full-width inputs
  - Larger input heights for touch (min 44px)
  - Proper input types (email, tel, number) for mobile keyboards
  - Test all forms on mobile devices
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 4.3 Enhance mobile navigation
  - Update `frontend/src/components/layout/Navigation.tsx`
  - Improve hamburger menu animation (slide in from right)
  - Add backdrop overlay when menu open
  - Close menu on navigation
  - Add close button (X) in mobile menu
  - Test on all mobile breakpoints
  - _Requirements: 2.1, 2.2_

- [ ] 4.4 Make tables responsive
  - Update `frontend/src/components/pages/JobTableView.tsx`
  - Add horizontal scroll for tables on mobile
  - Alternatively: Switch to card view on mobile (<768px)
  - Add "View as: Table | Cards" toggle
  - Add sticky table headers on desktop
  - _Requirements: 2.1, 2.4_

- [ ] 4.5 Optimize touch targets
  - Audit all interactive elements for minimum 44x44px
  - Add padding to links if needed
  - Ensure checkboxes/radios are 44x44px
  - Add @media (hover: none) styles for touch devices
  - Remove hover states on touch, add active/pressed states
  - _Requirements: 2.2_

- [ ] 4.6 Create responsive typography scale
  - Update typography to use responsive classes
  - H1: text-2xl md:text-4xl (28px → 48px)
  - H2: text-xl md:text-3xl (24px → 36px)
  - H3: text-lg md:text-2xl (20px → 28px)
  - Test readability on all screen sizes
  - _Requirements: 2.1_

## Phase 3: Advanced Features

- [x] 5. Implement Command Palette
- [x] 5.1 Create command registry
  - Create `frontend/src/lib/commands.ts`
  - Define Command interface with id, label, category, icon, keywords, action, shortcut
  - Create commandRegistry array with navigation commands (Dashboard, Jobs, Applications, etc.)
  - Add action commands (Create Job, Create Application, etc.)
  - Add settings commands (Toggle theme, Open settings, etc.)
  - Export getCommands() function
  - _Requirements: 3.1, 3.2_

- [x] 5.2 Create keyboard shortcut hook
  - Create `frontend/src/hooks/useKeyboardShortcut.ts`
  - Listen for keyboard events with useEffect
  - Handle platform differences (Cmd on Mac, Ctrl on Windows/Linux)
  - Support modifiers: ctrl, meta, shift, alt
  - Prevent default browser behavior
  - Return cleanup function
  - _Requirements: 3.1, 3.2_

- [x] 5.3 Create CommandPalette component
  - Create `frontend/src/components/ui/CommandPalette.tsx`
  - Use cmdk library (Command component)
  - Implement modal-style overlay with backdrop blur
  - Add search input at top with search icon
  - Implement fuzzy search across commands using keywords
  - Add keyboard navigation (arrow keys, enter, escape)
  - Group results by category
  - Show command icons and keyboard shortcuts
  - Style to match Linear/Raycast/Spotlight
  - _Requirements: 3.1, 3.2_

- [x] 5.4 Add dynamic search for jobs and applications
  - Implement debounced API search (300ms delay)
  - Query jobs from API when user types
  - Query applications from API
  - Show results in separate groups
  - Click to navigate to detail page
  - _Requirements: 3.1, 3.2_

- [x] 5.5 Implement recent searches and commands
  - Store recent searches in localStorage (last 10)
  - Show at top when palette opens (before typing)
  - Track command usage frequency
  - Sort by recency
  - Add clear history button
  - _Requirements: 3.1, 3.2_

- [x] 5.6 Integrate CommandPalette globally
  - Add CommandPalette to `frontend/src/app/layout.tsx`
  - Use useKeyboardShortcut for ⌘K/Ctrl+K
  - Toggle palette visibility
  - Close palette after command execution
  - Add toast notification for command feedback
  - Show keyboard hint in UI: "Press ⌘K to search"
  - _Requirements: 3.1, 3.2_

- [x] 5.7 Style and polish CommandPalette
  - Apply glass morphism backdrop
  - Add smooth fade in/out animations
  - Style input with focus ring
  - Add hover state for results
  - Add keyboard-selected item highlight (different from hover)
  - Add keyboard shortcut hints (e.g., "↵ Enter" to select)
  - Test accessibility with screen readers
  - _Requirements: 3.1, 3.2_

- [x] 6. Implement Advanced Search System
- [x] 6.1 Create SearchRule and SearchGroup interfaces
  - Create `frontend/src/types/search.ts`
  - Define SearchRule interface (id, field, operator, value)
  - Define SearchGroup interface (id, logic AND/OR, rules, nested groups)
  - Define SearchField interface (name, label, type, operators)
  - Export types
  - _Requirements: 3.3_

- [x] 6.2 Create QueryBuilder component
  - Create `frontend/src/components/features/QueryBuilder.tsx`
  - Implement visual tree structure for rules and groups
  - Add rule button with field selector
  - Add group button for nested logic
  - Implement AND/OR toggle for groups
  - Add remove buttons for rules and groups
  - Support nested groups (recursive rendering)
  - _Requirements: 3.3_

- [x] 6.3 Create field-specific operator and value inputs
  - Create operator selector based on field type
  - Text fields: contains, equals, starts with, ends with
  - Number fields: equals, gt, lt, between
  - Date fields: before, after, between, in last X days
  - Boolean fields: is, is not
  - Create value input components for each field type
  - Add validation for value inputs
  - _Requirements: 3.3_

- [x] 6.4 Create AdvancedSearch component
  - Create `frontend/src/components/features/AdvancedSearch.tsx`
  - Implement slide-out panel or modal
  - Integrate QueryBuilder component
  - Add live preview of results count
  - Add "Apply search" button
  - Add "Clear all" button
  - Add "Save search" button
  - _Requirements: 3.3_

- [x] 6.5 Implement saved searches
  - Create SavedSearches component
  - Implement save search dialog (prompt for name)
  - Save to backend API and localStorage
  - Create saved searches dropdown
  - Implement load, edit, delete operations
  - Add "Saved searches" section in sidebar
  - _Requirements: 3.3_

- [x] 6.6 Implement recent searches
  - Track recent searches in localStorage (last 10)
  - Include search criteria and result count
  - Show in dropdown
  - Add clear history button
  - _Requirements: 3.3_

- [x] 6.7 Create filter chips display
  - Show active filters as chips above results
  - Format: "Field: value"
  - Add X button to remove filter
  - Click chip to edit filter
  - Add "Clear all filters" button
  - Show filter count badge
  - _Requirements: 3.3_

- [x] 6.8 Integrate AdvancedSearch with JobsPage
  - Add AdvancedSearch to `frontend/src/components/pages/JobsPage.tsx`
  - Add "Advanced Search" button
  - Apply search to job list query
  - Update URL with search params
  - Show active filters as chips
  - Test various search combinations
  - _Requirements: 3.3_

- [x] 6.9 Integrate AdvancedSearch with ApplicationsPage
  - Add AdvancedSearch to `frontend/src/components/pages/ApplicationsPage.tsx`
  - Add "Advanced Search" button
  - Apply search to applications query
  - Update URL with search params
  - Show active filters as chips
  - Test search functionality
  - _Requirements: 3.3_

- [-] 7. Implement Bulk Operations
- [x] 7.1 Create BulkActionBar component
  - Create `frontend/src/components/ui/BulkActionBar.tsx`
  - Implement fixed position bar at bottom of screen
  - Add slide up animation when items selected
  - Show selection count: "X items selected"
  - Add action buttons based on context
  - Add cancel selection button
  - Style with backdrop blur and shadow
  - _Requirements: 3.4_

- [x] 7.2 Define bulk actions for jobs
  - Create bulk action definitions for job listings
  - Archive selected jobs
  - Add to wishlist/saved
  - Export to CSV
  - Mark as viewed/unviewed
  - Implement action handlers with API calls
  - Add optimistic UI updates
  - _Requirements: 3.4_

- [x] 7.3 Define bulk actions for applications
  - Create bulk action definitions for applications
  - Change status (dropdown: Applied, Interviewing, Offer, Rejected, Accepted)
  - Delete selected applications
  - Export to CSV
  - Archive selected applications
  - Implement action handlers
  - _Requirements: 3.4_

- [x] 7.4 Create confirmation dialogs for destructive actions
  - Create ConfirmBulkAction component
  - Show "Delete X applications?" with warning
  - List items to be affected (first 5, then "and X more")
  - Add destructive confirm button (red)
  - Add cancel button
  - Add "Don't ask again" checkbox (store preference)
  - _Requirements: 3.4_

- [x] 7.5 Implement bulk operation progress
  - Create progress indicator for long-running operations
  - Show progress bar or circular spinner
  - Display status text: "Processing X of Y items..."
  - Add cancel button if possible
  - Show success/failure summary
  - Show errors for failed items with retry button
  - _Requirements: 3.4_

- [x] 7.6 Implement undo functionality
  - Add undo for non-destructive bulk actions
  - Show toast notification with "Undo" button
  - Set undo timeout to 5 seconds
  - Store previous state temporarily
  - Test undo for status changes, archive, etc.
  - _Requirements: 3.4_

- [x] 7.7 Integrate bulk operations with DataTable
  - Ensure DataTable row selection works (already implemented in Phase 3)
  - Add BulkActionBar when items selected
  - Pass selected IDs to bulk actions
  - Clear selection after action completion
  - Test with 1, 10, 100+ items
  - _Requirements: 3.4_

- [x] 8. Enhance Notification System
- [x] 8.1 Update notification data model
  - Update Notification interface with category field
  - Categories: system, job_alert, application, recommendation, social
  - Add category badges with icons
  - Add actionUrl and actionLabel fields
  - _Requirements: 3.5, 4.4_

- [x] 8.2 Create NotificationCenter component
  - Create `frontend/src/components/ui/NotificationCenter.tsx`
  - Add bell icon in Navigation header
  - Add badge with unread count
  - Implement dropdown panel when clicked
  - Show list of recent notifications (last 20)
  - Add "View all" link to full notification page
  - Style notification items with icon, title, description, timestamp
  - Add read/unread indicator
  - Click to navigate or dismiss
  - _Requirements: 3.5, 4.4_

- [x] 8.3 Create notification history page
  - Create `frontend/src/app/notifications/page.tsx`
  - Show full list of all notifications
  - Add filters: All, Unread, by Category
  - Add search notifications
  - Implement pagination
  - Add bulk actions: Mark all as read, Delete all
  - _Requirements: 3.5, 4.4_

- [x] 8.4 Create NotificationPreferences component
  - Create `frontend/src/components/settings/NotificationPreferences.tsx`
  - Add toggle per category
  - Add email notification settings (immediate, daily digest, off)
  - Add push notification toggle
  - Add sound/vibration settings
  - Add Do Not Disturb schedule (optional)
  - Save preferences to backend API
  - _Requirements: 3.5, 4.4_

- [x] 8.5 Implement browser push notifications
  - Request notification permission on first visit or in settings
  - Show benefits of enabling notifications
  - Implement Web Push API with service worker
  - Register and store subscription on backend
  - Add "Send test notification" button in settings
  - Handle notification click to navigate to relevant page
  - _Requirements: 3.5, 4.4_

- [x] 8.6 Create notification templates
  - Create notification template system
  - Job match: "New job: {jobTitle} at {company}"
  - Application update: "Your application for {jobTitle} status changed to {status}"
  - Interview scheduled: "Interview scheduled for {jobTitle} on {date}"
  - Recommendation: "We found {count} jobs matching your profile"
  - Support rich content (links, buttons)
  - _Requirements: 3.5, 4.4_

- [x] 8.7 Implement mark as read/unread
  - Add "Mark as read" action to notifications
  - Auto-mark as read when viewing notification detail
  - Add "Mark all as read" button
  - Update unread count badge immediately
  - _Requirements: 3.5, 4.4_

- [x] 8.8 Add inline notification actions
  - Add "View job" button to job notifications
  - Add "View application" button to application notifications
  - Add "Dismiss" button
  - Add "Remind me later" (snooze) button
  - Execute actions without leaving current page
  - _Requirements: 3.5, 4.4_

## Phase 4: Performance Optimization

- [ ] 9. Implement Code Splitting
- [-] 9.1 Audit current bundle size
  - Run `npm run build` and note bundle sizes
  - Run `ANALYZE=true npm run build` to generate bundle analysis
  - Identify large chunks (>200KB)
  - Document route bundle sizes
  - _Requirements: 6.4_

- [x] 9.2 Implement component-level code splitting
  - Identify heavy components for lazy loading (charts, rich editors, etc.)
  - Wrap with React.lazy() and Suspense
  - Create loading fallback components
  - Test functionality after splitting
  - _Requirements: 6.4_

- [x] 9.3 Implement dynamic imports for conditional features
  - Identify conditionally used features (modals, dialogs, etc.)
  - Convert to dynamic imports
  - Test all features still work
  - _Requirements: 6.4_

- [x] 9.4 Add preload for critical routes
  - Identify critical user paths (dashboard, jobs, applications)
  - Add router.prefetch() on link hover
  - Test preloading behavior
  - _Requirements: 6.4_

- [x] 9.5 Set bundle size budget alerts
  - Configure bundle size budgets in next.config.js
  - Set warning threshold at 200KB per route
  - Set error threshold at 250KB per route
  - Add to CI/CD pipeline
  - _Requirements: 6.4_

- [ ] 10. Optimize Images
- [x] 10.1 Migrate all img tags to Next.js Image
  - Audit all `<img>` tags in codebase
  - Replace with Next.js `<Image>` component
  - Add required props: width, height, alt
  - Test image loading
  - _Requirements: 6.4_

- [x] 10.2 Configure responsive images
  - Configure image sizes in next.config.js
  - Use `sizes` prop for responsive images
  - Test on different screen sizes
  - _Requirements: 6.4_

- [x] 10.3 Optimize image formats
  - Configure WebP format in next.config.js
  - Compress source images to <100KB
  - Test image quality
  - _Requirements: 6.4_

- [x] 10.4 Test image optimization
  - Test on slow 3G network
  - Verify blur placeholders appear
  - Check WebP format delivery in Network tab
  - _Requirements: 6.4_

- [ ] 11. Implement List Virtualization
- [x] 11.1 Create VirtualJobList component
  - Create `frontend/src/components/jobs/VirtualJobList.tsx`
  - Use @tanstack/react-virtual
  - Configure virtualizer with estimateSize
  - Set overscan to 5 items
  - Render only visible items
  - Test with 100+ jobs
  - _Requirements: 6.4_

- [x] 11.2 Create VirtualApplicationList component
  - Create `frontend/src/components/applications/VirtualApplicationList.tsx`
  - Implement virtualization similar to VirtualJobList
  - Test with 100+ applications
  - _Requirements: 6.4_

- [x] 11.3 Add virtualization to DataTable
  - Update DataTable component to support virtualization
  - Add virtualizer for rows when count > 100
  - Test with 1000+ rows
  - Measure FPS (target: 60fps)
  - _Requirements: 6.4_

- [x] 11.4 Performance testing
  - Benchmark rendering time before/after virtualization
  - Measure FPS during scrolling
  - Test on lower-end devices
  - Document performance improvements
  - _Requirements: 6.4_

- [x] 12. Optimize Caching & State Management
- [x] 12.1 Review and optimize React Query configuration
  - Review current queryClient configuration
  - Optimize staleTime and cacheTime per query type
  - Jobs list: staleTime 5 min, refetch on mount
  - Applications: staleTime 1 min, refetch on mount
  - User profile: staleTime 30 min, refetch on focus
  - Analytics: staleTime 10 min, no auto-refetch
  - Notifications: staleTime 30 sec, refetch on focus
  - _Requirements: 6.4, 6.5_

- [x] 12.2 Implement stale-while-revalidate pattern
  - Configure SWR for key data endpoints
  - Show cached data immediately while fetching fresh data
  - Test instant cached data display
  - _Requirements: 6.4, 6.5_

- [x] 12.3 Implement optimistic updates
  - Add optimistic updates for application status changes
  - Add optimistic updates for job saves/unsaves
  - Implement rollback on error
  - Test error scenarios
  - _Requirements: 6.4, 6.5_

- [x] 12.4 Implement prefetching
  - Add prefetch on hover for job/application cards
  - Prefetch next pagination page when near end
  - Test prefetching behavior
  - _Requirements: 6.4, 6.5_

- [x] 13. Setup Performance Monitoring
- [x] 13.1 Install and configure Lighthouse CI
  - Install @lhci/cli
  - Create lighthouserc.json configuration
  - Add npm script: "lighthouse": "lhci autorun"
  - Run initial audit
  - _Requirements: 6.4_

- [x] 13.2 Implement Web Vitals reporting
  - Create `frontend/src/lib/vitals.ts`
  - Implement reportWebVitals function
  - Send metrics to analytics (console.log for now)
  - Track FCP, LCP, FID, CLS, TTFB
  - _Requirements: 6.4_

- [x] 13.3 Define performance budgets
  - Document performance budgets
  - FCP < 1.5s, LCP < 2.5s, FID < 100ms, CLS < 0.1
  - Bundle size < 250KB gzipped
  - Lighthouse Performance score > 95
  - _Requirements: 6.4_

- [x] 13.4 Add Lighthouse to CI/CD
  - Create GitHub Actions workflow for Lighthouse
  - Run on every PR
  - Fail build if Performance score < 90
  - Post results as PR comment
  - _Requirements: 6.4_

## Phase 5: Advanced UX Patterns

- [x] 14. Create Onboarding Wizard
- [x] 14.1 Create OnboardingWizard component
  - Create `frontend/src/components/onboarding/OnboardingWizard.tsx`
  - Implement multi-step wizard with progress indicator
  - Add Next/Back/Skip buttons
  - Implement smooth transitions between steps
  - Save progress to backend to allow resume
  - _Requirements: 4.1, 4.2_

- [x] 14.2 Create Step 1: Welcome & Profile Setup
  - Create WelcomeStep component
  - Show value proposition
  - Collect name, email (pre-filled if signed in)
  - Add profile photo upload (optional)
  - Add job title/role input
  - Add years of experience dropdown (0-1, 1-3, 3-5, 5-10, 10+)
  - _Requirements: 4.1, 4.2_

- [x] 14.3 Create Step 2: Skills & Expertise
  - Create SkillsStep component
  - Implement multi-select skill tags
  - Show popular skills suggestions
  - Add search for skills
  - Allow adding custom skills
  - Add proficiency level per skill (optional)
  - _Requirements: 4.1, 4.2_

- [x] 14.4 Create Step 3: Resume Upload
  - Create ResumeStep component
  - Add file upload with drag & drop
  - Support PDF, DOCX formats
  - Parse resume with AI (optional, call backend)
  - Auto-fill skills from resume
  - Allow skip if no resume
  - _Requirements: 4.1, 4.2_

- [x] 14.5 Create Step 4: Job Preferences
  - Create PreferencesStep component
  - Add preferred job titles (multi-select)
  - Add preferred locations (city, state, or remote)
  - Add salary expectations (range slider)
  - Add work arrangement: Remote, Hybrid, On-site
  - Add company size preference (optional)
  - Add industry preference (optional)
  - _Requirements: 4.1, 4.2_

- [x] 14.6 Create Step 5: Feature Tour
  - Create FeatureTourStep component
  - Show interactive tour of key features
  - Highlight dashboard, jobs, applications
  - Show command palette (⌘K)
  - Show notification center
  - Add animated pointers and tooltips
  - _Requirements: 4.1, 4.2_

- [x] 14.7 Create completion screen
  - Create CompletionStep component
  - Show success animation
  - Display first recommended jobs
  - Add CTA buttons: "View Dashboard", "Browse Jobs"
  - Add option to retake onboarding in settings
  - _Requirements: 4.1, 4.2_

- [x] 14.8 Implement skip and resume logic
  - Allow skipping individual steps
  - Allow skipping entire onboarding
  - Save progress to backend after each step
  - Resume from last step if interrupted
  - Show onboarding progress in profile
  - _Requirements: 4.1, 4.2_

- [x] 15. Implement Data Visualization Charts
- [x] 15.1 Create ChartWrapper component
  - Create `frontend/src/components/charts/ChartWrapper.tsx`
  - Add consistent styling with design tokens
  - Add loading skeleton state
  - Add error state
  - Add export button
  - Add full-screen mode toggle
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.2 Create ApplicationStatusChart
  - Create `frontend/src/components/charts/ApplicationStatusChart.tsx`
  - Implement pie or donut chart using Recharts
  - Show status distribution (Applied, Interviewing, Offer, Rejected)
  - Add interactive tooltips with counts and percentages
  - Click slice to filter applications by status
  - Add smooth animations on load and data changes
  - Support dark mode
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.3 Create ApplicationTimelineChart
  - Create `frontend/src/components/charts/ApplicationTimelineChart.tsx`
  - Implement line chart showing applications over time
  - X-axis: dates, Y-axis: application count
  - Show trend line (optional)
  - Add hover tooltip with exact count and date
  - Add zoom/pan controls for large date ranges
  - Support dark mode
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.4 Create SalaryDistributionChart
  - Create `frontend/src/components/charts/SalaryDistributionChart.tsx`
  - Implement bar chart or histogram showing salary ranges
  - X-axis: salary buckets, Y-axis: job count
  - Highlight user's target salary range
  - Add interactive tooltips
  - Support dark mode
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.5 Create SkillsDemandChart
  - Create `frontend/src/components/charts/SkillsDemandChart.tsx`
  - Implement bar chart showing top skills in job postings
  - Compare with user's skills (overlay)
  - Clickable bars to filter jobs by skill
  - Sort by: frequency, match rate, trending
  - Support dark mode
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.6 Create SuccessRateChart
  - Create `frontend/src/components/charts/SuccessRateChart.tsx`
  - Implement funnel chart: Applied → Interviewed → Offer → Accepted
  - Show conversion rates at each stage
  - Benchmark against averages (optional)
  - Add interactive hover states
  - Support dark mode
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.7 Add chart interactivity
  - Add zoom/pan controls to time-series charts
  - Add legend toggle to show/hide datasets
  - Add data export button (CSV, PNG)
  - Add full-screen mode for detailed analysis
  - Ensure responsive charts (adapt to mobile)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.8 Integrate charts into Dashboard
  - Add charts to `frontend/src/components/pages/Dashboard.tsx`
  - Create chart grid layout (responsive)
  - Add chart loading skeletons
  - Test with real data
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 16. Implement WebSocket Real-time Updates
- [x] 16.1 Create WebSocket client
  - Create `frontend/src/lib/websocket.ts`
  - Implement WebSocketClient class
  - Connect to backend WebSocket server
  - Handle connection lifecycle (open, close, error)
  - Implement auto-reconnect with exponential backoff
  - Implement event subscription system
  - Implement message queue for offline mode
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 16.2 Create ConnectionStatus component
  - Create `frontend/src/components/ui/ConnectionStatus.tsx`
  - Show small indicator in Navigation header
  - States: Connected (green), Connecting (yellow), Disconnected (red)
  - Add tooltip with status message
  - Add manual reconnect button
  - _Requirements: 5.1, 5.4_

- [x] 16.3 Implement real-time job recommendations
  - Listen for `job:recommendation` WebSocket events
  - Show toast notification when new job matches
  - Update jobs list in real-time without page refresh
  - Add badge on Jobs tab: "X new matches"
  - Add smooth animation for new items appearing
  - _Requirements: 5.1, 5.2_

- [x] 16.4 Implement real-time application status updates
  - Listen for `application:status_change` events
  - Update application status in UI instantly
  - Show toast notification: "Application status changed to {status}"
  - Update dashboard stats in real-time
  - Add badge animation for status change
  - _Requirements: 5.1, 5.3_

- [x] 16.5 Implement real-time notifications
  - Listen for `notification:new` events
  - Display toast notification
  - Update notification bell badge count
  - Add to notification center list
  - Play sound (with user preference)
  - _Requirements: 5.1, 5.2_

- [x] 16.6 Handle reconnection and offline mode
  - Detect network offline/online events
  - Show reconnecting toast
  - Retry connection with exponential backoff
  - Resync data on reconnect (fetch latest)
  - Handle message queue for missed events
  - _Requirements: 5.1, 5.4_

- [x] 16.7 Test WebSocket functionality
  - Test real-time updates in multiple browser tabs
  - Test reconnection after network disruption
  - Test on mobile devices
  - Test with slow network
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 17. Implement Drag & Drop Features
- [x] 17.1 Create draggable dashboard widgets
  - Update Dashboard component to use @dnd-kit
  - Make dashboard cards/widgets draggable
  - Allow reordering widgets
  - Save widget layout to user preferences
  - Add "Reset layout" button
  - Add visual feedback during drag (ghost element, drop zones)
  - _Requirements: 4.1_

- [x] 17.2 Create Kanban board for applications
  - Create `frontend/src/components/pages/ApplicationKanban.tsx`
  - Create columns: Applied, Interviewing, Offer, Rejected
  - Make application cards draggable between columns
  - Update status on drop (with API call)
  - Implement optimistic update + rollback on error
  - Add smooth animations
  - _Requirements: 4.1_

- [x] 17.3 Add drag-to-reorder for lists
  - Add drag-to-reorder for custom job lists
  - Add drag-to-reorder for saved searches
  - Save order to backend
  - Add visual feedback (drag handle, drop indicator)
  - _Requirements: 4.1_

- [x] 17.4 Add keyboard support for drag & drop
  - Implement keyboard navigation for drag & drop
  - Space to pick up, arrow keys to move, Enter to drop
  - Announce drag/drop actions to screen readers
  - Add ARIA live regions for status updates
  - _Requirements: 4.1_

- [x] 17.5 Test drag & drop functionality
  - Test on desktop browsers
  - Test touch drag on mobile/tablet
  - Test keyboard navigation
  - Test with screen reader
  - _Requirements: 4.1_

## Phase 6: Production Readiness

- [ ] 18. Enhance Error Handling
- [ ] 18.1 Create error handling utility
  - Create `frontend/src/lib/errorHandling.ts`
  - Implement classifyError function (network, auth, server, client, unknown)
  - Implement getErrorMessage function for user-friendly messages
  - Implement shouldRetry function
  - Implement retry with exponential backoff
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 18.2 Update API client with error interceptor
  - Update unified API client to intercept errors
  - Classify errors and show appropriate toast notifications
  - Network error: "Connection lost. Retrying..."
  - 401: "Session expired. Please log in."
  - 403: "You don't have permission for this action."
  - 404: "Resource not found."
  - 500: "Server error. Please try again later."
  - _Requirements: 8.1, 8.2_

- [ ] 18.3 Enhance ErrorBoundary component
  - Update `frontend/src/components/ErrorBoundary.tsx`
  - Show user-friendly error UI (not technical stack trace)
  - Add "Retry" button to re-render component
  - Add "Report issue" button (send error to backend/Sentry)
  - Different error UIs for different error types
  - _Requirements: 8.1, 8.4, 8.5_

- [ ] 18.4 Implement offline mode detection
  - Listen for `online`/`offline` browser events
  - Show offline banner at top of page
  - Disable actions that require network
  - Cache data for offline viewing (Service Worker)
  - Show cached data indicator
  - _Requirements: 8.1, 8.3_

- [ ] 18.5 Create custom error pages
  - Create `frontend/src/app/404/page.tsx` (Not Found)
  - Friendly message, helpful links, search bar
  - Create `frontend/src/app/500/page.tsx` (Server Error)
  - Friendly message, retry button, contact support link
  - Create `frontend/src/app/error.tsx` (Next.js error handling)
  - _Requirements: 8.1, 8.4_

- [ ] 18.6 Implement graceful degradation
  - Identify non-critical features
  - Degrade gracefully if feature fails (don't crash entire app)
  - Show fallback UI or hide feature
  - Log non-critical errors without alerting user
  - _Requirements: 8.1, 8.4_

- [ ] 18.7 Configure Sentry error monitoring
  - Verify Sentry configuration in `frontend/src/app/layout.tsx`
  - Set up source maps for production
  - Add user context to error reports
  - Set up error alerting rules
  - Test error reporting
  - _Requirements: 8.5_

- [x] 19. Implement Help & Documentation System
- [x] 19.1 Create useFirstTimeHint hook
  - Create `frontend/src/hooks/useFirstTimeHint.ts`
  - Track which features user has seen (localStorage)
  - Show tooltip on first interaction
  - Add "Got it" button to dismiss permanently
  - _Requirements: 4.3, 4.4_

- [x] 19.2 Create HelpIcon component
  - Create `frontend/src/components/ui/HelpIcon.tsx`
  - Small "?" icon next to complex features
  - Popover with explanation on hover/click
  - Link to full documentation
  - Consistent styling
  - _Requirements: 4.3, 4.4_

- [x] 19.3 Create FeatureTour modal
  - Create `frontend/src/components/help/FeatureTour.tsx`
  - Multi-step modal explaining key features
  - Add screenshots or GIFs
  - Add navigation: Next, Previous, Skip
  - Accessible via Help menu
  - _Requirements: 4.3, 4.4_

- [x] 19.4 Create Help Center page
  - Create `frontend/src/app/help/page.tsx`
  - Organize by categories: Getting Started, Features, Troubleshooting
  - Implement searchable FAQ
  - Use accordion-style Q&A
  - Add links to video tutorials
  - _Requirements: 4.3, 4.4_

- [x] 19.5 Add contextual help to features
  - Add help text to complex forms
  - Add tooltips to unclear buttons/icons
  - Add "Learn more" links to documentation
  - Add examples/placeholders in inputs
  - _Requirements: 4.3, 4.4_

- [x] 19.6 Create feedback widget
  - Add feedback button in footer or settings
  - Simple form: Rating, Comment, Screenshot option
  - Send to backend for review
  - Show thank you message after submission
  - _Requirements: 4.3, 4.4_

- [ ] 20. Implement Export & Import Features
- [ ] 20.1 Create CSV export utility
  - Create `frontend/src/lib/export/exportToCSV.ts`
  - Implement data to CSV conversion
  - Escape special characters (commas, quotes)
  - Trigger download with proper filename
  - _Requirements: 9.1, 9.2_

- [ ] 20.2 Create PDF export utility
  - Install jspdf and jspdf-autotable
  - Create `frontend/src/lib/export/exportToPDF.ts`
  - Generate PDF with table layout
  - Include logo, title, date
  - Proper formatting and styling
  - Trigger download
  - _Requirements: 9.1, 9.2_

- [ ] 20.3 Add export to applications page
  - Add "Export" dropdown button to ApplicationsPage
  - Options: Current view (CSV), All data (CSV), Selected rows (CSV), PDF
  - Show export progress for large datasets
  - Show success toast
  - _Requirements: 9.1, 9.2_

- [ ] 20.4 Add export to jobs page
  - Add "Export" dropdown button to JobsPage
  - Options: Current view, All data, Selected rows, PDF
  - Include relevant job data
  - _Requirements: 9.1, 9.2_

- [ ] 20.5 Create full data backup feature
  - Add "Export all data" in settings
  - Generate JSON file with all user data (profile, applications, saved jobs, preferences)
  - Compressed zip file if large
  - Encrypt sensitive data (optional)
  - _Requirements: 9.1, 9.5_

- [ ] 20.6 Create data import component
  - Create `frontend/src/components/features/DataImport.tsx`
  - Upload CSV file
  - Parse and validate CSV
  - Preview import (first 5 rows)
  - Map columns to fields
  - Bulk import with progress indicator
  - Show success/error summary
  - _Requirements: 9.3, 9.4_

- [ ] 20.7 Add CSV import to jobs page
  - Add "Import jobs" button
  - Use DataImport component
  - Provide CSV template download link
  - Include example data in template
  - _Requirements: 9.3, 9.4_

- [ ] 20.8 Create data restore feature
  - Add "Restore from backup" in settings
  - Upload backup JSON file
  - Validate file structure
  - Preview what will be restored
  - Restore data with confirmation
  - Show restore progress and summary
  - _Requirements: 9.5, 9.6_

- [ ] 21. Create Settings System
- [ ] 21.1 Create settings layout
  - Create `frontend/src/app/settings/layout.tsx`
  - Implement sidebar navigation
  - Categories: Profile, Appearance, Notifications, Privacy, Account, Data
  - Responsive: drawer on mobile
  - _Requirements: 10.1, 10.2_

- [ ] 21.2 Create Profile settings page
  - Create `frontend/src/app/settings/profile/page.tsx`
  - Edit profile info: name, email, photo
  - Edit job title, experience
  - Edit skills (multi-select)
  - Edit bio/summary
  - Save button with success message
  - _Requirements: 10.1, 10.2_

- [ ] 21.3 Create Appearance settings page
  - Create `frontend/src/app/settings/appearance/page.tsx`
  - Theme selector: Light, Dark, System
  - UI density: Comfortable, Compact
  - Language selector (future i18n)
  - Font size adjustment (accessibility)
  - _Requirements: 10.1, 10.2_

- [ ] 21.4 Create Notifications settings page
  - Create `frontend/src/app/settings/notifications/page.tsx`
  - Integrate NotificationPreferences component (from task 8.4)
  - Toggle per category
  - Email notifications: Immediate, Daily digest, Off
  - Push notifications toggle
  - Sound/vibration settings
  - Do Not Disturb schedule
  - _Requirements: 10.1, 10.3_

- [ ] 21.5 Create Privacy settings page
  - Create `frontend/src/app/settings/privacy/page.tsx`
  - Profile visibility (future multi-user)
  - Search indexing opt-out
  - Data sharing preferences
  - Cookie preferences
  - _Requirements: 10.1_

- [ ] 21.6 Create Account settings page
  - Create `frontend/src/app/settings/account/page.tsx`
  - Change password form
  - Two-factor authentication (future)
  - Connected accounts (LinkedIn, Google)
  - Active sessions list
  - Log out all devices button
  - _Requirements: 10.1_

- [ ] 21.7 Create Data settings page
  - Create `frontend/src/app/settings/data/page.tsx`
  - Link to export data (from task 20.5)
  - Delete specific data types (applications, jobs)
  - Delete account section with confirmation
  - Warning: "This action cannot be undone"
  - Type account email to confirm
  - 30-day grace period before permanent deletion
  - _Requirements: 10.1, 10.4_

- [ ] 21.8 Create keyboard shortcuts reference
  - Create `frontend/src/app/settings/shortcuts/page.tsx`
  - Display all keyboard shortcuts
  - Searchable shortcut list
  - Grouped by category
  - Customize shortcuts (optional)
  - _Requirements: 10.5_

- [ ] 22. Comprehensive Testing & QA
- [ ] 22.1 Cross-browser testing
  - Test on Chrome (latest)
  - Test on Firefox (latest)
  - Test on Safari (latest)
  - Test on Edge (latest)
  - Document browser-specific issues
  - Add browser compatibility notice if needed
  - _Requirements: 11.3_

- [ ] 22.2 Mobile device testing
  - Test on iOS Safari (iPhone SE, 13, 14, 15)
  - Test touch interactions
  - Test Safari-specific features (add to home screen)
  - Test on Android Chrome (various screen sizes)
  - Test PWA features
  - Test on tablet devices (iPad, Android tablet)
  - Document mobile-specific issues
  - _Requirements: 11.4_

- [ ] 22.3 Accessibility final audit
  - Run automated accessibility audit (axe, WAVE)
  - Manual keyboard navigation test on all pages
  - Screen reader test (VoiceOver, NVDA)
  - Color contrast check with WebAIM (min 4.5:1)
  - Verify WCAG 2.1 AA compliance
  - Document accessibility conformance
  - _Requirements: 11.2_

- [ ] 22.4 Performance final audit
  - Run Lighthouse on all main pages
  - Target: Performance > 95, Accessibility > 95, Best Practices > 95, SEO > 90
  - Measure Core Web Vitals (FCP, LCP, CLS, FID)
  - Test on slow 3G network
  - Test with CPU throttling
  - Document performance metrics
  - _Requirements: 11.1_

- [ ] 22.5 Security audit
  - Check for XSS vulnerabilities
  - Check for CSRF protection
  - Review authentication flow
  - Check API security (rate limiting, input validation)
  - Review environment variable handling
  - Check for exposed secrets
  - Run security scanning tools (Snyk, npm audit)
  - _Requirements: 11.1_

- [ ] 22.6 Functional testing
  - Test all user flows end-to-end
  - Sign up → Onboarding → Dashboard
  - Browse jobs → Save job → Apply
  - Track application → Update status
  - View analytics
  - Test all forms (submit, validation, errors)
  - Test all CRUD operations
  - Test error scenarios (network failure, server error)
  - _Requirements: 11.1, 11.3, 11.4_

- [ ] 22.7 User acceptance testing
  - Recruit beta testers (5-10 users)
  - Provide testing checklist
  - Collect feedback via survey
  - Prioritize bugs and improvements
  - Fix critical issues
  - Document known issues
  - _Requirements: 11.1_

- [ ] 23. Documentation
- [ ] 23.1 Update README
  - Update `README.md` with project description
  - Add features list with screenshots
  - Document tech stack
  - Add quick start guide
  - Add development setup instructions
  - Add deployment instructions
  - Add contributing guidelines
  - Add license information
  - _Requirements: 11.5_

- [ ] 23.2 Create user guide
  - Create `docs/USER_GUIDE.md`
  - Add getting started section
  - Add feature walkthrough with screenshots
  - Document common tasks and workflows
  - Add tips and best practices
  - Add troubleshooting section
  - _Requirements: 11.5_

- [ ] 23.3 Create developer documentation
  - Create `docs/DEVELOPER_GUIDE.md`
  - Document project structure
  - Add architecture overview
  - Document coding conventions
  - Document component patterns
  - Document state management approach
  - Add API integration guide
  - Add testing guidelines
  - _Requirements: 11.5_

- [ ] 23.4 Document components in Storybook
  - Ensure all reusable components have Storybook stories
  - Add props table for each component
  - Add usage examples
  - Add accessibility notes
  - Add migration guide (old component → new component)
  - _Requirements: 11.5_

- [ ] 23.5 Create deployment guide
  - Create `docs/DEPLOYMENT.md`
  - Document environment variables setup
  - Document build process
  - Add deployment platforms guide (Vercel, Netlify, etc.)
  - Document CI/CD pipeline setup
  - Add monitoring setup instructions
  - Add rollback procedures
  - _Requirements: 11.5_

- [ ] 23.6 Create changelog
  - Create `CHANGELOG.md`
  - Document all major changes
  - Follow semantic versioning
  - Include migration notes for breaking changes
  - _Requirements: 11.5_

- [ ] 23.7 Record demo video
  - Record application demo video (3-5 minutes)
  - Record developer setup video
  - Upload to YouTube/Vimeo
  - Link in README and docs
  - _Requirements: 11.5_
