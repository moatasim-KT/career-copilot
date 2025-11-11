/**
 * VirtualDataTable Storybook Stories
 * 
 * Interactive stories demonstrating the VirtualDataTable component
 * with various dataset sizes and configurations.
 */

import React, { useState } from 'react';
import { Meta, StoryObj } from '@storybook/react';
import { ColumnDef } from '@tanstack/react-table';

import { VirtualDataTable } from './VirtualDataTable';
import {
  runBenchmark,
  formatBenchmarkResults,
  comparePerformance,
  exportBenchmarkResults,
} from './benchmark';

// Mock data generator
function generateMockData(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Item ${i + 1}`,
    email: `user${i + 1}@example.com`,
    value: Math.floor(Math.random() * 10000),
    status: ['active', 'inactive', 'pending'][i % 3] as 'active' | 'inactive' | 'pending',
    date: new Date(2024, 0, (i % 28) + 1).toISOString().split('T')[0],
    category: ['A', 'B', 'C', 'D'][i % 4],
    priority: ['low', 'medium', 'high'][i % 3] as 'low' | 'medium' | 'high',
  }));
}

type MockDataItem = ReturnType<typeof generateMockData>[0];

const mockColumns: ColumnDef<MockDataItem>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
    size: 80,
  },
  {
    accessorKey: 'name',
    header: 'Name',
    size: 200,
  },
  {
    accessorKey: 'email',
    header: 'Email',
    size: 250,
  },
  {
    accessorKey: 'value',
    header: 'Value',
    size: 120,
    cell: ({ getValue }) => {
      const value = getValue() as number;
      return `$${value.toLocaleString()}`;
    },
  },
  {
    accessorKey: 'status',
    header: 'Status',
    size: 120,
    cell: ({ getValue }) => {
      const status = getValue() as string;
      const colors = {
        active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
        pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      };
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors]}`}>
          {status}
        </span>
      );
    },
  },
  {
    accessorKey: 'date',
    header: 'Date',
    size: 120,
  },
  {
    accessorKey: 'category',
    header: 'Category',
    size: 100,
  },
  {
    accessorKey: 'priority',
    header: 'Priority',
    size: 100,
    cell: ({ getValue }) => {
      const priority = getValue() as string;
      const colors = {
        low: 'text-blue-600 dark:text-blue-400',
        medium: 'text-yellow-600 dark:text-yellow-400',
        high: 'text-red-600 dark:text-red-400',
      };
      return (
        <span className={`font-medium ${colors[priority as keyof typeof colors]}`}>
          {priority}
        </span>
      );
    },
  },
];

const meta: Meta<typeof VirtualDataTable> = {
  title: 'Components/DataTable/VirtualDataTable',
  component: VirtualDataTable,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'A virtualized DataTable component that efficiently renders large datasets by only rendering visible rows.',
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof VirtualDataTable>;

// Small Dataset (Non-virtualized)
export const SmallDataset: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(20),
  },
  parameters: {
    docs: {
      description: {
        story: 'Small dataset with 20 rows. Virtualization is not enabled as it\'s below the 100-row threshold.',
      },
    },
  },
};

// Medium Dataset (Auto-virtualized)
export const MediumDataset: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(150),
  },
  parameters: {
    docs: {
      description: {
        story: 'Medium dataset with 150 rows. Virtualization is automatically enabled.',
      },
    },
  },
};

// Large Dataset (1000 rows)
export const LargeDataset: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(1000),
  },
  parameters: {
    docs: {
      description: {
        story: 'Large dataset with 1000 rows. Demonstrates smooth scrolling with virtualization.',
      },
    },
  },
};

// Extra Large Dataset (5000 rows)
export const ExtraLargeDataset: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(5000),
  },
  parameters: {
    docs: {
      description: {
        story: 'Extra large dataset with 5000 rows. Tests virtualization performance at scale.',
      },
    },
  },
};

// With Performance Monitoring
export const WithPerformanceMonitoring: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(1000),
    enablePerformanceMonitoring: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows real-time performance metrics including FPS, render time, and visible rows.',
      },
    },
  },
};

// Force Virtualization on Small Dataset
export const ForceVirtualization: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(50),
    enableVirtualization: true,
    enablePerformanceMonitoring: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Forces virtualization on a small dataset (50 rows) for testing purposes.',
      },
    },
  },
};

// Disable Virtualization on Large Dataset
export const DisableVirtualization: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(150),
    enableVirtualization: false,
    enablePerformanceMonitoring: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Disables virtualization on a large dataset to compare performance. May experience performance issues.',
      },
    },
  },
};

// With Expandable Rows
export const WithExpandableRows: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(200),
    renderSubComponent: (row: MockDataItem) => (
      <div className="p-4 bg-neutral-50 dark:bg-neutral-900">
        <h4 className="font-semibold mb-2">Details for {row.name}</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-neutral-600 dark:text-neutral-400">ID:</span>{' '}
            <span className="font-medium">{row.id}</span>
          </div>
          <div>
            <span className="text-neutral-600 dark:text-neutral-400">Email:</span>{' '}
            <span className="font-medium">{row.email}</span>
          </div>
          <div>
            <span className="text-neutral-600 dark:text-neutral-400">Value:</span>{' '}
            <span className="font-medium">${row.value.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-neutral-600 dark:text-neutral-400">Status:</span>{' '}
            <span className="font-medium">{row.status}</span>
          </div>
          <div>
            <span className="text-neutral-600 dark:text-neutral-400">Category:</span>{' '}
            <span className="font-medium">{row.category}</span>
          </div>
          <div>
            <span className="text-neutral-600 dark:text-neutral-400">Priority:</span>{' '}
            <span className="font-medium">{row.priority}</span>
          </div>
        </div>
      </div>
    ),
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates expandable rows with detailed sub-components.',
      },
    },
  },
};

// Loading State
export const LoadingState: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(100),
    isLoading: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows the loading state while data is being fetched.',
      },
    },
  },
};

// Empty State
export const EmptyState: Story = {
  args: {
    columns: mockColumns,
    data: [],
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows the empty state when no data is available.',
      },
    },
  },
};

// Custom Row Height
export const CustomRowHeight: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(500),
    estimatedRowHeight: 80,
    enablePerformanceMonitoring: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Uses a custom estimated row height of 80px instead of the default 53px.',
      },
    },
  },
};

// Custom Overscan
export const CustomOverscan: Story = {
  args: {
    columns: mockColumns,
    data: generateMockData(500),
    overscan: 10,
    enablePerformanceMonitoring: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Uses a custom overscan of 10 items (default is 5) for smoother scrolling.',
      },
    },
  },
};

// Interactive Benchmark Tool
export const BenchmarkTool: Story = {
  render: () => {
    const [datasetSize, setDatasetSize] = useState(1000);
    const [virtualized, setVirtualized] = useState(true);
    const [results, setResults] = useState<string>('');
    const [isRunning, setIsRunning] = useState(false);

    const runTest = async () => {
      setIsRunning(true);
      setResults('Running benchmark...');

      try {
        const data = generateMockData(datasetSize);
        const result = await runBenchmark(datasetSize, virtualized);
        const formatted = formatBenchmarkResults([result]);
        setResults(formatted);
      } catch (error) {
        setResults(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        setIsRunning(false);
      }
    };

    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-4">DataTable Performance Benchmark</h2>
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium mb-2">
                Dataset Size: {datasetSize} rows
              </label>
              <input
                type="range"
                min="100"
                max="5000"
                step="100"
                value={datasetSize}
                onChange={(e) => setDatasetSize(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={virtualized}
                  onChange={(e) => setVirtualized(e.target.checked)}
                />
                <span className="text-sm font-medium">Enable Virtualization</span>
              </label>
            </div>
            <button
              onClick={runTest}
              disabled={isRunning}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isRunning ? 'Running...' : 'Run Benchmark'}
            </button>
          </div>
          {results && (
            <div className="bg-neutral-100 dark:bg-neutral-900 p-4 rounded">
              <pre className="text-xs whitespace-pre-wrap">{results}</pre>
            </div>
          )}
        </div>
        <div data-testid="datatable-container">
          <VirtualDataTable
            columns={mockColumns}
            data={generateMockData(datasetSize)}
            enableVirtualization={virtualized}
            enablePerformanceMonitoring
          />
        </div>
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive benchmark tool to test performance with different configurations.',
      },
    },
  },
};
