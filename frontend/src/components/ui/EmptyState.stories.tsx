
import { Meta, StoryObj } from '@storybook/react';
import EmptyState from './EmptyState';
import Button from './Button';

const meta: Meta<typeof EmptyState> = {
  title: 'UI/EmptyState',
  component: EmptyState,
};

export default meta;

type Story = StoryObj<typeof EmptyState>;

export const Default: Story = {
  args: {
    title: 'No results found',
    message: 'Try adjusting your search or filter to find what you are looking for.',
  },
};

export const WithAction: Story = {
  args: {
    title: 'No jobs found',
    message: 'Get started by creating a new job.',
    action: <Button>Create Job</Button>,
  },
};
