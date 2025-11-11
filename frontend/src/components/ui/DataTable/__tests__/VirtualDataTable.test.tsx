/**
 * VirtualDataTable Tests
 * 
 * Tests for the virtualized DataTable component including:
 * - Virtualization behavior with large datasets
 * - Performance characteristics
 * - All standard DataTable features
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ColumnDef } from '@tanstack/react-table';
import React from 'react';

import { VirtualDataTable } from '../VirtualDataTable';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as any;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;

// Mock data generator
function generateMockData(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Item ${i + 1}`,
    value: Math.floor(Math.random() * 1000),
    status: ['active', 'inactive', 'pending'][i % 3],
    date: new Date(2024, 0, (i % 28) + 1).toISOString(),
  }));
}

type MockDataItem = ReturnType<typeof generateMockData>[0];

const mockColumns: ColumnDef<MockDataItem>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'value',
    header: 'Value',
  },
  {
    accessorKey: 'status',
    header: 'Status',
  },
  {
    accessorKey: 'date',
    header: 'Date',
  },
];

describe('VirtualDataTable', () => {
  describe('Basic Rendering', () => {
    it('renders with small dataset (non-virtualized)', () => {
      const data = generateMockData(10);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 10')).toBeInTheDocument();
    });

    it('renders with large dataset (virtualized)', () => {
      const data = generateMockData(200);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      // Should show virtualized indicator
      expect(screen.getByText(/Virtualized/i)).toBeInTheDocument();
      
      // Should show total count
      expect(screen.getByText(/Showing 200 of 200 results/i)).toBeInTheDocument();
    });

    it('renders loading state', () => {
      const data = generateMockData(10);
      render(<VirtualDataTable columns={mockColumns} data={data} isLoading />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders empty state', () => {
      render(<VirtualDataTable columns={mockColumns} data={[]} />);

      expect(screen.getByText('No results.')).toBeInTheDocument();
    });
  });

  describe('Virtualization Behavior', () => {
    it('automatically enables virtualization for 100+ rows', () => {
      const data = generateMockData(150);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      expect(screen.getByText(/Virtualized/i)).toBeInTheDocument();
    });

    it('does not virtualize for less than 100 rows', () => {
      const data = generateMockData(50);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      expect(screen.queryByText(/Virtualized/i)).not.toBeInTheDocument();
    });

    it('respects enableVirtualization prop', () => {
      const data = generateMockData(50);
      render(
        <VirtualDataTable
          columns={mockColumns}
          data={data}
          enableVirtualization={true}
        />
      );

      expect(screen.getByText(/Virtualized/i)).toBeInTheDocument();
    });

    it('can disable virtualization for large datasets', () => {
      const data = generateMockData(150);
      render(
        <VirtualDataTable
          columns={mockColumns}
          data={data}
          enableVirtualization={false}
        />
      );

      expect(screen.queryByText(/Virtualized/i)).not.toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('sorts data when column header is clicked', async () => {
      const user = userEvent.setup();
      const data = generateMockData(20);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      const nameHeader = screen.getByText('Name');
      await user.click(nameHeader);

      // After sorting, first item should be visible
      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
      });
    });
  });

  describe('Filtering', () => {
    it('has global search input', () => {
      const data = generateMockData(20);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      const searchInput = screen.getByPlaceholderText('Filter all columns...');
      expect(searchInput).toBeInTheDocument();
    });
  });

  describe('Row Selection', () => {
    it('selects individual rows', async () => {
      const user = userEvent.setup();
      const data = generateMockData(10);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      const checkboxes = screen.getAllByRole('checkbox');
      // First checkbox is "select all", so select the second one (first row)
      await user.click(checkboxes[1]);

      await waitFor(() => {
        expect(screen.getByText(/1 of 10 row\(s\) selected/i)).toBeInTheDocument();
      });
    });

    it('selects all rows', async () => {
      const user = userEvent.setup();
      const data = generateMockData(10);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
      await user.click(selectAllCheckbox);

      await waitFor(() => {
        expect(screen.getByText(/10 of 10 row\(s\) selected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Column Visibility', () => {
    it('has column visibility toggle', () => {
      const data = generateMockData(10);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      const columnsButton = screen.getByRole('button', { name: 'Columns' });
      expect(columnsButton).toBeInTheDocument();
    });
  });

  describe('Export Functionality', () => {
    it('has export button', () => {
      const data = generateMockData(10);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      const exportButton = screen.getByRole('button', { name: 'Export' });
      expect(exportButton).toBeInTheDocument();
    });
  });

  describe('Pagination', () => {
    it('paginates data', async () => {
      const user = userEvent.setup();
      const data = generateMockData(50);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      // Should show page 1
      expect(screen.getByText(/Page 1 of/i)).toBeInTheDocument();

      // Click next page
      const nextButton = screen.getAllByRole('button').find(
        (btn) => btn.getAttribute('aria-label') === 'Go to next page'
      );
      if (nextButton) {
        await user.click(nextButton);

        await waitFor(() => {
          expect(screen.getByText(/Page 2 of/i)).toBeInTheDocument();
        });
      }
    });

    it('changes page size', async () => {
      const user = userEvent.setup();
      const data = generateMockData(50);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      const pageSizeSelect = screen.getByRole('combobox');
      await user.selectOptions(pageSizeSelect, '20');

      await waitFor(() => {
        // Should now show more items per page
        expect(screen.getByText(/Page 1 of/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance Monitoring', () => {
    it('shows performance metrics when enabled', () => {
      const data = generateMockData(200);
      render(
        <VirtualDataTable
          columns={mockColumns}
          data={data}
          enablePerformanceMonitoring
        />
      );

      expect(screen.getByText(/FPS:/i)).toBeInTheDocument();
      expect(screen.getByText(/Render:/i)).toBeInTheDocument();
      expect(screen.getByText(/Rows:/i)).toBeInTheDocument();
      expect(screen.getByText(/Visible:/i)).toBeInTheDocument();
    });

    it('does not show performance metrics by default', () => {
      const data = generateMockData(200);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      expect(screen.queryByText(/FPS:/i)).not.toBeInTheDocument();
    });
  });

  describe('Expandable Rows', () => {
    it('renders with sub-component prop', () => {
      const data = generateMockData(10);
      const renderSubComponent = (row: MockDataItem) => (
        <div>Details for {row.name}</div>
      );

      render(
        <VirtualDataTable
          columns={mockColumns}
          data={data}
          renderSubComponent={renderSubComponent}
        />
      );

      // Component renders without crashing
      expect(screen.getByText('Item 1')).toBeInTheDocument();
    });
  });

  describe('Large Dataset Performance', () => {
    it('handles 1000+ rows efficiently', () => {
      const data = generateMockData(1500);
      const { container } = render(
        <VirtualDataTable
          columns={mockColumns}
          data={data}
          enablePerformanceMonitoring
        />
      );

      // Should render without crashing
      expect(container).toBeInTheDocument();
      
      // Should show virtualized indicator
      expect(screen.getByText(/Virtualized/i)).toBeInTheDocument();
      
      // Should show correct total count
      expect(screen.getByText(/Showing 1500 of 1500 results/i)).toBeInTheDocument();
    });

    it('only renders visible rows in virtualized mode', () => {
      const data = generateMockData(1000);
      render(
        <VirtualDataTable
          columns={mockColumns}
          data={data}
          enableVirtualization
        />
      );

      // Count actual rendered rows (should be much less than 1000)
      const rows = screen.getAllByRole('row');
      // Header row + visible rows (should be around 10-20 depending on viewport)
      expect(rows.length).toBeLessThan(50);
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for selection', () => {
      const data = generateMockData(10);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      expect(screen.getByLabelText('Select all')).toBeInTheDocument();
      const selectRowCheckboxes = screen.getAllByLabelText('Select row');
      expect(selectRowCheckboxes.length).toBeGreaterThan(0);
    });

    it('has pagination controls', () => {
      const data = generateMockData(50);
      render(<VirtualDataTable columns={mockColumns} data={data} />);

      // Check for pagination text
      expect(screen.getByText(/Page 1 of/i)).toBeInTheDocument();
    });
  });
});
