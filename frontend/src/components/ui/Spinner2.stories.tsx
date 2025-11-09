import type { Meta, StoryObj } from '@storybook/react';

import Spinner2 from './Spinner2';

const meta = {
  title: 'UI/Loading/Spinner2',
  component: Spinner2,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Size of the spinner',
    },
    variant: {
      control: 'select',
      options: ['default', 'smooth', 'pulsing'],
      description: 'Animation variant',
    },
    color: {
      control: 'select',
      options: ['primary', 'secondary', 'white', 'current'],
      description: 'Color of the spinner',
    },
    showLabel: {
      control: 'boolean',
      description: 'Show label text below spinner',
    },
    label: {
      control: 'text',
      description: 'Label for screen readers and display',
    },
  },
} satisfies Meta<typeof Spinner2>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default spinner with smooth animation
 */
export const Default: Story = {
  args: {
    size: 'md',
    variant: 'smooth',
    color: 'primary',
  },
};

/**
 * All sizes demonstration
 */
export const Sizes: Story = {
  render: () => (
    <div className="flex items-end gap-8">
      <div className="flex flex-col items-center gap-2">
        <Spinner2 size="xs" />
        <span className="text-xs text-neutral-600">XS</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Spinner2 size="sm" />
        <span className="text-xs text-neutral-600">SM</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Spinner2 size="md" />
        <span className="text-xs text-neutral-600">MD</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Spinner2 size="lg" />
        <span className="text-xs text-neutral-600">LG</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Spinner2 size="xl" />
        <span className="text-xs text-neutral-600">XL</span>
      </div>
    </div>
  ),
};

/**
 * All variants demonstration
 */
export const Variants: Story = {
  render: () => (
    <div className="flex items-center gap-12">
      <div className="flex flex-col items-center gap-2">
        <Spinner2 variant="default" size="lg" />
        <span className="text-sm text-neutral-600">Default</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Spinner2 variant="smooth" size="lg" />
        <span className="text-sm text-neutral-600">Smooth</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Spinner2 variant="pulsing" size="lg" />
        <span className="text-sm text-neutral-600">Pulsing</span>
      </div>
    </div>
  ),
};

/**
 * All colors demonstration
 */
export const Colors: Story = {
  render: () => (
    <div className="flex items-center gap-8">
      <div className="flex flex-col items-center gap-2">
        <Spinner2 color="primary" size="lg" />
        <span className="text-sm text-neutral-600">Primary</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Spinner2 color="secondary" size="lg" />
        <span className="text-sm text-neutral-600">Secondary</span>
      </div>
      <div className="flex flex-col items-center gap-2 rounded-lg bg-neutral-900 p-4">
        <Spinner2 color="white" size="lg" />
        <span className="text-sm text-white">White</span>
      </div>
    </div>
  ),
};

/**
 * Spinner with label
 */
export const WithLabel: Story = {
  args: {
    size: 'lg',
    variant: 'smooth',
    color: 'primary',
    showLabel: true,
    label: 'Loading data...',
  },
};

/**
 * Small spinner for inline use
 */
export const InlineSmall: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <span className="text-sm text-neutral-700">Processing</span>
      <Spinner2 size="sm" variant="smooth" />
    </div>
  ),
};

/**
 * Large pulsing spinner for emphasis
 */
export const LargePulsing: Story = {
  args: {
    size: 'xl',
    variant: 'pulsing',
    color: 'primary',
    showLabel: true,
    label: 'Please wait...',
  },
};

/**
 * In a card context
 */
export const InCard: Story = {
  render: () => (
    <div className="w-96 rounded-lg border border-neutral-200 bg-white p-8 shadow-sm">
      <div className="flex flex-col items-center justify-center gap-4">
        <Spinner2 size="lg" variant="smooth" color="primary" />
        <div className="text-center">
          <h3 className="text-lg font-semibold text-neutral-900">Loading Content</h3>
          <p className="mt-1 text-sm text-neutral-600">
            This will only take a moment...
          </p>
        </div>
      </div>
    </div>
  ),
};
