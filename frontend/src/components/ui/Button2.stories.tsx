import React from 'react';
import Button from './Button2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Button> = {
    title: 'Components/UI/Button2',
    component: Button,
    tags: ['autodocs'],
};
export default meta;
type Story = StoryObj<typeof Button>;

export const Variants: Story = {
    render: () => (
        <div className="flex flex-wrap gap-4">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="success">Success</Button>
        </div>
    ),
};

export const Sizes: Story = {
    render: () => (
        <div className="flex flex-wrap gap-4">
            <Button size="sm">Small</Button>
            <Button size="md">Medium</Button>
            <Button size="lg">Large</Button>
            <Button size="xl">Extra Large</Button>
        </div>
    ),
};

export const Loading: Story = {
    render: () => (
        <Button loading>Loading</Button>
    ),
};

export const WithIcon: Story = {
    render: () => (
        <Button variant="primary">
            <span className="mr-2">🚀</span>
            With Icon
        </Button>
    ),
};
