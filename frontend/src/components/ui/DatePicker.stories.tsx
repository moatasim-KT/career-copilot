
import { Meta, StoryObj } from '@storybook/react';
import DatePicker from './DatePicker';
import React, { useState } from 'react';

const meta: Meta<typeof DatePicker> = {
  title: 'UI/DatePicker',
  component: DatePicker,
  argTypes: {
    date: {
      control: 'date',
      description: 'The selected date',
    },
    onSelect: {
      action: 'date selected',
      description: 'Callback function when date changes',
    },
    label: {
      control: 'text',
      description: 'Optional label for the date picker',
    },
    error: {
      control: 'text',
      description: 'Optional error message to display',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the date picker is disabled',
    },
  },
};

export default meta;

type Story = StoryObj<typeof DatePicker>;

export const Default: Story = {
  render: (args) => {
    const [date, setDate] = useState<Date | undefined>(args.date);
    return <DatePicker {...args} date={date} onSelect={setDate} />;
  },
  args: {
    label: 'Event Date',
    placeholder: 'Pick a date',
  },
};

export const WithDefaultDate: Story = {
  render: (args) => {
    const [date, setDate] = useState<Date | undefined>(new Date());
    return <DatePicker {...args} date={date} onSelect={setDate} />;
  },
  args: {
    label: 'Start Date',
  },
};

export const WithError: Story = {
  render: (args) => {
    const [date, setDate] = useState<Date | undefined>(args.date);
    return <DatePicker {...args} date={date} onSelect={setDate} />;
  },
  args: {
    label: 'End Date',
    error: 'Date is required',
  },
};

export const Disabled: Story = {
  render: (args) => {
    const [date, setDate] = useState<Date | undefined>(args.date);
    return <DatePicker {...args} date={date} onSelect={setDate} />;
  },
  args: {
    label: 'Disabled Date',
    disabled: true,
  },
};
