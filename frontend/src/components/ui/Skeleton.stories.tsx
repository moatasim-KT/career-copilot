
import { Meta, StoryObj } from '@storybook/react';
import Skeleton from './Skeleton2';

const meta: Meta<typeof Skeleton> = {
  title: 'UI/Skeleton',
  component: Skeleton,
};

export default meta;

type Story = StoryObj<typeof Skeleton>;

export const Default: Story = {
  args: {
    className: 'h-4 w-full',
  },
};

export const Circle: Story = {
  args: {
    className: 'h-12 w-12 rounded-full',
  },
};

export const WithCustomSize: Story = {
  args: {
    className: 'h-24 w-48',
  },
};
