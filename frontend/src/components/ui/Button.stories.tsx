import type { Meta, StoryObj } from '@storybook/react';

import Button from './Button2';

const meta = {
    title: 'UI/Button',
    component: Button,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        variant: {
            control: 'select',
            options: ['primary', 'secondary', 'outline', 'ghost', 'destructive'],
            description: 'The visual style variant of the button',
        },
        size: {
            control: 'select',
            options: ['sm', 'md', 'lg'],
            description: 'The size of the button',
        },
        loading: {
            control: 'boolean',
            description: 'Shows a loading spinner',
        },
        fullWidth: {
            control: 'boolean',
            description: 'Makes the button full width',
        },
        disabled: {
            control: 'boolean',
            description: 'Disables the button',
        },
    },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
    args: {
        children: 'Primary Button',
        variant: 'primary',
    },
};

export const Secondary: Story = {
    args: {
        children: 'Secondary Button',
        variant: 'secondary',
    },
};

export const Outline: Story = {
    args: {
        children: 'Outline Button',
        variant: 'outline',
    },
};

export const Ghost: Story = {
    args: {
        children: 'Ghost Button',
        variant: 'ghost',
    },
};

export const Destructive: Story = {
    args: {
        children: 'Destructive Button',
        variant: 'destructive',
    },
};

export const Small: Story = {
    args: {
        children: 'Small Button',
        size: 'sm',
    },
};

export const Medium: Story = {
    args: {
        children: 'Medium Button',
        size: 'md',
    },
};

export const Large: Story = {
    args: {
        children: 'Large Button',
        size: 'lg',
    },
};

export const Loading: Story = {
    args: {
        children: 'Loading Button',
        loading: true,
    },
};

export const Disabled: Story = {
    args: {
        children: 'Disabled Button',
        disabled: true,
    },
};

export const FullWidth: Story = {
    args: {
        children: 'Full Width Button',
        fullWidth: true,
    },
    parameters: {
        layout: 'padded',
    },
};

export const AllVariants: Story = {
    args: {
        children: 'Button',
    },
    render: () => (
        <div className="space-y-4">
            <div className="space-x-2">
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="destructive">Destructive</Button>
            </div>
            <div className="space-x-2">
                <Button size="sm">Small</Button>
                <Button size="md">Medium</Button>
                <Button size="lg">Large</Button>
            </div>
            <div className="space-x-2">
                <Button loading>Loading</Button>
                <Button disabled>Disabled</Button>
            </div>
        </div>
    ),
    parameters: {
        layout: 'padded',
    },
};
