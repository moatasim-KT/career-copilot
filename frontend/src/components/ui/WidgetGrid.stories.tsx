
import { Meta, StoryObj } from '@storybook/react';
import WidgetGrid from './WidgetGrid';
import Widget from './Widget';

const meta: Meta<typeof WidgetGrid> = {
  title: 'UI/WidgetGrid',
  component: WidgetGrid,
};

export default meta;

type Story = StoryObj<typeof WidgetGrid>;

export const Default: Story = {
  args: {
    children: [
      <div key="a">
        <Widget title="Widget 1">Content for Widget 1</Widget>
      </div>,
      <div key="b">
        <Widget title="Widget 2">Content for Widget 2</Widget>
      </div>,
      <div key="c">
        <Widget title="Widget 3">Content for Widget 3</Widget>
      </div>,
    ],
  },
};
