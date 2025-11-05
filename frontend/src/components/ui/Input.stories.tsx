import { Meta, StoryObj } from '@storybook/react';
import Input from './Input';

const meta: Meta<typeof Input> = {
  title: 'UI/Input',
  component: Input,
  argTypes: {
    label: {
      control: 'text',
      description: 'Optional label for the input field',
    },
    error: {
      control: 'text',
      description: 'Optional error message to display',
    },
    variant: {
      control: 'select',
      options: ['default', 'ghost'],
      description: 'Visual variant of the input field',
    },
    type: {
      control: 'text',
      description: 'Type of the input field (e.g., text, password, email)',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text for the input field',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the input field is disabled',
    },
  },
};

export default meta;

type Story = StoryObj<typeof Input>;

export const Default: Story = {
  args: {
    label: 'Username',
    placeholder: 'Enter your username',
  },
};

export const WithError: Story = {
  args: {
    label: 'Email',
    placeholder: 'Enter your email',
    error: 'Invalid email address',
  },
};

export const PasswordInput: Story = {
  args: {
    label: 'Password',
    type: 'password',
    placeholder: 'Enter your password',
  },
};

export const GhostVariant: Story = {
  args: {
    label: 'Search',
    variant: 'ghost',
    placeholder: 'Search...',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled Input',
    placeholder: 'This input is disabled',
    disabled: true,
  },
};