import React, { useState } from 'react';
import { Textarea2 } from './Textarea2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Textarea2> = {
    title: 'Components/UI/Textarea2',
    component: Textarea2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Textarea2>;

export const Default: Story = {
    render: () => {
        const [value, setValue] = useState('');
        return (
            <Textarea2
                label="Description"
                placeholder="Enter description..."
                value={value}
                onChange={(e) => setValue(e.target.value)}
            />
        );
    },
};

export const Variants: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <Textarea2 variant="default" label="Default Textarea" placeholder="Default" />
            <Textarea2 variant="filled" label="Filled Textarea" placeholder="Filled" />
            <Textarea2 variant="outlined" label="Outlined Textarea" placeholder="Outlined" />
        </div>
    ),
};

export const WithCharacterCount: Story = {
    render: () => {
        const [value, setValue] = useState('');
        return (
            <Textarea2
                label="Bio"
                placeholder="Tell us about yourself..."
                value={value}
                onChange={(e) => setValue(e.target.value)}
                maxLength={200}
                showCount
            />
        );
    },
};

export const AutoResize: Story = {
    render: () => {
        const [value, setValue] = useState('');
        return (
            <Textarea2
                label="Notes"
                placeholder="Start typing..."
                value={value}
                onChange={(e) => setValue(e.target.value)}
                autoResize
            />
        );
    },
};

export const WithError: Story = {
    render: () => {
        const [value, setValue] = useState('Short text');
        return (
            <Textarea2
                label="Feedback"
                placeholder="Enter feedback..."
                value={value}
                onChange={(e) => setValue(e.target.value)}
                error="Feedback must be at least 10 characters."
            />
        );
    },
};
