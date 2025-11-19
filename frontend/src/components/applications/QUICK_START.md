# VirtualApplicationList - Quick Start Guide

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

Get up and running with VirtualApplicationList in 5 minutes.

## Installation

No installation needed - the component is already part of the project.

## Basic Example

```tsx
'use client';

import { useState } from 'react';
import { VirtualApplicationList } from '@/components/applications/VirtualApplicationList';
import { Application } from '@/components/ui/ApplicationCard';

export default function MyApplicationsPage() {
  // Your application data
  const [applications, setApplications] = useState<Application[]>([
    {
      id: 1,
      user_id: 1,
      job_id: 10,
      status: 'applied',
      applied_date: '2024-11-01',
      response_date: null,
      interview_date: null,
      offer_date: null,
      notes: 'Great company culture',
      interview_feedback: null,
      follow_up_date: null,
      created_at: '2024-11-01T10:00:00Z',
      updated_at: '2024-11-01T10:00:00Z',
      job_title: 'Software Engineer',
      company_name: 'TechCorp',
      job_location: 'Remote',
    },
    // ... more applications
  ]);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // Handle application click
  const handleClick = (id: number) => {
    console.log('Application clicked:', id);
    // Navigate to detail page, open modal, etc.
  };

  // Handle selection
  const handleSelect = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(selectedId => selectedId !== id)
        : [...prev, id]
    );
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">My Applications</h1>
      
      <VirtualApplicationList
        applications={applications}
        onApplicationClick={handleClick}
        selectedApplicationIds={selectedIds}
        onSelectApplication={handleSelect}
      />
    </div>
  );
}
```

## With Data Fetching

```tsx
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { VirtualApplicationList } from '@/components/applications/VirtualApplicationList';
import { ApplicationsService } from '@/lib/api/client';

export default function ApplicationsPage() {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // Fetch applications
  const { data: applications = [], isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: () => ApplicationsService.getApplicationsApiV1ApplicationsGet(),
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <VirtualApplicationList
      applications={applications}
      onApplicationClick={(id) => console.log('Clicked:', id)}
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

## Different Variants

### Compact (for dense lists)
```tsx
<VirtualApplicationList
  applications={applications}
  variant="compact"
  estimatedSize={120}
  {...otherProps}
/>
```

### Detailed (for more information)
```tsx
<VirtualApplicationList
  applications={applications}
  variant="detailed"
  estimatedSize={280}
  {...otherProps}
/>
```

### Grid Layout
```tsx
import { VirtualApplicationListGrid } from '@/components/applications/VirtualApplicationList';

<VirtualApplicationListGrid
  applications={applications}
  columns={{ sm: 1, md: 2, lg: 3 }}
  {...otherProps}
/>
```

## Common Customizations

### Custom Empty Message
```tsx
<VirtualApplicationList
  applications={applications}
  emptyMessage="You haven't applied to any jobs yet!"
  {...otherProps}
/>
```

### Adjust Performance
```tsx
<VirtualApplicationList
  applications={applications}
  estimatedSize={240}  // Match your card height
  overscan={10}        // Render more items outside viewport
  {...otherProps}
/>
```

### Custom Container Height
```tsx
<div className="h-[600px]">
  <VirtualApplicationList
    applications={applications}
    {...otherProps}
  />
</div>
```

## Testing in Storybook

```bash
npm run storybook
```

Navigate to: **Components > Applications > VirtualApplicationList**

Try the interactive examples:
- Default (10 applications)
- Large List (100 applications)
- Very Large List (1000 applications)
- Different variants
- Grid layout

## Performance Tips

1. **Set correct estimated size**: Measure your card height and set `estimatedSize` prop
2. **Use memoization**: Wrap callbacks in `useCallback` to prevent re-renders
3. **Pagination**: For 10,000+ items, consider pagination or infinite scroll
4. **Overscan**: Balance between smooth scrolling (higher) and memory (lower)

## Need Help?

- 📖 [Full Documentation](./README.md)
- 🔧 [Integration Guide](./INTEGRATION_GUIDE.md)
- 📊 [Performance Benchmarks](./benchmark.ts)
- 🎨 [Storybook Examples](./VirtualApplicationList.stories.tsx)
- ✅ [Test Examples](./__tests__/VirtualApplicationList.test.tsx)

## Common Issues

**Issue**: Cards not rendering
**Solution**: Ensure parent container has a defined height

**Issue**: Jumpy scrolling
**Solution**: Set `estimatedSize` to match actual card height

**Issue**: Slow performance
**Solution**: Check that virtualization is working (only ~10 items should render)

---

That's it! You're ready to use VirtualApplicationList in your application. 🚀
