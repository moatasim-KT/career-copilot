# VirtualDataTable Integration Guide

This guide shows how to integrate the VirtualDataTable component into your existing pages and components.

## Quick Start

### 1. Replace Existing DataTable

If you're already using the standard DataTable:

```tsx
// Before
import { DataTable } from '@/components/ui/DataTable/DataTable';

<DataTable columns={columns} data={data} />

// After
import { VirtualDataTable } from '@/components/ui/DataTable/VirtualDataTable';

<VirtualDataTable columns={columns} data={data} />
```

That's it! The VirtualDataTable is a drop-in replacement.

### 2. Integration with React Query

```tsx
import { useQuery } from '@tanstack/react-query';
import { VirtualDataTable } from '@/components/ui/DataTable/VirtualDataTable';

function JobsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: fetchJobs,
  });

  return (
    <VirtualDataTable
      columns={jobColumns}
      data={data ?? []}
      isLoading={isLoading}
    />
  );
}
```

### 3. Integration with Server-Side Data

```tsx
'use client';

import { useState, useEffect } from 'react';
import { VirtualDataTable } from '@/components/ui/DataTable/VirtualDataTable';

function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const response = await fetch('/api/applications');
      const data = await response.json();
      setApplications(data);
      setIsLoading(false);
    }
    loadData();
  }, []);

  return (
    <VirtualDataTable
      columns={applicationColumns}
      data={applications}
      isLoading={isLoading}
    />
  );
}
```

## Real-World Examples

### Example 1: Jobs Page with Filtering

```tsx
'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { VirtualDataTable } from '@/components/ui/DataTable/VirtualDataTable';
import { ColumnDef } from '@tanstack/react-table';

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salary: number;
  type: string;
  postedAt: string;
}

const jobColumns: ColumnDef<Job>[] = [
  {
    accessorKey: 'title',
    header: 'Job Title',
    size: 250,
  },
  {
    accessorKey: 'company',
    header: 'Company',
    size: 200,
  },
  {
    accessorKey: 'location',
    header: 'Location',
    size: 150,
  },
  {
    accessorKey: 'salary',
    header: 'Salary',
    size: 120,
    cell: ({ getValue }) => {
      const salary = getValue() as number;
      return `$${salary.toLocaleString()}`;
    },
  },
  {
    accessorKey: 'type',
    header: 'Type',
    size: 120,
  },
  {
    accessorKey: 'postedAt',
    header: 'Posted',
    size: 120,
  },
];

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await fetch('/api/jobs');
      return response.json();
    },
  });

  const filteredJobs = useMemo(() => {
    if (statusFilter === 'all') return jobs;
    return jobs.filter((job) => job.type === statusFilter);
  }, [jobs, statusFilter]);

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4">Job Listings</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-4 py-2 rounded ${
              statusFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setStatusFilter('Full-time')}
            className={`px-4 py-2 rounded ${
              statusFilter === 'Full-time' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            Full-time
          </button>
          <button
            onClick={() => setStatusFilter('Part-time')}
            className={`px-4 py-2 rounded ${
              statusFilter === 'Part-time' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            Part-time
          </button>
        </div>
      </div>

      <VirtualDataTable
        columns={jobColumns}
        data={filteredJobs}
        isLoading={isLoading}
        enablePerformanceMonitoring={process.env.NODE_ENV === 'development'}
      />
    </div>
  );
}
```

### Example 2: Applications Page with Expandable Details

```tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { VirtualDataTable } from '@/components/ui/DataTable/VirtualDataTable';
import { ColumnDef } from '@tanstack/react-table';

interface Application {
  id: number;
  jobTitle: string;
  company: string;
  status: 'applied' | 'interviewing' | 'offer' | 'rejected';
  appliedDate: string;
  notes: string;
}

const applicationColumns: ColumnDef<Application>[] = [
  {
    accessorKey: 'jobTitle',
    header: 'Job Title',
  },
  {
    accessorKey: 'company',
    header: 'Company',
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ getValue }) => {
      const status = getValue() as string;
      const colors = {
        applied: 'bg-blue-100 text-blue-800',
        interviewing: 'bg-yellow-100 text-yellow-800',
        offer: 'bg-green-100 text-green-800',
        rejected: 'bg-red-100 text-red-800',
      };
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors]}`}>
          {status}
        </span>
      );
    },
  },
  {
    accessorKey: 'appliedDate',
    header: 'Applied Date',
  },
];

export default function ApplicationsPage() {
  const { data: applications = [], isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: async () => {
      const response = await fetch('/api/applications');
      return response.json();
    },
  });

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">My Applications</h1>

      <VirtualDataTable
        columns={applicationColumns}
        data={applications}
        isLoading={isLoading}
        renderSubComponent={(application) => (
          <div className="p-6 bg-neutral-50 dark:bg-neutral-900">
            <h3 className="font-semibold text-lg mb-4">Application Details</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">Job Title</p>
                <p className="font-medium">{application.jobTitle}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">Company</p>
                <p className="font-medium">{application.company}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">Status</p>
                <p className="font-medium">{application.status}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">Applied Date</p>
                <p className="font-medium">{application.appliedDate}</p>
              </div>
            </div>
            {application.notes && (
              <div className="mt-4">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">Notes</p>
                <p className="mt-1">{application.notes}</p>
              </div>
            )}
          </div>
        )}
      />
    </div>
  );
}
```

### Example 3: Analytics Dashboard with Custom Columns

```tsx
'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { VirtualDataTable } from '@/components/ui/DataTable/VirtualDataTable';
import { ColumnDef } from '@tanstack/react-table';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface Metric {
  id: number;
  name: string;
  value: number;
  previousValue: number;
  change: number;
  category: string;
}

export default function AnalyticsDashboard() {
  const { data: metrics = [], isLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      const response = await fetch('/api/analytics/metrics');
      return response.json();
    },
  });

  const columns: ColumnDef<Metric>[] = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Metric',
        size: 250,
      },
      {
        accessorKey: 'value',
        header: 'Current Value',
        size: 150,
        cell: ({ getValue }) => {
          const value = getValue() as number;
          return value.toLocaleString();
        },
      },
      {
        accessorKey: 'previousValue',
        header: 'Previous Value',
        size: 150,
        cell: ({ getValue }) => {
          const value = getValue() as number;
          return value.toLocaleString();
        },
      },
      {
        accessorKey: 'change',
        header: 'Change',
        size: 120,
        cell: ({ getValue }) => {
          const change = getValue() as number;
          const isPositive = change > 0;
          return (
            <div className={`flex items-center gap-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              <span className="font-medium">{Math.abs(change)}%</span>
            </div>
          );
        },
      },
      {
        accessorKey: 'category',
        header: 'Category',
        size: 150,
      },
    ],
    []
  );

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Analytics Dashboard</h1>

      <VirtualDataTable
        columns={columns}
        data={metrics}
        isLoading={isLoading}
        estimatedRowHeight={60}
      />
    </div>
  );
}
```

## Performance Optimization Tips

### 1. Memoize Column Definitions

```tsx
const columns = useMemo<ColumnDef<DataType>[]>(
  () => [
    // ... column definitions
  ],
  [] // Empty dependency array if columns don't change
);
```

### 2. Optimize Cell Renderers

```tsx
// ❌ Bad: Creates new component on every render
{
  cell: ({ getValue }) => {
    return <CustomComponent value={getValue()} />;
  }
}

// ✅ Good: Use memoized component
const MemoizedCustomComponent = memo(CustomComponent);

{
  cell: ({ getValue }) => {
    return <MemoizedCustomComponent value={getValue()} />;
  }
}
```

### 3. Use Appropriate Row Height

```tsx
// Measure your actual row height and set it accurately
<VirtualDataTable
  estimatedRowHeight={65} // Adjust based on your content
/>
```

### 4. Enable Performance Monitoring in Development

```tsx
<VirtualDataTable
  enablePerformanceMonitoring={process.env.NODE_ENV === 'development'}
/>
```

## Common Patterns

### Pattern 1: Lazy Loading with Infinite Scroll

```tsx
// Note: VirtualDataTable uses pagination by default
// For infinite scroll, consider using VirtualJobList or VirtualApplicationList instead
```

### Pattern 2: Real-time Updates

```tsx
function LiveDataTable() {
  const { data, isLoading } = useQuery({
    queryKey: ['live-data'],
    queryFn: fetchData,
    refetchInterval: 5000, // Refetch every 5 seconds
  });

  return (
    <VirtualDataTable
      columns={columns}
      data={data ?? []}
      isLoading={isLoading}
    />
  );
}
```

### Pattern 3: Bulk Actions

```tsx
function DataTableWithBulkActions() {
  const [selectedRows, setSelectedRows] = useState<number[]>([]);

  const handleBulkDelete = async () => {
    await deleteItems(selectedRows);
    // Refetch data
  };

  return (
    <>
      {selectedRows.length > 0 && (
        <div className="mb-4">
          <button onClick={handleBulkDelete}>
            Delete {selectedRows.length} items
          </button>
        </div>
      )}
      <VirtualDataTable
        columns={columns}
        data={data}
        // Row selection is built-in
      />
    </>
  );
}
```

## Troubleshooting

### Issue: Table doesn't scroll smoothly

**Solution**: Increase the overscan value

```tsx
<VirtualDataTable overscan={10} />
```

### Issue: Rows are misaligned

**Solution**: Adjust the estimated row height

```tsx
<VirtualDataTable estimatedRowHeight={70} />
```

### Issue: Performance is poor with large datasets

**Solution**: 
1. Ensure virtualization is enabled (check for "Virtualized" indicator)
2. Optimize cell renderers
3. Use memoization for columns and expensive computations

### Issue: Export doesn't work

**Solution**: The export functionality is built-in. Make sure you're using the Export dropdown in the table toolbar.

## Next Steps

- Review the [README](./README.md) for detailed API documentation
- Check out the [Storybook stories](./VirtualDataTable.stories.tsx) for interactive examples
- Run the benchmark tool to test performance with your data
- Read the [TanStack Table documentation](https://tanstack.com/table/v8) for advanced features
