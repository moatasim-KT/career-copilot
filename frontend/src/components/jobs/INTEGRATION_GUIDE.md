# VirtualJobList Integration Guide

This guide shows how to integrate the `VirtualJobList` component into the existing JobsPage for improved performance with large job lists.

## Quick Integration

### Step 1: Import the Component

```tsx
// In JobsPage.tsx
import { VirtualJobList } from '@/components/jobs';
```

### Step 2: Replace JobListView

Replace the existing `JobListView` component with `VirtualJobList`:

```tsx
// Before
{currentView === 'list' ? (
  <JobListView
    key={listKey}
    jobs={filteredAndSortedJobs}
    onJobClick={(jobId) => console.log('View job:', jobId)}
    selectedJobIds={selectedJobIds}
    onSelectJob={handleSelectJob}
  />
) : (
  <JobTableView
    key={listKey}
    jobs={filteredAndSortedJobs}
    onJobClick={(jobId) => console.log('View job:', jobId)}
    selectedJobIds={selectedJobIds}
    onSelectJob={handleSelectJob}
  />
)}

// After
{currentView === 'list' ? (
  <VirtualJobList
    key={listKey}
    jobs={filteredAndSortedJobs}
    onJobClick={(jobId) => console.log('View job:', jobId)}
    selectedJobIds={selectedJobIds}
    onSelectJob={handleSelectJob}
    estimatedSize={220}
    overscan={5}
  />
) : (
  <JobTableView
    key={listKey}
    jobs={filteredAndSortedJobs}
    onJobClick={(jobId) => console.log('View job:', jobId)}
    selectedJobIds={selectedJobIds}
    onSelectJob={handleSelectJob}
  />
)}
```

### Step 3: Adjust Estimated Size (Optional)

Measure your actual job card height and adjust the `estimatedSize` prop for optimal performance:

```tsx
<VirtualJobList
  jobs={filteredAndSortedJobs}
  onJobClick={handleJobClick}
  selectedJobIds={selectedJobIds}
  onSelectJob={handleSelectJob}
  estimatedSize={240} // Adjust based on your JobCard height
  overscan={5}
/>
```

## Complete Example

Here's a complete example showing the integration:

```tsx
// JobsPage.tsx
import { VirtualJobList } from '@/components/jobs';

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);
  const [currentView, setCurrentView] = useState('list');
  
  // ... other state and handlers ...

  const handleJobClick = (jobId: number) => {
    // Navigate to job detail page
    router.push(`/jobs/${jobId}`);
  };

  const handleSelectJob = (jobId: number) => {
    setSelectedJobIds(prev =>
      prev.includes(jobId)
        ? prev.filter(id => id !== jobId)
        : [...prev, jobId]
    );
  };

  return (
    <div className="space-y-6">
      {/* Header, filters, etc. */}
      
      {/* Job List */}
      {isLoading ? (
        <LoadingSkeleton />
      ) : (
        <AnimatePresence mode="wait">
          {currentView === 'list' ? (
            <VirtualJobList
              key={listKey}
              jobs={filteredAndSortedJobs}
              onJobClick={handleJobClick}
              selectedJobIds={selectedJobIds}
              onSelectJob={handleSelectJob}
              estimatedSize={220}
              overscan={5}
              emptyMessage="No jobs found. Try adjusting your filters."
            />
          ) : (
            <JobTableView
              key={listKey}
              jobs={filteredAndSortedJobs}
              onJobClick={handleJobClick}
              selectedJobIds={selectedJobIds}
              onSelectJob={handleSelectJob}
            />
          )}
        </AnimatePresence>
      )}
    </div>
  );
}
```

## Grid Layout Option

You can also use the grid layout variant:

```tsx
import { VirtualJobListGrid } from '@/components/jobs';

// Add a new view option
const [currentView, setCurrentView] = useState<'list' | 'grid' | 'table'>('list');

// In your render:
{currentView === 'list' ? (
  <VirtualJobList
    jobs={filteredAndSortedJobs}
    onJobClick={handleJobClick}
    selectedJobIds={selectedJobIds}
    onSelectJob={handleSelectJob}
  />
) : currentView === 'grid' ? (
  <VirtualJobListGrid
    jobs={filteredAndSortedJobs}
    onJobClick={handleJobClick}
    selectedJobIds={selectedJobIds}
    onSelectJob={handleSelectJob}
    columns={{ sm: 1, md: 2, lg: 3, xl: 4 }}
  />
) : (
  <JobTableView
    jobs={filteredAndSortedJobs}
    onJobClick={handleJobClick}
    selectedJobIds={selectedJobIds}
    onSelectJob={handleSelectJob}
  />
)}
```

## Performance Optimization

### 1. Memoize Callbacks

```tsx
const handleJobClick = useCallback((jobId: number) => {
  router.push(`/jobs/${jobId}`);
}, [router]);

const handleSelectJob = useCallback((jobId: number) => {
  setSelectedJobIds(prev =>
    prev.includes(jobId)
      ? prev.filter(id => id !== jobId)
      : [...prev, jobId]
  );
}, []);
```

### 2. Memoize Filtered Jobs

```tsx
const filteredAndSortedJobs = useMemo(() => {
  // Your filtering and sorting logic
  return jobs.filter(/* ... */).sort(/* ... */);
}, [jobs, searchTerm, filters, sortBy]);
```

### 3. Adjust Overscan Based on Performance

```tsx
// For slower devices or very complex job cards
<VirtualJobList
  jobs={jobs}
  overscan={3}
  // ...
/>

// For faster devices or simpler job cards
<VirtualJobList
  jobs={jobs}
  overscan={10}
  // ...
/>
```

## Testing with Large Datasets

To test the virtualization with a large dataset:

```tsx
// Generate test data
const generateTestJobs = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: `Job ${i + 1}`,
    company: `Company ${i + 1}`,
    location: 'Remote',
    type: 'full-time',
    postedAt: '1 day ago',
  }));
};

// Use in development
const testJobs = generateTestJobs(1000);

<VirtualJobList
  jobs={testJobs}
  onJobClick={handleJobClick}
  selectedJobIds={selectedJobIds}
  onSelectJob={handleSelectJob}
/>
```

## Troubleshooting

### Issue: Items not rendering

**Solution**: Ensure the parent container has a defined height:

```tsx
<div className="h-[calc(100vh-300px)]">
  <VirtualJobList {...props} />
</div>
```

### Issue: Jumpy scrolling

**Solution**: Adjust the `estimatedSize` to match your actual job card height more closely:

```tsx
// Measure your JobCard height in the browser
// Then set estimatedSize to that value
<VirtualJobList
  estimatedSize={240} // Match your actual card height
  {...props}
/>
```

### Issue: Performance still slow

**Solution**: 
1. Reduce overscan
2. Simplify JobCard component
3. Memoize callbacks and filtered data
4. Check for unnecessary re-renders with React DevTools

```tsx
<VirtualJobList
  overscan={3} // Reduce from default 5
  {...props}
/>
```

## Migration Checklist

- [ ] Import `VirtualJobList` from `@/components/jobs`
- [ ] Replace `JobListView` with `VirtualJobList`
- [ ] Add `estimatedSize` prop (measure your JobCard height)
- [ ] Add `overscan` prop (start with 5)
- [ ] Memoize `handleJobClick` callback
- [ ] Memoize `handleSelectJob` callback
- [ ] Memoize `filteredAndSortedJobs` array
- [ ] Test with 100+ jobs
- [ ] Test scrolling performance
- [ ] Test selection functionality
- [ ] Test on mobile devices
- [ ] Update tests if needed

## Benefits

After integration, you should see:

- ✅ Smooth scrolling with 100+ jobs
- ✅ Instant initial render
- ✅ Lower memory usage
- ✅ Better mobile performance
- ✅ No layout shifts during scroll
- ✅ Maintained animations and interactions

## Rollback

If you need to rollback, simply replace `VirtualJobList` with the original `JobListView`:

```tsx
// Rollback to original
<JobListView
  jobs={filteredAndSortedJobs}
  onJobClick={handleJobClick}
  selectedJobIds={selectedJobIds}
  onSelectJob={handleSelectJob}
/>
```

## Support

For issues or questions:
1. Check the [README](./README.md)
2. Review the [Storybook stories](./VirtualJobList.stories.tsx)
3. Check the [test file](./__tests__/VirtualJobList.test.tsx) for usage examples
