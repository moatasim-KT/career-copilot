
import { Meta, StoryObj } from '@storybook/react';
import Tabs from './Tabs';

const meta: Meta<typeof Tabs> = {
  title: 'UI/Tabs',
  component: Tabs,
};

export default meta;

type Story = StoryObj<typeof Tabs>;

const sampleTabs = [
  {
    id: 'tab1',
    label: 'Tab 1',
    content: <div>Content for Tab 1</div>,
  },
  {
    id: 'tab2',
    label: 'Tab 2',
    content: <div>Content for Tab 2</div>,
  },
  {
    id: 'tab3',
    label: 'Tab 3',
    content: <div>Content for Tab 3</div>,
  },
];

export const Default: Story = {
  args: {
    tabs: sampleTabs,
  },
};
