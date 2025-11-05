/* eslint-disable storybook/no-renderer-packages */
import type { Meta, StoryObj } from '@storybook/react';

import Badge from './Badge';

const meta: Meta<typeof Badge> = {
    title: 'UI/Badge',
    component: Badge,
    tags: ['autodocs'],
    argTypes: {
        variant: {
            control: 'select',
            options: ['default', 'primary', 'secondary', 'success', 'warning', 'danger', 'info'],
        },
        size: {
            control: 'select',
            options: ['sm', 'md', 'lg'],
        },
    },
};

export default meta;
type Story = StoryObj<typeof Badge>;

export const Default: Story = {
    args: {
        children: 'Badge',
    },
};

export const Primary: Story = {
    args: {
        children: 'Primary',
        variant: 'primary',
    },
};

export const Success: Story = {
    args: {
        children: 'Success',
        variant: 'success',
    },
};

export const Warning: Story = {
    args: {
        children: 'Warning',
        variant: 'warning',
    },
};

export const Danger: Story = {
    args: {
        children: 'Danger',
        variant: 'danger',
    },
};

export const Sizes: Story = {
    render: () => (
        <div className="flex items-center gap-4">
            <Badge size="sm">Small</Badge>
            <Badge size="md">Medium</Badge>
            <Badge size="lg">Large</Badge>
        </div>
    ),
};

export const AllVariants: Story = {
    render: () => (
        <div className="flex flex-wrap gap-2">
            <Badge variant="default">Default</Badge>
            <Badge variant="primary">Primary</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge variant="danger">Danger</Badge>
            <Badge variant="info">Info</Badge>
        </div>
    ),
};

export const JobStatuses: Story = {
    render: () => (
        <div className="flex flex-wrap gap-2">
            <Badge variant="default">Manual</Badge>
            <Badge variant="primary">LinkedIn</Badge>
            <Badge variant="success">Indeed</Badge>
            <Badge variant="secondary">Glassdoor</Badge>
        </div>
    ),
};

