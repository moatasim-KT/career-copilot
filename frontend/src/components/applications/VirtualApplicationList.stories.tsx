/**
 * VirtualApplicationList Storybook Stories
 * 
 * Interactive documentation and testing for the VirtualApplicationList component.
 */

import type { Meta, StoryObj } from '@storybook/react';
import React, { useState } from 'react';

import { VirtualApplicationList, VirtualApplicationListGrid } from './VirtualApplicationList';
import { Application } from '@/components/ui/ApplicationCard';

/**
 * Generate mock application data
 */
function generateMockApplication(id: number, overrides?: Partial<Application>): Application {
  const statuses = ['interested', 'applied', 'interview', 'offer', 'rejected', 'accepted', 'declined'];
  const companies = ['TechCorp', 'InnovateLabs', 'DataSystems', 'CloudServices', 'AI Solutions', 'DevTools Inc'];
  const titles = ['Software Engineer', 'Senior Developer', 'Full Stack Engineer', 'Backend Developer', 'Frontend Developer', 'DevOps Engineer'];
  const locations = ['Remote', 'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA', 'Boston, MA'];

  const daysAgo = Math.floor(Math.random() * 60);
  const appliedDate = new Date(Date.now() - daysAgo * 86400000);

  return {
    id,
    user_id: 1,
    job_id: id * 10,
    status: statuses[id % statuses.length],
    applied_date: appliedDate.toISOString(),
    response_date: Math.random() > 0.7 ? new Date(appliedDate.getTime() + 7 * 86400000).toISOString() : null,
    interview_date: Math.random() > 0.8 ? new Date(appliedDate.getTime() + 14 * 86400000).toISOString() : null,
    offer_date: Math.random() > 0.9 ? new Date(appliedDate.getTime() + 21 * 86400000).toISOString() : null,
    notes: Math.random() > 0.5 ? `Follow up with hiring manager. Great company culture and benefits. Team seems collaborative and innovative.` : null,
    interview_feedback: null,
    follow_up_date: Math.random() > 0.7 ? new Date(appliedDate.getTime() + 10 * 86400000).toISOString() : null,
    created_at: appliedDate.toISOString(),
    updated_at: new Date().toISOString(),
    job_title: titles[id % titles.length],
    company_name: companies[id % companies.length],
    job_location: locations[id % locations.length],
    ...overrides,
  };
}

/**
 * Generate multiple mock applications
 */
function generateMockApplications(count: number): Application[] {
  return Array.from({ length: count }, (_, i) => generateMockApplication(i + 1));
}

const meta: Meta<typeof VirtualApplicationList> = {
  title: 'Components/Applications/VirtualApplicationList',
  component: VirtualApplicationList,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
# VirtualApplicationList

A high-performance virtualized list component for displaying large numbers of applications.
Uses \`@tanstack/react-virtual\` to render only visible items, ensuring smooth scrolling
even with thousands of applications.

## Features

- **Virtual Scrolling**: Only renders visible items for optimal performance
- **Smooth Animations**: Framer Motion animations for delightful interactions
- **Selection Support**: Multi-select with visual feedback
- **Responsive Design**: Adapts to different screen sizes
- **Accessibility**: Full keyboard navigation and screen reader support
- **Empty States**: Helpful messages when no applications are available
- **Variants**: Multiple display modes (default, compact, detailed)

## Performance

Tested with 1000+ applications, maintaining 60fps scrolling performance.
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    applications: {
      description: 'Array of application objects to display',
      control: false,
    },
    onApplicationClick: {
      description: 'Callback when an application is clicked',
      action: 'application clicked',
    },
    selectedApplicationIds: {
      description: 'Array of selected application IDs',
      control: false,
    },
    onSelectApplication: {
      description: 'Callback when an application is selected/deselected',
      action: 'application selected',
    },
    estimatedSize: {
      description: 'Estimated height of each application card in pixels',
      control: { type: 'number', min: 100, max: 500, step: 10 },
    },
    overscan: {
      description: 'Number of items to render outside the visible area',
      control: { type: 'number', min: 0, max: 20, step: 1 },
    },
    variant: {
      description: 'Card display variant',
      control: { type: 'select' },
      options: ['default', 'compact', 'detailed'],
    },
    emptyMessage: {
      description: 'Custom message to display when no applications are available',
      control: 'text',
    },
  },
};

export default meta;
type Story = StoryObj<typeof VirtualApplicationList>;

/**
 * Interactive wrapper component for stories
 */
function InteractiveWrapper({ 
  applications, 
  variant = 'default',
  estimatedSize = 220,
  overscan = 5,
}: { 
  applications: Application[];
  variant?: 'default' | 'compact' | 'detailed';
  estimatedSize?: number;
  overscan?: number;
}) {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const handleSelect = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(selectedId => selectedId !== id)
        : [...prev, id]
    );
  };

  const handleClick = (id: number) => {
    console.log('Application clicked:', id);
  };

  return (
    <div className="h-screen p-6 bg-neutral-50 dark:bg-neutral-900">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
          Applications ({applications.length})
        </h2>
        {selectedIds.length > 0 && (
          <div className="flex items-center gap-4">
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              {selectedIds.length} selected
            </span>
            <button
              onClick={() => setSelectedIds([])}
              className="px-3 py-1 text-sm bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 rounded hover:bg-neutral-300 dark:hover:bg-neutral-600"
            >
              Clear Selection
            </button>
          </div>
        )}
      </div>
      <VirtualApplicationList
        applications={applications}
        onApplicationClick={handleClick}
        selectedApplicationIds={selectedIds}
        onSelectApplication={handleSelect}
        variant={variant}
        estimatedSize={estimatedSize}
        overscan={overscan}
      />
    </div>
  );
}

/**
 * Default story with a small list
 */
export const Default: Story = {
  render: () => <InteractiveWrapper applications={generateMockApplications(10)} />,
};

/**
 * Empty state
 */
export const Empty: Story = {
  render: () => <InteractiveWrapper applications={[]} />,
};

/**
 * Large list (100 applications)
 */
export const LargeList: Story = {
  render: () => <InteractiveWrapper applications={generateMockApplications(100)} />,
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates performance with 100 applications. Scroll smoothly through the list.',
      },
    },
  },
};

/**
 * Very large list (1000 applications)
 */
export const VeryLargeList: Story = {
  render: () => <InteractiveWrapper applications={generateMockApplications(1000)} />,
  parameters: {
    docs: {
      description: {
        story: 'Stress test with 1000 applications. Notice the smooth scrolling performance thanks to virtualization.',
      },
    },
  },
};

/**
 * Compact variant
 */
export const CompactVariant: Story = {
  render: () => <InteractiveWrapper applications={generateMockApplications(50)} variant="compact" estimatedSize={120} />,
  parameters: {
    docs: {
      description: {
        story: 'Compact variant shows minimal information, useful for dense lists.',
      },
    },
  },
};

/**
 * Detailed variant
 */
export const DetailedVariant: Story = {
  render: () => <InteractiveWrapper applications={generateMockApplications(20)} variant="detailed" estimatedSize={280} />,
  parameters: {
    docs: {
      description: {
        story: 'Detailed variant shows full application information including notes and dates.',
      },
    },
  },
};

/**
 * With pre-selected items
 */
export const WithSelection: Story = {
  render: () => {
    const applications = generateMockApplications(20);
    const [selectedIds, setSelectedIds] = useState<number[]>([1, 3, 5, 7]);

    const handleSelect = (id: number) => {
      setSelectedIds(prev => 
        prev.includes(id) 
          ? prev.filter(selectedId => selectedId !== id)
          : [...prev, id]
      );
    };

    return (
      <div className="h-screen p-6 bg-neutral-50 dark:bg-neutral-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            Applications with Pre-selection
          </h2>
          <div className="flex items-center gap-4">
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              {selectedIds.length} selected
            </span>
            <button
              onClick={() => setSelectedIds([])}
              className="px-3 py-1 text-sm bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 rounded hover:bg-neutral-300 dark:hover:bg-neutral-600"
            >
              Clear Selection
            </button>
            <button
              onClick={() => setSelectedIds(applications.map(a => a.id))}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Select All
            </button>
          </div>
        </div>
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={(id) => console.log('Clicked:', id)}
          selectedApplicationIds={selectedIds}
          onSelectApplication={handleSelect}
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates selection functionality with some items pre-selected.',
      },
    },
  },
};

/**
 * Grid layout story
 */
export const GridLayout: Story = {
  render: () => {
    const applications = generateMockApplications(50);
    const [selectedIds, setSelectedIds] = useState<number[]>([]);

    const handleSelect = (id: number) => {
      setSelectedIds(prev => 
        prev.includes(id) 
          ? prev.filter(selectedId => selectedId !== id)
          : [...prev, id]
      );
    };

    return (
      <div className="h-screen p-6 bg-neutral-50 dark:bg-neutral-900">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            Grid Layout
          </h2>
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
            Responsive grid that adapts to screen size
          </p>
        </div>
        <VirtualApplicationListGrid
          applications={applications}
          onApplicationClick={(id) => console.log('Clicked:', id)}
          selectedApplicationIds={selectedIds}
          onSelectApplication={handleSelect}
          columns={{ sm: 1, md: 2, lg: 3, xl: 4 }}
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Grid layout variant that displays applications in a responsive grid.',
      },
    },
  },
};

/**
 * Different status types
 */
export const DifferentStatuses: Story = {
  render: () => {
    const applications = [
      generateMockApplication(1, { status: 'interested', job_title: 'Interested Position' }),
      generateMockApplication(2, { status: 'applied', job_title: 'Applied Position' }),
      generateMockApplication(3, { status: 'interview', job_title: 'Interview Scheduled', interview_date: new Date().toISOString() }),
      generateMockApplication(4, { status: 'offer', job_title: 'Offer Received', offer_date: new Date().toISOString() }),
      generateMockApplication(5, { status: 'rejected', job_title: 'Rejected Application' }),
      generateMockApplication(6, { status: 'accepted', job_title: 'Accepted Offer' }),
      generateMockApplication(7, { status: 'declined', job_title: 'Declined Offer' }),
    ];

    return <InteractiveWrapper applications={applications} variant="detailed" />;
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows all different application statuses with appropriate badge colors.',
      },
    },
  },
};

/**
 * Custom empty message
 */
export const CustomEmptyMessage: Story = {
  render: () => {
    const [selectedIds, setSelectedIds] = useState<number[]>([]);

    return (
      <div className="h-screen p-6 bg-neutral-50 dark:bg-neutral-900">
        <VirtualApplicationList
          applications={[]}
          onApplicationClick={(id) => console.log('Clicked:', id)}
          selectedApplicationIds={selectedIds}
          onSelectApplication={(id) => setSelectedIds(prev => [...prev, id])}
          emptyMessage="You haven't applied to any jobs yet. Start your job search today!"
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates custom empty state message.',
      },
    },
  },
};

/**
 * Performance benchmark
 */
export const PerformanceBenchmark: Story = {
  render: () => {
    const [count, setCount] = useState(100);
    const applications = generateMockApplications(count);

    return (
      <div className="h-screen p-6 bg-neutral-50 dark:bg-neutral-900">
        <div className="mb-4 flex items-center gap-4">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            Performance Test
          </h2>
          <div className="flex items-center gap-2">
            <label className="text-sm text-neutral-600 dark:text-neutral-400">
              Count:
            </label>
            <input
              type="number"
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="px-3 py-1 border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100"
              min="10"
              max="10000"
              step="100"
            />
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              applications
            </span>
          </div>
        </div>
        <InteractiveWrapper applications={applications} />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive performance test. Adjust the count to test with different dataset sizes.',
      },
    },
  },
};
