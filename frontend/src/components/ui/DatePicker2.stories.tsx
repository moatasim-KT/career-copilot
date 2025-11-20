import React, { useState } from 'react';
import { DatePicker2 } from './DatePicker2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof DatePicker2> = {
    title: 'Components/UI/DatePicker2',
    component: DatePicker2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof DatePicker2>;

export const Default: Story = {
    render: () => {
        const [date, setDate] = useState<Date | null>(null);
        return <DatePicker2 value={date} onChange={setDate} />;
    },
};

export const WithLabel: Story = {
    render: () => {
        const [date, setDate] = useState<Date | null>(null);
        return <DatePicker2 value={date} onChange={setDate} label="Start Date" />;
    },
};

export const WithError: Story = {
    render: () => {
        const [date, setDate] = useState<Date | null>(null);
        return <DatePicker2 value={date} onChange={setDate} label="Start Date" error="Please select a date." />;
    },
};

export const Range: Story = {
    render: () => {
        const [startDate, setStartDate] = useState<Date | null>(null);
        const [endDate, setEndDate] = useState<Date | null>(null);
        return (
            <DatePicker2
                range
                startDate={startDate}
                endDate={endDate}
                onRangeChange={(start, end) => {
                    setStartDate(start);
                    setEndDate(end);
                }}
                label="Date Range"
            />
        );
    },
};
