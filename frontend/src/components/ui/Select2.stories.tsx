import React, { useState } from 'react';
import { Select2 } from './Select2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Select2> = {
    title: 'Components/UI/Select2',
    component: Select2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Select2>;

export const Default: Story = {
    render: () => {
        const [value, setValue] = useState('');
        return (
            <Select2 value={value} onChange={(e) => setValue(e.target.value)} label="Choose an option">
                <option value="">Select...</option>
                <option value="option1">Option 1</option>
                <option value="option2">Option 2</option>
                <option value="option3">Option 3</option>
            </Select2>
        );
    },
};

export const Variants: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <Select2 variant="default" label="Default Select">
                <option value="">Select...</option>
                <option value="option1">Option 1</option>
            </Select2>
            <Select2 variant="filled" label="Filled Select">
                <option value="">Select...</option>
                <option value="option1">Option 1</option>
            </Select2>
            <Select2 variant="outlined" label="Outlined Select">
                <option value="">Select...</option>
                <option value="option1">Option 1</option>
            </Select2>
        </div>
    ),
};

export const WithError: Story = {
    render: () => (
        <Select2 label="Country" error="Please select a country.">
            <option value="">Select...</option>
            <option value="usa">USA</option>
        </Select2>
    ),
};
