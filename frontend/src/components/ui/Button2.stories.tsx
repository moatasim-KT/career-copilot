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

export const GlowEffects: Story = {
    render: () => (
        <div className="flex flex-col gap-8 p-8 bg-neutral-900">
            <div>
                <h3 className="text-white mb-4 text-lg font-semibold">Primary Glow</h3>
                <div className="flex flex-wrap gap-4">
                    <Button variant="primary" glow>
                        Primary with Glow
                    </Button>
                    <Button variant="primary" glow size="lg">
                        Large Primary Glow
                    </Button>
                </div>
            </div>
            
            <div>
                <h3 className="text-white mb-4 text-lg font-semibold">Success Glow</h3>
                <div className="flex flex-wrap gap-4">
                    <Button variant="success" glow>
                        Success with Glow
                    </Button>
                    <Button variant="success" glow size="lg">
                        Large Success Glow
                    </Button>
                </div>
            </div>
            
            <div>
                <h3 className="text-white mb-4 text-lg font-semibold">Destructive Glow</h3>
                <div className="flex flex-wrap gap-4">
                    <Button variant="destructive" glow>
                        Destructive with Glow
                    </Button>
                    <Button variant="destructive" glow size="lg">
                        Large Destructive Glow
                    </Button>
                </div>
            </div>
            
            <div>
                <h3 className="text-white mb-4 text-lg font-semibold">Gradient Variant</h3>
                <div className="flex flex-wrap gap-4">
                    <Button variant="gradient">
                        Gradient Button
                    </Button>
                    <Button variant="gradient" glow>
                        Gradient with Glow
                    </Button>
                    <Button variant="gradient" glow size="lg">
                        Large Gradient Glow
                    </Button>
                </div>
            </div>
        </div>
    ),
};

export const PulseAnimation: Story = {
    render: () => (
        <div className="flex flex-col gap-8 p-8 bg-neutral-900">
            <div>
                <h3 className="text-white mb-4 text-lg font-semibold">Pulse for Critical Actions</h3>
                <div className="flex flex-wrap gap-4">
                    <Button variant="primary" glow pulse>
                        Critical Action
                    </Button>
                    <Button variant="destructive" glow pulse>
                        Delete Account
                    </Button>
                    <Button variant="success" glow pulse>
                        Confirm Payment
                    </Button>
                    <Button variant="gradient" glow pulse size="lg">
                        Start Now
                    </Button>
                </div>
            </div>
        </div>
    ),
};

export const GlowComparison: Story = {
    render: () => (
        <div className="flex flex-col gap-8 p-8">
            <div className="bg-white p-8 rounded-lg">
                <h3 className="mb-4 text-lg font-semibold">Light Mode</h3>
                <div className="flex flex-wrap gap-4">
                    <Button variant="primary">Without Glow</Button>
                    <Button variant="primary" glow>With Glow</Button>
                    <Button variant="gradient">Gradient</Button>
                    <Button variant="gradient" glow>Gradient + Glow</Button>
                </div>
            </div>
            
            <div className="bg-neutral-900 p-8 rounded-lg">
                <h3 className="text-white mb-4 text-lg font-semibold">Dark Mode</h3>
                <div className="flex flex-wrap gap-4">
                    <Button variant="primary">Without Glow</Button>
                    <Button variant="primary" glow>With Glow</Button>
                    <Button variant="gradient">Gradient</Button>
                    <Button variant="gradient" glow>Gradient + Glow</Button>
                </div>
            </div>
        </div>
    ),
};
