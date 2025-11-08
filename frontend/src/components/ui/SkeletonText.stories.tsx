import type { Meta, StoryObj } from '@storybook/react';
import { SkeletonText } from './SkeletonText';

const meta = {
  title: 'UI/Loading/SkeletonText',
  component: SkeletonText,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['heading', 'paragraph', 'caption'],
      description: 'Text variant determining height and styling',
    },
    width: {
      control: 'select',
      options: ['full', '3/4', '1/2', '1/4'],
      description: 'Width as percentage of container',
    },
    animation: {
      control: 'select',
      options: ['pulse', 'shimmer', 'none'],
      description: 'Animation style for the skeleton',
    },
    lines: {
      control: { type: 'number', min: 1, max: 10 },
      description: 'Number of lines (for multi-line text)',
    },
  },
} satisfies Meta<typeof SkeletonText>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Heading: Story = {
  args: {
    variant: 'heading',
    width: '3/4',
    animation: 'pulse',
  },
};

export const Paragraph: Story = {
  args: {
    variant: 'paragraph',
    width: 'full',
    animation: 'pulse',
  },
};

export const Caption: Story = {
  args: {
    variant: 'caption',
    width: '1/2',
    animation: 'pulse',
  },
};

export const MultipleLines: Story = {
  args: {
    variant: 'paragraph',
    lines: 3,
    animation: 'pulse',
  },
  render: (args) => (
    <div className="max-w-2xl">
      <SkeletonText {...args} />
    </div>
  ),
};

export const ShimmerAnimation: Story = {
  args: {
    variant: 'paragraph',
    lines: 4,
    animation: 'shimmer',
  },
  render: (args) => (
    <div className="max-w-2xl">
      <SkeletonText {...args} />
    </div>
  ),
};

export const NoAnimation: Story = {
  args: {
    variant: 'paragraph',
    width: 'full',
    animation: 'none',
  },
};

export const ArticlePreview: Story = {
  name: 'Real-World Example: Article Preview',
  render: () => (
    <div className="max-w-3xl space-y-6 rounded-lg border border-neutral-200 bg-white p-8">
      {/* Title */}
      <SkeletonText variant="heading" width="3/4" animation="shimmer" />
      
      {/* Meta info */}
      <div className="flex gap-4">
        <SkeletonText variant="caption" width="1/4" />
        <SkeletonText variant="caption" width="1/4" />
      </div>
      
      {/* Body paragraphs */}
      <div className="space-y-4">
        <SkeletonText variant="paragraph" lines={3} animation="shimmer" />
        <SkeletonText variant="paragraph" lines={4} animation="shimmer" />
        <SkeletonText variant="paragraph" lines={2} animation="shimmer" />
      </div>
    </div>
  ),
};

export const DashboardStats: Story = {
  name: 'Real-World Example: Dashboard Stats',
  render: () => (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="rounded-xl border border-neutral-200 bg-white p-6">
          <SkeletonText variant="caption" width="1/2" className="mb-2" />
          <SkeletonText variant="heading" width="3/4" animation="shimmer" />
        </div>
      ))}
    </div>
  ),
};

export const AllVariants: Story = {
  name: 'All Variants',
  render: () => (
    <div className="space-y-8">
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-600">Heading</p>
        <SkeletonText variant="heading" width="3/4" />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-600">Paragraph</p>
        <SkeletonText variant="paragraph" width="full" />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-600">Caption</p>
        <SkeletonText variant="caption" width="1/2" />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-600">Multiple Lines</p>
        <SkeletonText variant="paragraph" lines={5} />
      </div>
    </div>
  ),
};
