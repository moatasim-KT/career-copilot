# Caching & State Management Optimization

This document describes the comprehensive caching and state management optimizations implemented in the Career Copilot application.

## Overview

The application uses React Query (TanStack Query) for server state management with optimized caching strategies, stale-while-revalidate pattern, optimistic updates, and intelligent prefetching.

## Table of Contents

1. [Query Client Configuration](#query-client-configuration)
2. [Stale-While-Revalidate Pattern](#stale-while-revalidate-pattern)
3. [Optimistic Updates](#optimistic-updates)
4. [Prefetching](#prefetching)
5. [Best Practices](#best-practices)
6. [Performance Metrics](#performance-metrics)

## Query Client Configuration

### Cache Time Settings

Different data types have different caching strategies based on their update frequency and importance:

| Data Type | Stale Time | GC Time | Refetch on Mount | Refetch on Focus | Refetch on Reconnect |
|-----------|------------|---------|------------------|------------------|---------------------|
| Jobs | 5 min | 10 min | ✅ Yes | ❌ No | ✅ Yes |
| Applications | 1 min | 5 min | ✅ Yes | ❌ No | ✅ Yes |
| User Profile | 30 min | 1 hour | ❌ No | ✅ Yes | ✅ Yes |
| Analytics | 10 min | 30 min | ❌ No | ❌ No | ❌ No |
| Notifications | 30 sec | 5 min | ✅ Yes | ✅ Yes | ✅ Yes |
| Recommendations | 5 min | 15 min | ✅ Yes | ❌ No | ✅ Yes |
| Skill Gap | 15 min | 30 min | ❌ No | ❌ No | ❌ No |
| Search Results | 30 sec | 5 min | ❌ No | ❌ No | ❌ No |

### Usage

```typescript
import { useJobs } from '@/hooks/useJobs';
import { useApplications } from '@/hooks/useApplications';
import { useUserProfile } from '@/hooks/useUserProfile';
import { useAnalyticsSummary } from '@/hooks/useAnalytics';

// Jobs - 5 min stale time, refetch on mount
const { data: jobs } = useJobs();

// Applications - 1 min stale time, refetch on mount
const { data: applications } = useApplications();

// User profile - 30 min stale time, refetch on focus
const { data: profile } = useUserProfile();

// Analytics - 10 min stale time, no auto-refetch
const { data: analytics } = useAnalyticsSummary();
```

### Query Keys

Structured query keys for better cache management:

```typescript
import { queryKeys } from '@/lib/queryClient';

// Jobs
queryKeys.jobs.all                    // ['jobs']
queryKeys.jobs.lists()                // ['jobs', 'list']
queryKeys.jobs.list({ status: 'active' }) // ['jobs', 'list', { status: 'active' }]
queryKeys.jobs.detail(123)            // ['jobs', 'detail', 123]
queryKeys.jobs.search('engineer')     // ['jobs', 'search', 'engineer']

// Applications
queryKeys.applications.all            // ['applications']
queryKeys.applications.list({})       // ['applications', 'list', {}]
queryKeys.applications.detail(456)    // ['applications', 'detail', 456]

// User Profile
queryKeys.userProfile.current()       // ['user-profile', 'current']

// Analytics
queryKeys.analytics.summary()         // ['analytics', 'summary']
queryKeys.analytics.comprehensive(90) // ['analytics', 'comprehensive', 90]
```

## Stale-While-Revalidate Pattern

The SWR pattern shows cached data immediately while fetching fresh data in the background.

### How It Works

1. **Initial Load**: Data is fetched from the server
2. **Subsequent Loads**: Cached data is shown immediately
3. **Background Revalidation**: Fresh data is fetched in the background
4. **Automatic Update**: UI updates when fresh data arrives

### Benefits

- ✅ Instant UI updates with cached data
- ✅ Background revalidation ensures data freshness
- ✅ Reduced perceived latency
- ✅ Better user experience

### Usage

```typescript
import { useSWR } from '@/lib/swr';

function JobsList() {
  const { data, isLoading, isStale } = useSWR(
    ['jobs', 'list'],
    () => fetchJobs(),
    { staleTime: 5 * 60 * 1000 }
  );
  
  return (
    <div>
      {isStale && <p>Updating...</p>}
      {data?.map(job => <JobCard key={job.id} job={job} />)}
    </div>
  );
}
```

### Manual Revalidation

```typescript
import { useRevalidate } from '@/lib/swr';

function RefreshButton() {
  const { revalidate, revalidateAll } = useRevalidate();
  
  return (
    <>
      <button onClick={() => revalidate(['jobs'])}>
        Refresh Jobs
      </button>
      <button onClick={() => revalidateAll()}>
        Refresh All
      </button>
    </>
  );
}
```

## Optimistic Updates

Optimistic updates improve perceived performance by updating the UI immediately before the server responds.

### How It Works

1. **Mutation Triggered**: User performs an action (e.g., update status)
2. **Optimistic Update**: UI is updated immediately
3. **Server Request**: Request is sent to the server
4. **Success**: Cache is updated with server response
5. **Error**: UI is rolled back to previous state

### Benefits

- ✅ Instant UI feedback
- ✅ Better user experience
- ✅ Reduced perceived latency
- ✅ Automatic rollback on errors

### Usage

#### Application Status Update

```typescript
import { useUpdateApplication } from '@/hooks/useUpdateApplication';

function ApplicationCard({ application }) {
  const updateApplication = useUpdateApplication();
  
  const handleStatusChange = (newStatus) => {
    updateApplication.mutate({
      id: application.id,
      data: { status: newStatus }
    });
    // UI updates immediately, rolls back if error occurs
  };
  
  return (
    <select onChange={(e) => handleStatusChange(e.target.value)}>
      <option value="applied">Applied</option>
      <option value="interview">Interview</option>
      <option value="offer">Offer</option>
    </select>
  );
}
```

#### Job Save/Unsave

```typescript
import { useSaveJob, useUnsaveJob } from '@/hooks/useJobActions';

function JobCard({ job }) {
  const saveJob = useSaveJob();
  const unsaveJob = useUnsaveJob();
  
  const handleToggleSave = () => {
    if (job.saved) {
      unsaveJob.mutate(job.id);
    } else {
      saveJob.mutate(job.id);
    }
    // UI updates immediately, rolls back if error occurs
  };
  
  return (
    <button onClick={handleToggleSave}>
      {job.saved ? 'Unsave' : 'Save'}
    </button>
  );
}
```

#### Custom Optimistic Mutation

```typescript
import { useOptimisticMutation } from '@/lib/optimisticUpdates';

function CustomComponent() {
  const mutation = useOptimisticMutation({
    mutationFn: (data) => apiClient.updateData(data),
    queryKey: ['my-data'],
    updater: (oldData, variables) => {
      // Update logic
      return oldData.map(item =>
        item.id === variables.id ? { ...item, ...variables } : item
      );
    },
  });
  
  return (
    <button onClick={() => mutation.mutate({ id: 1, name: 'Updated' })}>
      Update
    </button>
  );
}
```

### Error Handling

Optimistic updates automatically roll back on error:

```typescript
const updateApplication = useUpdateApplication();

updateApplication.mutate(
  { id: 1, data: { status: 'interview' } },
  {
    onError: (error) => {
      // UI has already been rolled back
      toast.error('Failed to update application');
    },
    onSuccess: (data) => {
      toast.success('Application updated successfully');
    },
  }
);
```

## Prefetching

Prefetching loads data before it's needed, reducing wait times when users navigate.

### Strategies

#### 1. Hover Prefetch

Prefetch data when user hovers over a link or card:

```typescript
import { usePrefetchJob } from '@/lib/prefetch';

function JobCard({ job }) {
  const prefetchJob = usePrefetchJob();
  
  return (
    <Link
      href={`/jobs/${job.id}`}
      onMouseEnter={() => prefetchJob(job.id)}
    >
      {job.title}
    </Link>
  );
}
```

#### 2. Next Page Prefetch

Prefetch next page when user is near the end of the current page:

```typescript
import { usePrefetchNextPage } from '@/lib/prefetch';

function JobsList({ page, pageSize, totalItems }) {
  const { observerRef } = usePrefetchNextPage({
    currentPage: page,
    pageSize,
    totalItems,
    onPrefetch: () => prefetchJobs({ skip: (page + 1) * pageSize, limit: pageSize }),
  });
  
  return (
    <div>
      {jobs.map(job => <JobCard key={job.id} job={job} />)}
      <div ref={observerRef} /> {/* Sentinel element */}
    </div>
  );
}
```

#### 3. Scroll Prefetch

Prefetch data when user scrolls past a threshold:

```typescript
import { usePrefetchOnScroll } from '@/lib/prefetch';

function InfiniteList() {
  const { reset } = usePrefetchOnScroll({
    onPrefetch: () => loadMoreData(),
    threshold: 0.8, // Prefetch when 80% scrolled
  });
  
  return <div>{/* List content */}</div>;
}
```

#### 4. Route Prefetch

Prefetch page data when user hovers over navigation links:

```typescript
import { usePrefetchRoute } from '@/lib/prefetch';

function Navigation() {
  const { prefetchDashboard, prefetchJobsPage } = usePrefetchRoute();
  
  return (
    <nav>
      <Link href="/dashboard" onMouseEnter={prefetchDashboard}>
        Dashboard
      </Link>
      <Link href="/jobs" onMouseEnter={prefetchJobsPage}>
        Jobs
      </Link>
    </nav>
  );
}
```

### Manual Prefetch

```typescript
import { prefetchJob, prefetchJobs } from '@/lib/prefetch';
import { useQueryClient } from '@tanstack/react-query';

function MyComponent() {
  const queryClient = useQueryClient();
  
  const handlePrefetch = async () => {
    // Prefetch single job
    await prefetchJob(queryClient, 123);
    
    // Prefetch jobs list
    await prefetchJobs(queryClient, { skip: 0, limit: 50 });
  };
  
  return <button onClick={handlePrefetch}>Prefetch</button>;
}
```

## Best Practices

### 1. Use Appropriate Cache Times

- **Frequently changing data** (notifications): Short stale time (30 sec)
- **Moderately changing data** (applications): Medium stale time (1-5 min)
- **Rarely changing data** (user profile): Long stale time (30 min)
- **Static data** (analytics): Very long stale time (10+ min)

### 2. Implement Optimistic Updates for User Actions

Always use optimistic updates for:
- Status changes
- Save/unsave actions
- Like/unlike actions
- Simple updates

### 3. Prefetch Predictable Navigation

Prefetch data for:
- Hover over links
- Next page in pagination
- Related data
- Common navigation paths

### 4. Handle Errors Gracefully

```typescript
const mutation = useMutation({
  mutationFn: updateData,
  onError: (error, variables, context) => {
    // Rollback is automatic
    toast.error('Update failed');
    logger.error('Mutation error:', error);
  },
});
```

### 5. Invalidate Related Queries

```typescript
const mutation = useMutation({
  mutationFn: updateApplication,
  onSuccess: () => {
    // Invalidate related queries
    queryClient.invalidateQueries({ queryKey: ['applications'] });
    queryClient.invalidateQueries({ queryKey: ['analytics'] });
  },
});
```

### 6. Use Query Keys Consistently

```typescript
// Good: Use structured query keys
queryKeys.jobs.list({ status: 'active' })

// Bad: Use ad-hoc strings
['jobs', 'active']
```

### 7. Monitor Cache Performance

```typescript
import { useQueryClient } from '@tanstack/react-query';

function CacheMonitor() {
  const queryClient = useQueryClient();
  
  const cacheSize = queryClient.getQueryCache().getAll().length;
  const mutationCount = queryClient.getMutationCache().getAll().length;
  
  return (
    <div>
      <p>Cached queries: {cacheSize}</p>
      <p>Active mutations: {mutationCount}</p>
    </div>
  );
}
```

## Performance Metrics

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Initial page load | 2-3s | 1-1.5s | 50% faster |
| Navigation between pages | 1-2s | <100ms | 90% faster |
| Status update feedback | 500ms | Instant | 100% faster |
| Perceived latency | High | Low | Significant |

### Measuring Performance

```typescript
import { useQuery } from '@tanstack/react-query';

function MyComponent() {
  const { data, dataUpdatedAt, isFetching, isStale } = useQuery({
    queryKey: ['my-data'],
    queryFn: fetchData,
  });
  
  console.log('Data age:', Date.now() - dataUpdatedAt);
  console.log('Is fetching:', isFetching);
  console.log('Is stale:', isStale);
}
```

## Troubleshooting

### Data Not Updating

Check if stale time is too long:

```typescript
// Reduce stale time
const { data } = useQuery({
  queryKey: ['my-data'],
  queryFn: fetchData,
  staleTime: 30 * 1000, // 30 seconds instead of 5 minutes
});
```

### Optimistic Update Not Rolling Back

Ensure you're returning context from `onMutate`:

```typescript
const mutation = useMutation({
  mutationFn: updateData,
  onMutate: async (variables) => {
    const previousData = queryClient.getQueryData(['my-data']);
    // ... optimistic update
    return { previousData }; // Must return context
  },
  onError: (err, variables, context) => {
    if (context?.previousData) {
      queryClient.setQueryData(['my-data'], context.previousData);
    }
  },
});
```

### Prefetch Not Working

Check if data is already cached:

```typescript
await queryClient.prefetchQuery({
  queryKey: ['my-data'],
  queryFn: fetchData,
  staleTime: 5 * 60 * 1000,
  // Add this to force refetch
  force: true,
});
```

## Demo Pages

- **SWR Demo**: `/examples/swr-demo` - Demonstrates stale-while-revalidate pattern
- **Prefetch Demo**: `/examples/prefetch-demo` - Demonstrates various prefetching strategies

## Related Files

- `frontend/src/lib/queryClient.ts` - Query client configuration
- `frontend/src/lib/swr.ts` - SWR pattern implementation
- `frontend/src/lib/optimisticUpdates.ts` - Optimistic updates utilities
- `frontend/src/lib/prefetch.ts` - Prefetching utilities
- `frontend/src/hooks/useJobs.ts` - Jobs hooks with optimized caching
- `frontend/src/hooks/useApplications.ts` - Applications hooks with optimized caching
- `frontend/src/hooks/useUserProfile.ts` - User profile hooks
- `frontend/src/hooks/useAnalytics.ts` - Analytics hooks
- `frontend/src/hooks/useNotificationsQuery.ts` - Notifications hooks
- `frontend/src/hooks/useJobActions.ts` - Job actions with optimistic updates
- `frontend/src/hooks/useUpdateApplication.ts` - Application updates with optimistic updates

## Testing

Run tests for optimistic updates:

```bash
npm test optimisticUpdates.test.ts
```

## Conclusion

The caching and state management optimizations provide:

- ✅ Instant UI feedback with optimistic updates
- ✅ Reduced perceived latency with SWR pattern
- ✅ Predictive data loading with prefetching
- ✅ Automatic error handling and rollback
- ✅ Optimized cache times for different data types
- ✅ Better user experience overall

These optimizations significantly improve the perceived performance of the application without requiring changes to the backend API.
