import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import Button2 from './Button2';
import Drawer2 from './Drawer2';

const meta: Meta<typeof Drawer2> = {
  title: 'UI/Drawer2',
  component: Drawer2,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Drawer2>;

// Wrapper component to handle state
const DrawerWrapper = (args: any) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="p-8">
      <Button2 onClick={() => setOpen(true)}>Open Drawer</Button2>
      <Drawer2 {...args} open={open} onClose={() => setOpen(false)}>
        <div className="space-y-4">
          <p className="text-neutral-600 dark:text-neutral-300">
            This is a drawer with smooth slide animations. It features:
          </p>
          <ul className="list-disc list-inside space-y-2 text-neutral-600 dark:text-neutral-300">
            <li>Backdrop fade animation</li>
            <li>Smooth slide-in animation based on side</li>
            <li>Spring physics for natural motion</li>
            <li>Smooth exit animations</li>
          </ul>
          <div className="flex gap-2 justify-end mt-6">
            <Button2 variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button2>
          </div>
        </div>
      </Drawer2>
    </div>
  );
};

export const Right: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Right Drawer',
    description: 'This drawer slides in from the right',
    side: 'right',
  },
};

export const Left: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Left Drawer',
    description: 'This drawer slides in from the left',
    side: 'left',
  },
};

export const Bottom: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Bottom Drawer',
    description: 'This drawer slides in from the bottom',
    side: 'bottom',
  },
};

export const SmallSize: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Small Drawer',
    description: 'This drawer uses the small size variant',
    side: 'right',
    size: 'sm',
  },
};

export const LargeSize: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Large Drawer',
    description: 'This drawer uses the large size variant',
    side: 'right',
    size: 'lg',
  },
};

export const NoCloseButton: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'No Close Button',
    description: 'This drawer hides the close button',
    side: 'right',
    showClose: false,
  },
};

export const WithNavigation: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Navigation Menu',
    side: 'left',
    children: (
      <nav className="space-y-2">
        <a
          href="#"
          className="block px-4 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
        >
          Dashboard
        </a>
        <a
          href="#"
          className="block px-4 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
        >
          Jobs
        </a>
        <a
          href="#"
          className="block px-4 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
        >
          Applications
        </a>
        <a
          href="#"
          className="block px-4 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
        >
          Recommendations
        </a>
        <a
          href="#"
          className="block px-4 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
        >
          Analytics
        </a>
        <a
          href="#"
          className="block px-4 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
        >
          Settings
        </a>
      </nav>
    ),
  },
};

export const WithFilters: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Filter Options',
    description: 'Refine your search results',
    side: 'right',
    children: (
      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Job Type</h3>
          <div className="space-y-2">
            {['Full-time', 'Part-time', 'Contract', 'Internship'].map((type) => (
              <label key={type} className="flex items-center">
                <input type="checkbox" className="mr-2" />
                <span className="text-neutral-600 dark:text-neutral-400">{type}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Experience Level</h3>
          <div className="space-y-2">
            {['Entry Level', 'Mid Level', 'Senior Level', 'Executive'].map((level) => (
              <label key={level} className="flex items-center">
                <input type="checkbox" className="mr-2" />
                <span className="text-neutral-600 dark:text-neutral-400">{level}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Salary Range</h3>
          <input
            type="range"
            min="0"
            max="200000"
            step="10000"
            className="w-full"
          />
          <div className="flex justify-between text-sm text-neutral-600 dark:text-neutral-400 mt-1">
            <span>$0</span>
            <span>$200k+</span>
          </div>
        </div>
        <div className="flex gap-2 pt-4">
          <Button2 variant="outline" className="flex-1">
            Reset
          </Button2>
          <Button2 className="flex-1">Apply Filters</Button2>
        </div>
      </div>
    ),
  },
};

export const LongContent: Story = {
  render: (args) => <DrawerWrapper {...args} />,
  args: {
    title: 'Drawer with Long Content',
    description: 'This drawer contains a lot of content to demonstrate scrolling',
    side: 'right',
    children: (
      <div className="space-y-4">
        {Array.from({ length: 30 }, (_, i) => (
          <p key={i} className="text-neutral-600 dark:text-neutral-300">
            This is paragraph {i + 1}. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
          </p>
        ))}
      </div>
    ),
  },
};
