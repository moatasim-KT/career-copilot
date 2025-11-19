# Dashboard Customization Guide

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

## Overview

Career Copilot's customizable dashboard allows you to create a personalized workspace with widgets tailored to your job search needs. Drag, resize, and arrange widgets to build the perfect dashboard for tracking your applications, goals, and progress.

## Features

- **8 Customizable Widgets**: Choose from a variety of widgets
- **Drag-and-Drop**: Rearrange widgets with simple drag-and-drop
- **Resizable Widgets**: Adjust widget sizes to your preference
- **Layout Persistence**: Your layout is saved automatically
- **Responsive Design**: Adapts to desktop, tablet, and mobile screens
- **Quick Reset**: Restore default layout anytime

## Available Widgets

### 1. Application Status Overview
**Description**: Visual breakdown of your application statuses
- Displays total applications
- Color-coded status counts (Applied, In Progress, Interview, Offer, Rejected)
- Quick status summary

**Best For**: Getting a bird's-eye view of your job search progress

**Recommended Size**: Medium (6 columns × 4 rows)

### 2. Recent Job Listings
**Description**: Latest job opportunities matching your preferences
- Shows 5 most recent job postings
- Company name and location
- Posted time
- Quick "View" button

**Best For**: Staying updated on new opportunities

**Recommended Size**: Medium (6 columns × 4 rows)

### 3. Application Statistics
**Description**: Key metrics about your job search
- Total applications submitted
- Response rate percentage
- Average response time
- Trend indicators (up/down)

**Best For**: Tracking your application performance

**Recommended Size**: Small (4 columns × 3 rows)

### 4. Upcoming Interviews
**Description**: Next 5 scheduled interviews from your calendar
- Event title
- Date and time
- Calendar integration
- Countdown to interviews

**Best For**: Preparing for upcoming interviews

**Recommended Size**: Small (4 columns × 3 rows)

### 5. Job Recommendations
**Description**: AI-powered job matches based on your profile
- Match score percentage
- Reasons for recommendation
- Company and job title
- Quick view link

**Best For**: Discovering relevant opportunities

**Recommended Size**: Small (4 columns × 3 rows)

### 6. Recent Activity
**Description**: Timeline of your recent job search actions
- Application submissions
- Interview scheduled
- Offers received
- Status changes

**Best For**: Tracking your daily progress

**Recommended Size**: Medium (6 columns × 4 rows)

### 7. Skills Development Progress
**Description**: Track your skill improvement goals
- Progress bars for each skill
- Current level vs. target level
- Visual progress indicators

**Best For**: Monitoring skill development

**Recommended Size**: Medium (4 columns × 3 rows)

### 8. Career Goals Tracker
**Description**: Monitor your career goal completion
- Goal title and deadline
- Progress percentage
- Completion status
- Visual progress bars

**Best For**: Staying on track with career objectives

**Recommended Size**: Medium (6 columns × 4 rows)

## Getting Started

### Accessing the Customizable Dashboard

1. Navigate to **Dashboard → Customizable Dashboard** from the main menu
2. The dashboard loads with the default layout
3. All widgets are displayed and ready to customize

### Default Layout

The default layout includes all 8 widgets arranged in an optimal configuration:
- **Top Row**: Status Overview, Recent Jobs
- **Middle Rows**: Application Stats, Upcoming Calendar, Recommendations
- **Bottom Rows**: Activity Timeline, Skills Progress, Goals Tracker

## Customizing Your Dashboard

### Rearranging Widgets

**Method 1: Drag and Drop**
1. Hover over a widget header until the cursor changes to a move icon
2. Click and hold the header
3. Drag the widget to your desired position
4. Release to drop the widget
5. Other widgets automatically adjust

**Method 2: Keyboard (Accessibility)**
1. Focus on a widget using Tab
2. Press Space to enter drag mode
3. Use arrow keys to move
4. Press Space again to drop

**Tips:**
- Widgets snap to the grid for clean alignment
- A blue placeholder shows where the widget will drop
- Widgets cannot overlap

### Resizing Widgets

1. Hover over the bottom-right corner of a widget
2. Look for the resize handle (small diagonal lines)
3. Click and drag to resize
4. Widgets have minimum and maximum sizes

**Size Constraints:**
- **Minimum Width**: 3-4 columns (varies by widget)
- **Minimum Height**: 2-3 rows (varies by widget)
- **Maximum Size**: Full dashboard width/height

**Best Practices:**
- Make frequently-used widgets larger
- Keep less important widgets smaller
- Balance widget sizes for visual appeal

### Saving Your Layout

**Auto-Save (Recommended)**
- Your layout is saved automatically as you make changes
- No manual save required in most cases

**Manual Save**
1. After making changes, click the **"Save Layout"** button (top-right)
2. Wait for the "Layout Saved" confirmation message
3. Your layout is now saved to your profile

**What Gets Saved:**
- Widget positions (x, y coordinates)
- Widget sizes (width, height)
- Widget visibility
- Grid configuration

### Resetting to Default

If you want to start fresh:

1. Click the **"Reset"** button (top-right)
2. Confirm the reset action
3. Dashboard restores to the default 8-widget layout
4. Your custom layout is replaced (cannot be undone)

## Responsive Behavior

### Desktop (1200px+)
- **12-column grid**
- All widgets visible
- Full drag-and-drop functionality
- Horizontal layout

### Tablet (768px - 1199px)
- **8-column grid**
- Widgets automatically adjust
- Some widgets stack vertically
- Drag-and-drop still works

### Mobile (< 768px)
- **4-column grid** (< 768px)
- **2-column grid** (< 480px)
- Widgets stack vertically
- Simplified layout
- Limited drag functionality

**Tip**: Customize on desktop for the best experience, then view on mobile.

## Advanced Features

### Widget Visibility (Coming Soon)
- Hide widgets you don't use
- Show/hide from settings menu
- Hidden widgets don't take up space

### Custom Widget Themes (Coming Soon)
- Light and dark mode
- Accent color customization
- Widget border styles

### Widget Data Refresh
- Widgets automatically refresh every 5 minutes
- Manual refresh button in each widget
- Real-time updates for calendar events

## Best Practices

### 1. Prioritize Important Widgets
Place your most-used widgets at the top:
- Application Status Overview
- Upcoming Interviews
- Recent Jobs

### 2. Group Related Widgets
Keep similar widgets together:
- Stats widgets (Applications Stats, Status Overview)
- Action widgets (Recent Jobs, Recommendations)
- Progress widgets (Skills, Goals)

### 3. Use Appropriate Sizes
- **Large**: Detailed information (Activity Timeline)
- **Medium**: List views (Recent Jobs, Status Overview)
- **Small**: Quick stats (Application Stats, Upcoming Calendar)

### 4. Regular Updates
- Review your layout monthly
- Adjust as your job search evolves
- Hide completed goal trackers

### 5. Mobile-First Design
If you primarily use mobile:
- Keep widgets at default sizes
- Avoid overly complex layouts
- Test on your mobile device

## Keyboard Shortcuts

| Action                | Shortcut                    |
| --------------------- | --------------------------- |
| Save Layout           | `Ctrl/Cmd + S`              |
| Reset Layout          | `Ctrl/Cmd + R`              |
| Focus Next Widget     | `Tab`                       |
| Focus Previous Widget | `Shift + Tab`               |
| Enter Drag Mode       | `Space` (on focused widget) |
| Move Widget           | `Arrow Keys` (in drag mode) |
| Drop Widget           | `Space` (in drag mode)      |
| Cancel Drag           | `Esc` (in drag mode)        |

## Troubleshooting

### Layout Not Saving

**Problem**: Changes don't persist after refresh

**Solutions**:
1. Click the "Save Layout" button manually
2. Check your internet connection
3. Clear browser cache and try again
4. Ensure you're logged in

### Widgets Not Moving

**Problem**: Drag-and-drop not working

**Solutions**:
1. Ensure you're dragging from the widget header
2. Try refreshing the page
3. Check if browser has JavaScript enabled
4. Try a different browser

### Widget Overlapping

**Problem**: Widgets appear on top of each other

**Solutions**:
1. Refresh the page
2. Click "Reset" to restore default layout
3. Manually drag widgets apart
4. Clear browser cache

### Missing Widgets

**Problem**: Some widgets don't appear

**Solutions**:
1. Scroll down - widgets might be below the fold
2. Check if widgets are hidden (coming soon)
3. Reset to default layout
4. Check browser console for errors

### Performance Issues

**Problem**: Dashboard feels slow or laggy

**Solutions**:
1. Reduce the number of large widgets
2. Close other browser tabs
3. Disable browser extensions temporarily
4. Use a modern browser (Chrome, Firefox, Safari, Edge)

## Accessibility Features

- **Keyboard Navigation**: Full keyboard support for all actions
- **Screen Reader Compatible**: ARIA labels on all interactive elements
- **High Contrast**: Works with browser high-contrast modes
- **Focus Indicators**: Clear visual focus states
- **Semantic HTML**: Proper heading hierarchy

## Performance Tips

### Optimize Your Layout
- Use 6-8 widgets maximum for best performance
- Avoid very large widgets if not needed
- Keep widget count reasonable on mobile

### Browser Recommendations
- **Best**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Minimum**: Chrome 80+, Firefox 75+, Safari 13+

### Hardware Recommendations
- **Minimum**: 4GB RAM, dual-core processor
- **Recommended**: 8GB RAM, quad-core processor

## Privacy & Data

- **Local Storage**: Layout preferences stored in your browser
- **Server Sync**: Layout also saved to your Career Copilot account
- **No Tracking**: Widget interactions are not tracked
- **Data Security**: All data encrypted in transit

## FAQ

**Q: How many widgets can I add?**
A: Currently, all 8 widgets are included. Custom widget addition is coming soon.

**Q: Can I share my dashboard layout?**
A: Not yet, but layout sharing is planned for a future update.

**Q: Do widgets update in real-time?**
A: Widgets refresh every 5 minutes. Upcoming Calendar syncs immediately.

**Q: Can I have different layouts on different devices?**
A: No, your layout syncs across all devices.

**Q: What happens if I delete my account?**
A: Your custom layout is deleted along with your account data.

**Q: Can I customize widget colors?**
A: Not yet, but custom themes are coming in a future update.

**Q: Do widgets work offline?**
A: Widgets require an internet connection to display live data.

**Q: Can I print my dashboard?**
A: Yes, use your browser's print function (Ctrl/Cmd + P).

## Upcoming Features

- [ ] Widget visibility toggle
- [ ] Custom widget themes
- [ ] Additional widgets (salary insights, company research)
- [ ] Layout templates
- [ ] Export dashboard as PDF
- [ ] Dashboard sharing
- [ ] Widget data export

## Support

Need help customizing your dashboard?

- **Email**: support@careercopilot.com
- **Video Tutorials**: [Dashboard Walkthrough](https://help.careercopilot.com/dashboard)
- **Community Forum**: [Ask Questions](https://community.careercopilot.com)
- **GitHub**: [Report Issues](https://github.com/moatasim-KT/career-copilot/issues)

---

**Last Updated**: November 17, 2025
**Version**: 1.0.0
