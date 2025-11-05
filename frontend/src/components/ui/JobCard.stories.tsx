
import { Meta, StoryObj } from '@storybook/react';
import JobCard, { Job } from './JobCard';

const meta: Meta<typeof JobCard> = {
  title: 'UI/JobCard',
  component: JobCard,
  argTypes: {
    variant: {
      control: { type: 'select', options: ['default', 'compact', 'featured'] },
    },
  },
};

export default meta;

type Story = StoryObj<typeof JobCard>;

const sampleJob: Job = {
  id: '1',
  title: 'Software Engineer',
  company: 'Google',
  location: 'Mountain View, CA',
  type: 'Full-time',
  postedAt: '2 days ago',
};

export const Default: Story = {
  args: {
    job: sampleJob,
    variant: 'default',
  },
};

export const Compact: Story = {
  args: {
    job: sampleJob,
    variant: 'compact',
  },
};

export const Featured: Story = {
  args: {
    job: sampleJob,
    variant: 'featured',
  },
};
