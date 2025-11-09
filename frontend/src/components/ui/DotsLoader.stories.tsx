import type { Meta, StoryObj } from '@storybook/react';

import DotsLoader from './DotsLoader';

const meta = {
  title: 'UI/Loading/DotsLoader',
  component: DotsLoader,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size of the dots',
    },
    color: {
      control: 'select',
      options: ['primary', 'secondary', 'white', 'current'],
      description: 'Color of the dots',
    },
    label: {
      control: 'text',
      description: 'Label for screen readers',
    },
  },
} satisfies Meta<typeof DotsLoader>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default dots loader
 */
export const Default: Story = {
  args: {
    size: 'md',
    color: 'primary',
  },
};

/**
 * All sizes demonstration
 */
export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-12">
      <div className="flex flex-col items-center gap-4">
        <DotsLoader size="sm" />
        <span className="text-xs text-neutral-600">Small</span>
      </div>
      <div className="flex flex-col items-center gap-4">
        <DotsLoader size="md" />
        <span className="text-xs text-neutral-600">Medium</span>
      </div>
      <div className="flex flex-col items-center gap-4">
        <DotsLoader size="lg" />
        <span className="text-xs text-neutral-600">Large</span>
      </div>
    </div>
  ),
};

/**
 * All colors demonstration
 */
export const Colors: Story = {
  render: () => (
    <div className="flex items-center gap-12">
      <div className="flex flex-col items-center gap-4">
        <DotsLoader color="primary" size="lg" />
        <span className="text-sm text-neutral-600">Primary</span>
      </div>
      <div className="flex flex-col items-center gap-4">
        <DotsLoader color="secondary" size="lg" />
        <span className="text-sm text-neutral-600">Secondary</span>
      </div>
      <div className="flex flex-col items-center gap-4 rounded-lg bg-neutral-900 p-6">
        <DotsLoader color="white" size="lg" />
        <span className="text-sm text-white">White</span>
      </div>
    </div>
  ),
};

/**
 * Inline with text
 */
export const InlineWithText: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <span className="text-sm text-neutral-700">Loading</span>
      <DotsLoader size="sm" />
    </div>
  ),
};

/**
 * In a button
 */
export const InButton: Story = {
  render: () => (
    <button className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-white">
      <span>Processing</span>
      <DotsLoader size="sm" color="white" />
    </button>
  ),
};

/**
 * In a card
 */
export const InCard: Story = {
  render: () => (
    <div className="w-96 rounded-lg border border-neutral-200 bg-white p-8 shadow-sm">
      <div className="flex flex-col items-center justify-center gap-4">
        <DotsLoader size="lg" color="primary" />
        <p className="text-sm text-neutral-600">Fetching your data</p>
      </div>
    </div>
  ),
};

/**
 * Large for emphasis
 */
export const Large: Story = {
  args: {
    size: 'lg',
    color: 'primary',
    label: 'Loading content...',
  },
};
