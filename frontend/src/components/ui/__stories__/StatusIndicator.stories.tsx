import type { Meta, StoryObj } from '@storybook/react';

import StatusIndicator from '../StatusIndicator';

const meta = {
  title: 'UI/StatusIndicator',
  component: StatusIndicator,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['success', 'warning', 'error', 'info', 'neutral'],
      description: 'Status variant determining color and glow',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size of the indicator',
    },
    pulse: {
      control: 'boolean',
      description: 'Whether to show pulse animation',
    },
    label: {
      control: 'text',
      description: 'Optional label text',
    },
    dotOnly: {
      control: 'boolean',
      description: 'Whether to show as a dot only (no label)',
    },
  },
} satisfies Meta<typeof StatusIndicator>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default status indicator with label
 */
export const Default: Story = {
  args: {
    variant: 'success',
    label: 'Active',
  },
};

/**
 * Dot only indicators
 */
export const DotOnly: Story = {
  args: {
    variant: 'success',
    dotOnly: true,
  },
  render: (args) => (
    <div className="flex items-center gap-4">
      <StatusIndicator {...args} variant="success" />
      <StatusIndicator {...args} variant="warning" />
      <StatusIndicator {...args} variant="error" />
      <StatusIndicator {...args} variant="info" />
      <StatusIndicator {...args} variant="neutral" />
    </div>
  ),
};

/**
 * With pulse animation
 */
export const WithPulse: Story = {
  args: {
    variant: 'success',
    pulse: true,
    dotOnly: true,
  },
  render: (args) => (
    <div className="flex items-center gap-4">
      <StatusIndicator {...args} variant="success" />
      <StatusIndicator {...args} variant="warning" />
      <StatusIndicator {...args} variant="error" />
      <StatusIndicator {...args} variant="info" />
      <StatusIndicator {...args} variant="neutral" />
    </div>
  ),
};

/**
 * All variants with labels
 */
export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-3">
      <StatusIndicator variant="success" label="Success" />
      <StatusIndicator variant="warning" label="Warning" />
      <StatusIndicator variant="error" label="Error" />
      <StatusIndicator variant="info" label="Info" />
      <StatusIndicator variant="neutral" label="Neutral" />
    </div>
  ),
};

/**
 * All sizes
 */
export const AllSizes: Story = {
  render: () => (
    <div className="flex flex-col gap-3">
      <StatusIndicator variant="success" label="Small" size="sm" />
      <StatusIndicator variant="success" label="Medium" size="md" />
      <StatusIndicator variant="success" label="Large" size="lg" />
    </div>
  ),
};

/**
 * With pulse animation and labels
 */
export const PulseWithLabels: Story = {
  render: () => (
    <div className="flex flex-col gap-3">
      <StatusIndicator variant="success" label="Online" pulse />
      <StatusIndicator variant="warning" label="Connecting" pulse />
      <StatusIndicator variant="error" label="Offline" pulse />
    </div>
  ),
};

/**
 * Real-world usage examples
 */
export const UsageExamples: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-6 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
      <div>
        <h3 className="text-sm font-semibold mb-2 text-neutral-700 dark:text-neutral-300">
          Application Status
        </h3>
        <div className="flex flex-wrap gap-2">
          <StatusIndicator variant="success" label="Accepted" />
          <StatusIndicator variant="info" label="In Review" />
          <StatusIndicator variant="warning" label="Pending" />
          <StatusIndicator variant="error" label="Rejected" />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2 text-neutral-700 dark:text-neutral-300">
          Connection Status
        </h3>
        <div className="flex flex-wrap gap-2">
          <StatusIndicator variant="success" label="Connected" pulse />
          <StatusIndicator variant="warning" label="Reconnecting" pulse />
          <StatusIndicator variant="error" label="Disconnected" />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2 text-neutral-700 dark:text-neutral-300">
          Inline Status Dots
        </h3>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <StatusIndicator variant="success" dotOnly pulse />
            <span className="text-sm text-neutral-700 dark:text-neutral-300">
              Server Online
            </span>
          </div>
          <div className="flex items-center gap-2">
            <StatusIndicator variant="warning" dotOnly pulse />
            <span className="text-sm text-neutral-700 dark:text-neutral-300">
              High Load
            </span>
          </div>
          <div className="flex items-center gap-2">
            <StatusIndicator variant="error" dotOnly />
            <span className="text-sm text-neutral-700 dark:text-neutral-300">
              Service Down
            </span>
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * Dark mode comparison
 */
export const DarkMode: Story = {
  parameters: {
    backgrounds: { default: 'dark' },
  },
  render: () => (
    <div className="dark">
      <div className="flex flex-col gap-3 p-6 bg-neutral-900 rounded-lg">
        <StatusIndicator variant="success" label="Success" />
        <StatusIndicator variant="warning" label="Warning" />
        <StatusIndicator variant="error" label="Error" />
        <StatusIndicator variant="info" label="Info" />
        <StatusIndicator variant="neutral" label="Neutral" />
      </div>
    </div>
  ),
};
