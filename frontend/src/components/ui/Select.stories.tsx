
import { Meta, StoryObj } from '@storybook/react';
import Select from './Select2';

const meta: Meta<typeof Select> = {
  title: 'UI/Select',
  component: Select,
  argTypes: {
    label: {
      control: 'text',
      description: 'Optional label for the select field',
    },
    error: {
      control: 'text',
      description: 'Optional error message to display',
    },
    options: {
      control: 'object',
      description: 'Array of options for the select dropdown',
    },
    defaultValue: {
      control: 'text',
      description: 'Default selected value',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the select field is disabled',
    },
  },
};

export default meta;

type Story = StoryObj<typeof Select>;

const sampleOptions = [
  { value: 'option1', label: 'Option 1' },
  { value: 'option2', label: 'Option 2' },
  { value: 'option3', label: 'Option 3' },
];

export const Default: Story = {
  args: {
    label: 'Choose an option',
    options: sampleOptions,
    defaultValue: 'option1',
  },
};

export const WithError: Story = {
  args: {
    label: 'Required field',
    options: sampleOptions,
    error: 'Please select an option',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled Select',
    options: sampleOptions,
    defaultValue: 'option2',
    disabled: true,
  },
};

export const WithPlaceholder: Story = {
  args: {
    label: 'Select a category',
    options: [
      { value: '', label: '-- Select --', disabled: true },
      ...sampleOptions,
    ],
    defaultValue: '',
  },
};
