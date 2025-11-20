
import { Meta, StoryObj } from '@storybook/react';
import Textarea from './Textarea2';

const meta: Meta<typeof Textarea> = {
  title: 'UI/Textarea',
  component: Textarea,
  argTypes: {
    label: {
      control: 'text',
      description: 'Optional label for the textarea field',
    },
    error: {
      control: 'text',
      description: 'Optional error message to display',
    },
    variant: {
      control: 'select',
      options: ['default', 'ghost'],
      description: 'Visual variant of the textarea field',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text for the textarea field',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the textarea field is disabled',
    },
  },
};

export default meta;

type Story = StoryObj<typeof Textarea>;

export const Default: Story = {
  args: {
    label: 'Description',
    placeholder: 'Enter a description',
  },
};

export const WithError: Story = {
  args: {
    label: 'Notes',
    placeholder: 'Add some notes',
    error: 'This field is required',
  },
};

export const GhostVariant: Story = {
  args: {
    label: 'Comment',
    variant: 'ghost',
    placeholder: 'Leave a comment...',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled Textarea',
    placeholder: 'This textarea is disabled',
    disabled: true,
  },
};
