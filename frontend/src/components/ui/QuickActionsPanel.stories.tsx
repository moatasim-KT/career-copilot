
import { Meta, StoryObj } from '@storybook/react';
import QuickActionsPanel from './QuickActionsPanel';

const meta: Meta<typeof QuickActionsPanel> = {
  title: 'UI/QuickActionsPanel',
  component: QuickActionsPanel,
};

export default meta;

type Story = StoryObj<typeof QuickActionsPanel>;

export const Default: Story = {
  args: {},
};
