# Route Prefetching Implementation

## Overview

This document describes the implementation of route prefetching for critical user paths in the Career Copilot application. Route prefetching improves perceived performance by preloading route data when users hover over navigation links.

## Implementation Details

### Core Hook: `useRoutePrefetch`

**Location:** `frontend/src/hooks/useRoutePrefetch.ts`

The `useRoutePrefetch` hook provides event handlers for prefetching Next.js routes:

```typescript
const { onMouseEnter, onMouseLeave, onTouchStart } = useRoutePrefetch('/dashboard');
```

**Features:**
- **Hover-based prefetching**: Prefetches routes after a configurable delay (default 50ms) when user hovers over a link
- **Touch support**: Immediately prefetches on touch devices when user touches a link
- **Cancellation**: Cancels prefetch if user moves away before delay completes
- **Single prefetch**: Only prefetches each route once to avoid redundant network requests
- **Error handling**: Gracefully handles prefetch failures without breaking the UI
- **Configurable**: Supports custom delay and enable/disable options

### Batch Prefetching: `usePrefetchRoutes`

For prefetching multiple critical routes at once:

```typescript
const { prefetchAll } = usePrefetchRoutes(['/dashboard', '/jobs', '/applications']);
```

This is useful for prefetching all critical routes on app initialization.

### PrefetchLink Component

**Location:** `frontend/src/components/ui/PrefetchLink.tsx`

A wrapper around Next.js Link component that automatically adds prefetching:

```typescript
<PrefetchLink href="/dashboard">
  Go to Dashboard
</PrefetchLink>
```

**Props:**
- `prefetch`: Enable/disable prefetching (default: true)
- `prefetchDelay`: Delay in milliseconds before prefetching (default: 50)
- All standard Next.js Link props

## Integration Points

### 1. Navigation Component

**Location:** `frontend/src/components/layout/Navigation.tsx`

All navigation links now use prefetching:

```typescript
function NavigationLink({ href, label, icon, isActive }: NavigationLinkProps) {
  const prefetchHandlers = useRoutePrefetch(href);

  return (
    <Link
      href={href}
      onMouseEnter={prefetchHandlers.onMouseEnter}
      onMouseLeave={prefetchHandlers.onMouseLeave}
      onTouchStart={prefetchHandlers.onTouchStart}
      // ... other props
    />
  );
}
```

**Critical routes prefetched:**
- `/dashboard` - Main dashboard
- `/jobs` - Job listings
- `/applications` - Application tracking
- `/recommendations` - Job recommendations
- `/analytics` - Analytics dashboard
- `/advanced-features` - AI tools

### 2. NotificationCenter

**Location:** `frontend/src/components/ui/NotificationCenter.tsx`

Notification action links and the "View all notifications" link use prefetching:

```typescript
// Prefetch notification action URLs
const prefetchHandlers = useRoutePrefetch(
  notification.actionUrl || '',
  { enabled: !!notification.actionUrl }
);

// Prefetch notifications page
const notificationsPrefetch = useRoutePrefetch('/notifications');
```

## Performance Benefits

### Before Prefetching
1. User hovers over link
2. User clicks link
3. Browser requests route data
4. User waits for data to load
5. Page renders

### After Prefetching
1. User hovers over link
2. Browser prefetches route data in background
3. User clicks link
4. Page renders immediately (data already loaded)

**Result:** Near-instant page transitions for critical routes

## Configuration

### Default Settings

```typescript
{
  delay: 50,        // 50ms delay before prefetching
  enabled: true     // Prefetching enabled by default
}
```

### Custom Configuration

```typescript
// Longer delay for less critical routes
const handlers = useRoutePrefetch('/settings', { delay: 200 });

// Disable prefetching conditionally
const handlers = useRoutePrefetch('/admin', { 
  enabled: user.isAdmin 
});
```

## Testing

### Unit Tests

**Location:** `frontend/src/hooks/__tests__/useRoutePrefetch.test.ts`

Tests cover:
- ✅ Prefetch on mouse enter after delay
- ✅ Cancel prefetch on mouse leave
- ✅ Immediate prefetch on touch
- ✅ Single prefetch per route
- ✅ Custom delay configuration
- ✅ Enable/disable functionality
- ✅ Error handling
- ✅ Batch prefetching

### Manual Testing

To verify prefetching is working:

1. Open Chrome DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Hover over navigation links
4. Observe prefetch requests after 50ms delay
5. Click link and verify instant navigation

## Browser Compatibility

Route prefetching uses Next.js's built-in `router.prefetch()` which is supported in all modern browsers:

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Best Practices

### When to Use Prefetching

✅ **Use for:**
- Critical user paths (dashboard, main features)
- Frequently accessed pages
- Navigation links
- Call-to-action buttons

❌ **Avoid for:**
- Rarely accessed pages
- Large data-heavy routes
- External links
- Conditional routes that may not exist

### Performance Considerations

1. **Delay Configuration**: 50ms delay prevents unnecessary prefetches when users quickly move their mouse across links

2. **Single Prefetch**: Each route is only prefetched once to avoid redundant network requests

3. **Error Handling**: Prefetch failures are logged but don't affect user experience

4. **Touch Devices**: Immediate prefetch on touch provides better mobile experience

## Future Enhancements

Potential improvements for future iterations:

1. **Intelligent Prefetching**: Use analytics to prefetch most likely next routes
2. **Network-Aware**: Disable prefetching on slow connections
3. **Priority Levels**: Prefetch critical routes first, then secondary routes
4. **Cache Management**: Implement cache invalidation strategies
5. **Prefetch on Viewport**: Prefetch when links enter viewport (intersection observer)

## Metrics

To measure the impact of prefetching:

1. **Time to Interactive (TTI)**: Should decrease for prefetched routes
2. **First Contentful Paint (FCP)**: Should improve for navigation
3. **User Perception**: Faster perceived navigation speed
4. **Network Usage**: Monitor prefetch request volume

## Related Files

- `frontend/src/hooks/useRoutePrefetch.ts` - Core hook implementation
- `frontend/src/components/ui/PrefetchLink.tsx` - Prefetch link component
- `frontend/src/components/layout/Navigation.tsx` - Navigation integration
- `frontend/src/components/ui/NotificationCenter.tsx` - Notification integration
- `frontend/src/hooks/__tests__/useRoutePrefetch.test.ts` - Unit tests

## References

- [Next.js Router Prefetching](https://nextjs.org/docs/app/api-reference/functions/use-router#routerprefetch)
- [Web Performance: Resource Hints](https://developer.mozilla.org/en-US/docs/Web/Performance/dns-prefetch)
- [Optimizing Navigation Performance](https://web.dev/navigation-and-resource-timing/)
