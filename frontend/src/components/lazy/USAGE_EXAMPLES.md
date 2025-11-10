# Lazy Component Usage Examples

This document provides practical examples of how to use lazy-loaded components in your application.

## Page-Level Lazy Loading

### Analytics Page

**Before (Direct Import):**
```tsx
// app/analytics/page.tsx
import AnalyticsPage from '@/components/pages/AnalyticsPage';

export default function Analytics() {
  return <AnalyticsPage />;
}
```

**After (Lazy Loading):**
```tsx
// app/analytics/page.tsx
import { LazyAnalyticsPage } from '@/components/lazy';

export default function Analytics() {
  return <LazyAnalyticsPage />;
}
```

**Bundle Impact:** Reduces initial bundle by ~100KB (Recharts library)

### Enhanced Dashboard

```tsx
// app/dashboard/enhanced/page.tsx
import { LazyEnhancedDashboard } from '@/components/lazy';

export default function EnhancedDashboardPage() {
  return <LazyEnhancedDashboard />;
}
```

**Bundle Impact:** Reduces initial bundle by ~50KB (react-grid-layout)

## Modal/Dropdown Components

### Command Palette

```tsx
// app/layout.tsx
'use client';

import { useState } from 'react';
import { LazyCommandPalette } from '@/components/lazy';
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut';

export default function RootLayout({ children }) {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  
  // Open with Cmd+K / Ctrl+K
  useKeyboardShortcut('k', () => setIsCommandPaletteOpen(true), { 
    meta: true 
  });
  
  return (
    <html>
      <body>
        {children}
        
        {/* Only loads when opened */}
        <LazyCommandPalette
          isOpen={isCommandPaletteOpen}
          onClose={() => setIsCommandPaletteOpen(false)}
        />
      </body>
    </html>
  );
}
```

### Advanced Search

```tsx
// components/pages/JobsPage.tsx
'use client';

import { useState } from 'react';
import { LazyAdvancedSearch } from '@/components/lazy';
import { jobSearchFields } from '@/lib/searchFields';

export default function JobsPage() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  
  const handleSearch = (query) => {
    console.log('Search query:', query);
    // Apply search filters
  };
  
  return (
    <div>
      <button onClick={() => setIsSearchOpen(true)}>
        Advanced Search
      </button>
      
      {/* Only loads when opened */}
      <LazyAdvancedSearch
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSearch={handleSearch}
        fields={jobSearchFields}
      />
    </div>
  );
}
```

### Notification Center

```tsx
// components/layout/Navigation.tsx
'use client';

import { useState } from 'react';
import { Bell } from 'lucide-react';
import { LazyNotificationCenter } from '@/components/lazy';

export default function Navigation() {
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const unreadCount = 5; // From your state management
  
  return (
    <nav>
      <button 
        onClick={() => setIsNotificationsOpen(true)}
        className="relative"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>
      
      <LazyNotificationCenter
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
      />
    </nav>
  );
}
```

## Chart Components

### Using Individual Chart Types

```tsx
// components/charts/ApplicationStatusChart.tsx
'use client';

import { LazyPieChart, LazyChartComponents } from '@/components/lazy';

const { ResponsiveContainer, Pie, Cell, Tooltip, Legend } = LazyChartComponents;

export default function ApplicationStatusChart({ data }) {
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LazyPieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </LazyPieChart>
    </ResponsiveContainer>
  );
}
```

### Using Chart Wrapper

```tsx
// components/charts/TrendChart.tsx
'use client';

import { ChartWrapper, LazyLineChart, LazyChartComponents } from '@/components/lazy';

const { ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip, Line } = LazyChartComponents;

export default function TrendChart({ data }) {
  return (
    <ChartWrapper type="line">
      <ResponsiveContainer width="100%" height={300}>
        <LazyLineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="applications" stroke="#3B82F6" />
        </LazyLineChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
```

## Data Table

### Basic Usage

```tsx
// components/pages/ApplicationsTable.tsx
'use client';

import { LazyDataTable } from '@/components/lazy';
import { applicationColumns } from './columns';

export default function ApplicationsTable({ applications }) {
  return (
    <LazyDataTable
      columns={applicationColumns}
      data={applications}
      enableSorting
      enableFiltering
      enableColumnVisibility
      enableRowSelection
    />
  );
}
```

### With Custom Configuration

```tsx
// components/pages/JobsTable.tsx
'use client';

import { LazyDataTable } from '@/components/lazy';
import { jobColumns } from './columns';

export default function JobsTable({ jobs }) {
  return (
    <LazyDataTable
      columns={jobColumns}
      data={jobs}
      enableSorting
      enableFiltering
      enablePagination
      pageSize={20}
      enableRowSelection
      onRowSelectionChange={(selectedRows) => {
        console.log('Selected:', selectedRows);
      }}
    />
  );
}
```

## Rich Text Editor (Future)

```tsx
// components/features/NoteEditor.tsx
'use client';

import { useState } from 'react';
import { LazyRichTextEditor } from '@/components/lazy';

export default function NoteEditor() {
  const [content, setContent] = useState('');
  
  return (
    <div>
      <h2>Application Notes</h2>
      <LazyRichTextEditor
        value={content}
        onChange={setContent}
        placeholder="Add notes about this application..."
      />
    </div>
  );
}
```

## Testing Lazy Components

### Unit Test Example

```tsx
// __tests__/LazyComponent.test.tsx
import { render, waitFor } from '@testing-library/react';
import { LazyCommandPalette } from '@/components/lazy';

describe('LazyCommandPalette', () => {
  it('should not render when closed', () => {
    const { container } = render(
      <LazyCommandPalette isOpen={false} onClose={() => {}} />
    );
    
    expect(container.firstChild).toBeNull();
  });
  
  it('should show skeleton while loading', async () => {
    const { container } = render(
      <LazyCommandPalette isOpen={true} onClose={() => {}} />
    );
    
    // Skeleton should be visible
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });
});
```

## Performance Monitoring

### Measuring Bundle Impact

```bash
# Build with bundle analyzer
npm run analyze

# Check the generated report
# Look for separate chunks for:
# - recharts
# - react-grid-layout
# - cmdk
# - AdvancedSearch components
```

### Network Tab Verification

1. Open DevTools Network tab
2. Navigate to a page with lazy components
3. Verify chunks load on demand:
   - `recharts-[hash].js` loads only on Analytics page
   - `cmdk-[hash].js` loads only when Command Palette opens
   - `react-grid-layout-[hash].js` loads only on Enhanced Dashboard

## Best Practices

### 1. Conditional Rendering

Always check if modal/dropdown is open before rendering:

```tsx
// ✅ Good - Component only loads when needed
if (!isOpen) return null;
return <LazyComponent isOpen={isOpen} />;

// ❌ Bad - Component loads even when hidden
return <LazyComponent isOpen={isOpen} />;
```

### 2. Appropriate Skeletons

Use skeletons that match the final component:

```tsx
// ✅ Good - Skeleton matches chart layout
<ChartWrapper type="pie">
  <LazyPieChart />
</ChartWrapper>

// ❌ Bad - Generic skeleton doesn't match
<div>Loading...</div>
```

### 3. Error Boundaries

Wrap lazy components in error boundaries:

```tsx
import { ErrorBoundary } from '@/components/ErrorBoundary';

<ErrorBoundary fallback={<ErrorMessage />}>
  <LazyAnalyticsPage />
</ErrorBoundary>
```

### 4. Prefetching (Optional)

Prefetch lazy components on hover for instant loading:

```tsx
import { useState } from 'react';

function Navigation() {
  const [prefetchCommand, setPrefetchCommand] = useState(false);
  
  return (
    <button
      onMouseEnter={() => setPrefetchCommand(true)}
      onClick={() => setIsOpen(true)}
    >
      Search
    </button>
  );
}
```

## Troubleshooting

### Component Not Loading

**Problem:** Lazy component doesn't appear after opening

**Solution:**
1. Check browser console for errors
2. Verify component export is correct
3. Ensure Suspense boundary exists
4. Check network tab for chunk loading

### Hydration Errors

**Problem:** "Hydration failed" error in console

**Solution:**
1. Set `ssr: false` in dynamic import
2. Ensure skeleton structure matches component
3. Avoid using client-only APIs during SSR

### Performance Not Improving

**Problem:** Bundle size hasn't decreased

**Solution:**
1. Run `npm run analyze` to verify splitting
2. Ensure you're using lazy component, not direct import
3. Check component is actually heavy enough (>20KB)
4. Verify tree-shaking is working
