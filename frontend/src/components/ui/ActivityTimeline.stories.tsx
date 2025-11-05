
import { Meta, StoryObj } from '@storybook/react';
import ActivityTimeline from './ActivityTimeline';

const meta: Meta<typeof ActivityTimeline> = {
  title: 'UI/ActivityTimeline',
  component: ActivityTimeline,
};

export default meta;

type Story = StoryObj<typeof ActivityTimeline>;

export const Default: Story = {
  args: {},
};
