# VirtualApplicationList Integration Guide

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

This guide provides step-by-step instructions for integrating the VirtualApplicationList component into your application pages.

## Quick Start

### 1. Basic Integration

Replace existing application list with VirtualApplicationList:

```tsx
// Before
<div className="space-y-4">
  {applications.map(app => (
    <ApplicationCard key={app.id} application={app} />
  ))}
</div>

// After
import { VirtualApplicationList } from '@/components/applications/VirtualApplicationList';

<VirtualApplicationList
  applications={applications}
  onApplicationClick={(id) => router.push(`/applications/${id}`)}
  selectedApplicationIds={selectedIds}
  onSelectApplication={handleSelect}
/>
```

### 2. Add State Management

```tsx
import { useState } from 'react';

function ApplicationsPage() {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const handleSelect = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(selectedId => selectedId !== id)
        : [...prev, id]
    );
  };

  const handleClick = (id: number) => {
    router.push(`/applications/${id}`);
  };

  return (
    <VirtualApplicationList
      applications={applications}
      onApplicationClick={handleClick}
      selectedApplicationIds={selectedIds}
      onSelectApplication={handleSelect}
    />
  );
}
```

## Integration Patterns

### Pattern 1: With React Query

```tsx
import { useQuery } from '@tanstack/react-query';
import { VirtualApplicationList } from '@/components/applications/VirtualApplicationList';
import { ApplicationsService } from '@/lib/api/client';

function ApplicationsPage() {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const { data: applications = [], isLoading, error } = useQuery({
    queryKey: ['applications'],
    queryFn: () => ApplicationsService.getApplicationsApiV1ApplicationsGet(),
    staleTime: 1 * 60 * 1000, // 1 minute
  });

  if (isLoading) {
    return <ApplicationListSkeleton />;
  }

  if (error) {
    return <ErrorState message="Failed to load applications" />;
  }

  return (
    <VirtualApplicationList
      applications={applications}
      onApplicationClick={(id) => router.push(`/applications/${id}`)}
      selectedApplicationIds={selectedIds}
      onSelectApplication={(id) => {
        setSelectedIds(prev => 
          prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
      }}
    />
  );
}
```

### Pattern 2: With Filtering and Search

```tsx
import { useState, useMemo } from 'react';
import { VirtualApplicationList } from '@/components/applications/VirtualApplicationList';

function FilteredApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredApplications = useMemo(() => {
    return applications.filter(app => {
      // Status filter
      if (statusFilter !== 'all' && app.status !== statusFilter) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          app.job_title?.toLowerCase().includes(query) ||
          app.company_name?.toLowerCase().includes(query) ||
          app.notes?.toLowerCase().includes(query)
        );
      }

      return true;
    });
  }, [applications, statusFilter, searchQuery]);

  return (
    <div>
      <div className="mb-4 flex gap-4">
        <input
          type="text"
          placeholder="Search applications..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 px-4 py-2 border rounded"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border rounded"
        >
          <option value="all">All Statuses</option>
          <option value="interested">Interested</option>
          <option value="applied">Applied</option>
          <option value="interview">Interview</option>
          <option value="offer">Offer</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <VirtualApplicationList
        applications={filteredApplications}
        onApplicationClick={(id) => router.push(`/applications/${id}`)}
        selectedApplicationIds={selectedIds}
        onSelectApplication={(id) => {
          setSelectedIds(prev => 
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
          );
        }}
        emptyMessage={
          searchQuery || statusFilter !== 'all'
            ? 'No applications match your filters'
            : 'No applications found'
        }
      />
    </div>
  );
}
```

### Pattern 3: With Bulk Actions

```tsx
import { useState } from 'react';
import { VirtualApplicationList } from '@/components/applications/VirtualApplicationList';
import { BulkActionBar } from '@/components/ui/BulkActionBar';
import { Trash2, Archive, CheckCircle } from 'lucide-react';

function ApplicationsWithBulkActions() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const bulkActions = [
    {
      id: 'mark-reviewed',
      label: 'Mark as Reviewed',
      icon: CheckCircle,
      variant: 'default' as const,
      requiresConfirmation: false,
      action: async (ids: number[]) => {
        await updateApplications(ids, { reviewed: true });
        setSelectedIds([]);
      },
    },
    {
      id: 'archive',
      label: 'Archive',
      icon: Archive,
      variant: 'default' as const,
      requiresConfirmation: false,
      action: async (ids: number[]) => {
        await archiveApplications(ids);
        setApplications(prev => prev.filter(app => !ids.includes(app.id)));
        setSelectedIds([]);
      },
    },
    {
      id: 'delete',
      label: 'Delete',
      icon: Trash2,
      variant: 'destructive' as const,
      requiresConfirmation: true,
      action: async (ids: number[]) => {
        await deleteApplications(ids);
        setApplications(prev => prev.filter(app => !ids.includes(app.id)));
        setSelectedIds([]);
      },
    },
  ];

  return (
    <>
      <VirtualApplicationList
        applications={applications}
        onApplicationClick={(id) => router.push(`/applications/${id}`)}
        selectedApplicationIds={selectedIds}
        onSelectApplication={(id) => {
          setSelectedIds(prev => 
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
          );
        }}
      />

      {selectedIds.length > 0 && (
        <BulkActionBar
          selectedCount={selectedIds.length}
          actions={bulkActions}
          onClearSelection={() => setSelectedIds([])}
        />
      )}
    </>
  );
}
```

### Pattern 4: With Sorting

```tsx
import { useState, useMemo } from 'react';
import { VirtualApplicationList } from '@/components/applications/VirtualApplicationList';

type SortField = 'date' | 'status' | 'company';
type SortOrder = 'asc' | 'desc';

function SortedApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedApplications = useMemo(() => {
    const sorted = [...applications].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'date':
          comparison = new Date(a.applied_date || a.created_at).getTime() - 
                      new Date(b.applied_date || b.created_at).getTime();
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        case 'company':
          comparison = (a.company_name || '').localeCompare(b.company_name || '');
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [applications, sortField, sortOrder]);

  return (
    <div>
      <div className="mb-4 flex gap-4">
        <select
          value={sortField}
          onChange={(e) => setSortField(e.target.value as SortField)}
          className="px-4 py-2 border rounded"
        >
          <option value="date">Sort by Date</option>
          <option value="status">Sort by Status</option>
          <option value="company">Sort by Company</option>
        </select>
        <button
          onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
          className="px-4 py-2 border rounded"
        >
          {sortOrder === 'asc' ? '↑ Ascending' : '↓ Descending'}
        </button>
      </div>

      <VirtualApplicationList
        applications={sortedApplications}
        onApplicationClick={(id) => router.push(`/applications/${id}`)}
        selectedApplicationIds={selectedIds}
        onSelectApplication={(id) => {
          setSelectedIds(prev => 
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
          );
        }}
      />
    </div>
  );
}
```

### Pattern 5: Grid Layout with View Toggle

```tsx
import { useState } from 'react';
import { VirtualApplicationList, VirtualApplicationListGrid } from '@/components/applications/VirtualApplicationList';
import { List, Grid } from 'lucide-react';

function ApplicationsWithViewToggle() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

  const commonProps = {
    applications,
    onApplicationClick: (id: number) => router.push(`/applications/${id}`),
    selectedApplicationIds: selectedIds,
    onSelectApplication: (id: number) => {
      setSelectedIds(prev => 
        prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
      );
    },
  };

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <div className="inline-flex rounded-lg border border-neutral-300 dark:border-neutral-600">
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 flex items-center gap-2 ${
              viewMode === 'list' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300'
            }`}
          >
            <List className="w-4 h-4" />
            List
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`px-4 py-2 flex items-center gap-2 ${
              viewMode === 'grid' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300'
            }`}
          >
            <Grid className="w-4 h-4" />
            Grid
          </button>
        </div>
      </div>

      {viewMode === 'list' ? (
        <VirtualApplicationList {...commonProps} />
      ) : (
        <VirtualApplicationListGrid 
          {...commonProps}
          columns={{ sm: 1, md: 2, lg: 3, xl: 4 }}
        />
      )}
    </div>
  );
}
```

## Performance Optimization

### 1. Memoize Callbacks

```tsx
import { useCallback } from 'react';

const handleClick = useCallback((id: number) => {
  router.push(`/applications/${id}`);
}, [router]);

const handleSelect = useCallback((id: number) => {
  setSelectedIds(prev => 
    prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
  );
}, []);
```

### 2. Optimize Data Fetching

```tsx
// Use pagination for very large datasets
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['applications'],
  queryFn: ({ pageParam = 0 }) => 
    fetchApplications({ skip: pageParam, limit: 100 }),
  getNextPageParam: (lastPage, pages) => 
    lastPage.length === 100 ? pages.length * 100 : undefined,
});

const applications = data?.pages.flat() ?? [];
```

### 3. Adjust Virtualization Settings

```tsx
// For compact cards
<VirtualApplicationList
  estimatedSize={120}
  overscan={10}
  variant="compact"
/>

// For detailed cards
<VirtualApplicationList
  estimatedSize={280}
  overscan={3}
  variant="detailed"
/>
```

## Migration Checklist

- [ ] Replace existing list component with VirtualApplicationList
- [ ] Add state management for selection
- [ ] Implement click handlers
- [ ] Add loading and error states
- [ ] Test with large datasets (100+ items)
- [ ] Verify keyboard navigation works
- [ ] Test on mobile devices
- [ ] Check dark mode appearance
- [ ] Add bulk actions if needed
- [ ] Update tests

## Common Issues and Solutions

### Issue: Parent container has no height

```tsx
// ❌ Wrong
<div>
  <VirtualApplicationList applications={applications} ... />
</div>

// ✅ Correct
<div className="h-screen"> {/* or h-[600px], etc. */}
  <VirtualApplicationList applications={applications} ... />
</div>
```

### Issue: Cards have inconsistent heights

```tsx
// Measure actual card height and set estimatedSize
<VirtualApplicationList
  estimatedSize={240} // Adjust based on actual card height
  applications={applications}
  ...
/>
```

### Issue: Slow performance with many selected items

```tsx
// Use Set for O(1) lookup instead of array
const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

const isSelected = selectedIds.has(application.id);
```

## Next Steps

1. Review the [README](./README.md) for detailed API documentation
2. Explore [Storybook stories](./VirtualApplicationList.stories.tsx) for examples
3. Check [tests](./tests/VirtualApplicationList.test.tsx) for usage patterns
4. Integrate with your existing application pages

## Support

For issues or questions:
- Check existing tests and stories
- Review the VirtualJobList implementation (similar pattern)
- Consult the @tanstack/react-virtual documentation
