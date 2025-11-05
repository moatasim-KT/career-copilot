
import { Meta, StoryObj } from '@storybook/react';
import Tooltip from './Tooltip';
import Button from './Button';

const meta: Meta<typeof Tooltip> = {
  title: 'UI/Tooltip',
  component: Tooltip,
  argTypes: {
    position: { control: { type: 'select', options: ['top', 'bottom', 'left', 'right'] } },
  },
};

export default meta;

type Story = StoryObj<typeof Tooltip>;

export const Default: Story = {
  args: {
    content: 'This is a tooltip',
    children: <Button>Hover me</Button>,
  },
};

export const PositionBottom: Story = {
  args: {
    content: 'This is a tooltip on the bottom',
    children: <Button>Hover me</Button>,
    position: 'bottom',
  },
};
