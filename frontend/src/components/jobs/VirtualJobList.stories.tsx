/**
 * VirtualJobList Storybook Stories
 * 
 * Interactive documentation and testing for the VirtualJobList component.
 * Demonstrates various use cases and configurations.
 */

import type { Meta, StoryObj } from '@storybook/react';
import React, { useState } from 'react';

import { VirtualJobList, VirtualJobListGrid } from './VirtualJobList';

// Generate mock jobs for testing
const generateMockJobs = (count: number) => {
  const companies = ['Google', 'Microsoft', 'Apple', 'Amazon', 'Meta', 'Netflix', 'Tesla', 'SpaceX'];
  const locations = ['San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX', 'Remote'];
  const types = ['full-time', 'part-time', 'contract', 'internship'];
  const titles = [
    'Senior Software Engineer',
    'Frontend Developer',
    'Backend Engineer',
    'Full Stack Developer',
    'DevOps Engineer',
    'Data Scientist',
    'Product Manager',
    'UX Designer',
  ];

  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: titles[i % titles.length],
    company: companies[i % companies.length],
    location: locations[i % locations.length],
    type: types[i % types.length],
    postedAt: `${Math.floor(Math.random() * 30) + 1} days ago`,
    salary_range: `$${80 + Math.floor(Math.random() * 100)}k - $${120 + Math.floor(Math.random() * 100)}k`,
    remote: Math.random() > 0.5,
    tech_stack: ['React', 'TypeScript', 'Node.js'].slice(0, Math.floor(Math.random() * 3) + 1),
  }));
};

const meta: Meta<typeof VirtualJobList> = {
  title: 'Components/Jobs/VirtualJobList',
  component: VirtualJobList,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
# VirtualJobList

A high-performance virtualized job list component that efficiently renders large lists of jobs.
Only renders visible items in the viewport for optimal performance with 100+ jobs.

## Features

- ✅ Virtual scrolling for performance
- ✅ Smooth animations with Framer Motion
- ✅ Configurable overscan
- ✅ Selection support
- ✅ Responsive design
- ✅ Empty state handling
- ✅ Accessibility compliant

## Performance

The component uses \`@tanstack/react-virtual\` to render only visible items plus a configurable overscan.
This allows it to handle thousands of jobs without performance degradation.

## Usage

\`\`\`tsx
<VirtualJobList
  jobs={jobs}
  onJobClick={(id) => router.push(\`/jobs/\${id}\`)}
  selectedJobIds={selectedIds}
  onSelectJob={handleSelect}
  estimatedSize={220}
  overscan={5}
/>
\`\`\`
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    jobs: {
      description: 'Array of jobs to display',
      control: false,
    },
    onJobClick: {
      description: 'Callback when a job is clicked',
      action: 'job clicked',
    },
    selectedJobIds: {
      description: 'Array of selected job IDs',
      control: false,
    },
    onSelectJob: {
      description: 'Callback when a job is selected/deselected',
      action: 'job selected',
    },
    estimatedSize: {
      description: 'Estimated height of each job card in pixels',
      control: { type: 'number', min: 100, max: 500, step: 10 },
    },
    overscan: {
      description: 'Number of items to render outside the visible area',
      control: { type: 'number', min: 0, max: 20, step: 1 },
    },
    className: {
      description: 'Custom className for the container',
      control: 'text',
    },
    emptyMessage: {
      description: 'Custom empty state message',
      control: 'text',
    },
  },
};

export default meta;
type Story = StoryObj<typeof VirtualJobList>;

/**
 * Interactive wrapper component for stories
 */
const VirtualJobListWrapper = (args: any) => {
  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);

  const handleSelectJob = (jobId: number) => {
    setSelectedJobIds((prev) =>
      prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]
    );
  };

  return (
    <div className="h-screen p-4 bg-neutral-50 dark:bg-neutral-900">
      <div className="mb-4 text-sm text-neutral-600 dark:text-neutral-400">
        Selected: {selectedJobIds.length} jobs
      </div>
      <VirtualJobList
        {...args}
        selectedJobIds={selectedJobIds}
        onSelectJob={handleSelectJob}
      />
    </div>
  );
};

/**
 * Default story with a small list of jobs
 */
export const Default: Story = {
  render: (args) => <VirtualJobListWrapper {...args} />,
  args: {
    jobs: generateMockJobs(10),
    estimatedSize: 200,
    overscan: 5,
  },
};

/**
 * Empty state when no jobs are available
 */
export const EmptyState: Story = {
  render: (args) => <VirtualJobListWrapper {...args} />,
  args: {
    jobs: [],
    emptyMessage: 'No jobs found. Try adjusting your filters.',
  },
};

/**
 * Large list with 100 jobs to demonstrate virtualization
 */
export const LargeList: Story = {
  render: (args) => <VirtualJobListWrapper {...args} />,
  args: {
    jobs: generateMockJobs(100),
    estimatedSize: 200,
    overscan: 5,
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates virtualization with 100 jobs. Only visible items are rendered for optimal performance.',
      },
    },
  },
};

/**
 * Very large list with 1000 jobs
 */
export const VeryLargeList: Story = {
  render: (args) => <VirtualJobListWrapper {...args} />,
  args: {
    jobs: generateMockJobs(1000),
    estimatedSize: 200,
    overscan: 5,
  },
  parameters: {
    docs: {
      description: {
        story: 'Stress test with 1000 jobs. Virtualization ensures smooth scrolling and performance.',
      },
    },
  },
};

/**
 * Custom estimated size for taller job cards
 */
export const CustomEstimatedSize: Story = {
  render: (args) => <VirtualJobListWrapper {...args} />,
  args: {
    jobs: generateMockJobs(50),
    estimatedSize: 300,
    overscan: 5,
  },
  parameters: {
    docs: {
      description: {
        story: 'Uses a larger estimated size (300px) for taller job cards.',
      },
    },
  },
};

/**
 * Higher overscan for smoother scrolling
 */
export const HighOverscan: Story = {
  render: (args) => <VirtualJobListWrapper {...args} />,
  args: {
    jobs: generateMockJobs(100),
    estimatedSize: 200,
    overscan: 15,
  },
  parameters: {
    docs: {
      description: {
        story: 'Uses higher overscan (15 items) for smoother scrolling at the cost of rendering more items.',
      },
    },
  },
};

/**
 * Custom empty message
 */
export const CustomEmptyMessage: Story = {
  render: (args) => <VirtualJobListWrapper {...args} />,
  args: {
    jobs: [],
    emptyMessage: 'No matching jobs found. Try broadening your search criteria or check back later for new opportunities.',
  },
};

/**
 * Grid layout variant
 */
const VirtualJobListGridWrapper = (args: any) => {
  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);

  const handleSelectJob = (jobId: number) => {
    setSelectedJobIds((prev) =>
      prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]
    );
  };

  return (
    <div className="h-screen p-4 bg-neutral-50 dark:bg-neutral-900">
      <div className="mb-4 text-sm text-neutral-600 dark:text-neutral-400">
        Selected: {selectedJobIds.length} jobs
      </div>
      <VirtualJobListGrid
        {...args}
        selectedJobIds={selectedJobIds}
        onSelectJob={handleSelectJob}
      />
    </div>
  );
};

export const GridLayout: Story = {
  render: (args) => <VirtualJobListGridWrapper {...args} />,
  args: {
    jobs: generateMockJobs(50),
    estimatedSize: 220,
    overscan: 5,
    columns: { sm: 1, md: 2, lg: 3 },
  },
  parameters: {
    docs: {
      description: {
        story: 'Grid layout variant that displays jobs in a responsive grid. Automatically adjusts columns based on viewport width.',
      },
    },
  },
};

/**
 * Grid with many jobs
 */
export const GridLargeList: Story = {
  render: (args) => <VirtualJobListGridWrapper {...args} />,
  args: {
    jobs: generateMockJobs(200),
    estimatedSize: 220,
    overscan: 5,
    columns: { sm: 1, md: 2, lg: 3, xl: 4 },
  },
  parameters: {
    docs: {
      description: {
        story: 'Grid layout with 200 jobs and 4 columns on extra-large screens.',
      },
    },
  },
};

/**
 * Performance comparison
 */
export const PerformanceTest: Story = {
  render: () => {
    const [jobCount, setJobCount] = useState(100);
    const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);
    const jobs = generateMockJobs(jobCount);

    const handleSelectJob = (jobId: number) => {
      setSelectedJobIds((prev) =>
        prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]
      );
    };

    return (
      <div className="h-screen p-4 bg-neutral-50 dark:bg-neutral-900">
        <div className="mb-4 space-y-2">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
              Number of jobs: {jobCount}
            </label>
            <input
              type="range"
              min="10"
              max="1000"
              step="10"
              value={jobCount}
              onChange={(e) => setJobCount(Number(e.target.value))}
              className="flex-1"
            />
          </div>
          <div className="text-sm text-neutral-600 dark:text-neutral-400">
            Selected: {selectedJobIds.length} jobs
          </div>
        </div>
        <VirtualJobList
          jobs={jobs}
          onJobClick={(id) => console.log('Clicked job:', id)}
          selectedJobIds={selectedJobIds}
          onSelectJob={handleSelectJob}
          estimatedSize={200}
          overscan={5}
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive performance test. Adjust the slider to test with different numbers of jobs (10-1000).',
      },
    },
  },
};
