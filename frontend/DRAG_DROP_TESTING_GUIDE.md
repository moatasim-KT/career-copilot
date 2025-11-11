# Drag & Drop Testing Guide

This guide provides comprehensive testing instructions for the drag and drop functionality implemented in Task 17.

## Overview

The following drag and drop features have been implemented:

1. **Draggable Dashboard Widgets** - Reorder dashboard widgets
2. **Application Kanban Board** - Drag applications between status columns
3. **Draggable Lists** - Reorder saved searches and custom job lists
4. **Keyboard Support** - Full keyboard navigation for accessibility

## Testing Checklist

### 1. Desktop Browser Testing

#### Chrome (Latest)

- [ ] **Dashboard Widgets**
  - [ ] Hover over widget to see drag handle
  - [ ] Click and drag widget to reorder
  - [ ] Verify smooth animation during drag
  - [ ] Verify drop indicator shows target position
  - [ ] Verify layout persists after page refresh
  - [ ] Click "Reset Layout" button and verify default order restored

- [ ] **Application Kanban**
  - [ ] Drag application card between columns
  - [ ] Verify optimistic update (immediate UI change)
  - [ ] Verify toast notification on successful move
  - [ ] Verify rollback on API error (simulate by disconnecting network)
  - [ ] Drag card within same column (should not trigger API call)

- [ ] **Saved Searches List**
  - [ ] Hover over search item to see drag handle
  - [ ] Drag to reorder searches
  - [ ] Verify order persists after page refresh
  - [ ] Verify smooth animations

- [ ] **Custom Job Lists**
  - [ ] Hover over list item to see drag handle
  - [ ] Drag to reorder lists
  - [ ] Verify order persists after page refresh
  - [ ] Verify smooth animations

#### Firefox (Latest)

- [ ] Repeat all Chrome tests
- [ ] Verify drag handle visibility
- [ ] Verify animations work smoothly
- [ ] Check for any Firefox-specific issues

#### Safari (Latest)

- [ ] Repeat all Chrome tests
- [ ] Verify drag handle visibility
- [ ] Verify animations work smoothly
- [ ] Check for any Safari-specific issues

#### Edge (Latest)

- [ ] Repeat all Chrome tests
- [ ] Verify drag handle visibility
- [ ] Verify animations work smoothly
- [ ] Check for any Edge-specific issues

### 2. Touch Device Testing

#### iPad / Android Tablet

- [ ] **Dashboard Widgets**
  - [ ] Long press on widget to initiate drag
  - [ ] Drag widget to new position
  - [ ] Verify visual feedback during drag
  - [ ] Verify drop works correctly

- [ ] **Application Kanban**
  - [ ] Long press on application card
  - [ ] Drag between columns
  - [ ] Verify smooth touch interactions
  - [ ] Verify no accidental drags on tap

- [ ] **Saved Searches / Job Lists**
  - [ ] Long press to initiate drag
  - [ ] Drag to reorder
  - [ ] Verify touch feedback

#### iPhone / Android Phone

- [ ] Repeat all tablet tests on smaller screen
- [ ] Verify drag handle is large enough for touch (44x44px minimum)
- [ ] Verify no conflicts with scroll gestures
- [ ] Test in both portrait and landscape orientations

### 3. Keyboard Navigation Testing

#### Dashboard Widgets

- [ ] Tab to focus on first widget
- [ ] Press Space to pick up widget
- [ ] Verify screen reader announcement: "Picked up item..."
- [ ] Use Arrow keys (Up/Down) to move widget
- [ ] Press Enter to drop widget
- [ ] Verify screen reader announcement: "Item moved to new position"
- [ ] Tab to another widget and press Space
- [ ] Press Escape to cancel drag
- [ ] Verify screen reader announcement: "Drag cancelled..."

#### Application Kanban

- [ ] Tab to focus on first application card
- [ ] Press Space to pick up card
- [ ] Use Arrow keys to move between columns
- [ ] Press Enter to drop in new column
- [ ] Verify status update occurs
- [ ] Test cancelling with Escape key

#### Saved Searches / Job Lists

- [ ] Tab to focus on first item
- [ ] Press Space to pick up
- [ ] Use Arrow keys to reorder
- [ ] Press Enter to drop
- [ ] Verify order persists

### 4. Screen Reader Testing

#### VoiceOver (macOS/iOS)

- [ ] Enable VoiceOver (Cmd + F5)
- [ ] Navigate to draggable items
- [ ] Verify drag handle is announced with instructions
- [ ] Verify ARIA attributes are read correctly:
  - [ ] "Drag to reorder. Press Space to pick up..."
  - [ ] "Picked up item. Use arrow keys to move..."
  - [ ] "Item moved to new position"
- [ ] Verify live region announcements work
- [ ] Test complete drag and drop flow

#### NVDA (Windows)

- [ ] Enable NVDA
- [ ] Navigate to draggable items
- [ ] Verify drag handle is announced
- [ ] Verify ARIA attributes are read correctly
- [ ] Verify live region announcements work
- [ ] Test complete drag and drop flow

#### JAWS (Windows)

- [ ] Enable JAWS
- [ ] Navigate to draggable items
- [ ] Verify drag handle is announced
- [ ] Verify ARIA attributes are read correctly
- [ ] Verify live region announcements work
- [ ] Test complete drag and drop flow

### 5. Performance Testing

- [ ] **Large Lists (100+ items)**
  - [ ] Create 100+ saved searches
  - [ ] Verify drag performance is smooth (60fps)
  - [ ] Measure time to reorder items
  - [ ] Check for memory leaks

- [ ] **Dashboard with Many Widgets**
  - [ ] Add maximum number of widgets
  - [ ] Verify drag performance
  - [ ] Check for layout issues

- [ ] **Kanban with Many Applications**
  - [ ] Create 50+ applications
  - [ ] Drag between columns
  - [ ] Verify smooth performance
  - [ ] Check for API throttling

### 6. Edge Cases & Error Handling

- [ ] **Network Errors**
  - [ ] Disconnect network
  - [ ] Drag application in Kanban
  - [ ] Verify rollback occurs
  - [ ] Verify error toast is shown
  - [ ] Reconnect and verify retry works

- [ ] **Concurrent Updates**
  - [ ] Open app in two tabs
  - [ ] Drag item in tab 1
  - [ ] Verify tab 2 updates (if real-time sync implemented)

- [ ] **Browser Refresh During Drag**
  - [ ] Start dragging an item
  - [ ] Refresh page mid-drag
  - [ ] Verify no broken state

- [ ] **Rapid Dragging**
  - [ ] Quickly drag multiple items in succession
  - [ ] Verify all updates are processed
  - [ ] Verify no race conditions

### 7. Visual Feedback Testing

- [ ] **Drag Handle**
  - [ ] Verify appears on hover
  - [ ] Verify has proper cursor (grab/grabbing)
  - [ ] Verify visible in both light and dark mode
  - [ ] Verify focus ring appears on keyboard focus

- [ ] **Drag Overlay**
  - [ ] Verify ghost element appears during drag
  - [ ] Verify opacity is correct (90%)
  - [ ] Verify follows cursor/touch point

- [ ] **Drop Indicator**
  - [ ] Verify shows target position
  - [ ] Verify color/style is clear
  - [ ] Verify updates as drag moves

- [ ] **Animations**
  - [ ] Verify smooth transitions
  - [ ] Verify no jank or stuttering
  - [ ] Verify animations respect prefers-reduced-motion

### 8. Accessibility Compliance

- [ ] **WCAG 2.1 AA Compliance**
  - [ ] Color contrast meets 4.5:1 minimum
  - [ ] Focus indicators are visible
  - [ ] Keyboard navigation works completely
  - [ ] Screen reader support is comprehensive

- [ ] **ARIA Attributes**
  - [ ] `role="listitem"` on draggable items
  - [ ] `aria-grabbed` updates during drag
  - [ ] `aria-label` on drag handles
  - [ ] `aria-live="assertive"` on announcements
  - [ ] `tabindex="0"` on drag handles

- [ ] **Keyboard Instructions**
  - [ ] Instructions visible to all users
  - [ ] Instructions clear and concise
  - [ ] Instructions match actual behavior

## Test Results Template

```markdown
## Test Results - [Date]

**Tester:** [Name]
**Browser:** [Browser Name & Version]
**OS:** [Operating System]
**Device:** [Desktop/Tablet/Phone]

### Dashboard Widgets
- [ ] Pass / [ ] Fail - [Notes]

### Application Kanban
- [ ] Pass / [ ] Fail - [Notes]

### Saved Searches
- [ ] Pass / [ ] Fail - [Notes]

### Custom Job Lists
- [ ] Pass / [ ] Fail - [Notes]

### Keyboard Navigation
- [ ] Pass / [ ] Fail - [Notes]

### Screen Reader
- [ ] Pass / [ ] Fail - [Notes]

### Performance
- [ ] Pass / [ ] Fail - [Notes]

### Issues Found
1. [Issue description]
2. [Issue description]

### Recommendations
1. [Recommendation]
2. [Recommendation]
```

## Known Limitations

1. **Touch Devices**: Long press duration may vary by device
2. **Screen Readers**: Announcement timing may vary by screen reader
3. **Performance**: Large lists (1000+ items) may experience slowdown
4. **Browser Support**: IE11 not supported (uses modern APIs)

## Reporting Issues

When reporting issues, please include:

1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Browser/Device information**
5. **Screenshots/Videos** (if applicable)
6. **Console errors** (if any)

## Success Criteria

All drag and drop features are considered complete when:

- [ ] All desktop browsers pass tests
- [ ] Touch devices work correctly
- [ ] Keyboard navigation is fully functional
- [ ] Screen readers announce correctly
- [ ] Performance is acceptable (60fps)
- [ ] No critical bugs found
- [ ] WCAG 2.1 AA compliance achieved
