/**
 * Toast Component Story
 * 
 * Storybook stories for the Toast notification system.
 * 
 * @module components/common/Toast.stories
 */

import type { Meta, StoryObj } from '@storybook/react';
import { ToastProvider, useToast } from '@/components/common/Toast';
import { useEffect } from 'react';

const meta = {
    title: 'Components/Common/Toast',
    component: ToastProvider,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
} satisfies Meta<typeof ToastProvider>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Demo component to trigger toasts
 */
function ToastDemo({ type, message, duration }: { type: 'success' | 'error' | 'warning' | 'info'; message: string; duration?: number }) {
    const toast = useToast();

    useEffect(() => {
        toast[type](message, undefined, undefined);
    }, [toast, type, message]);

    return (
        <div className="flex flex-col gap-4 p-8">
            <button
                onClick={() => toast[type](message, undefined, undefined)}
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
                Show {type} Toast
            </button>
        </div>
    );
}

export const Success: Story = {
    render: () => (
        <ToastProvider>
            <ToastDemo type="success" message="Application submitted successfully!" />
        </ToastProvider>
    ),
};

export const Error: Story = {
    render: () => (
        <ToastProvider>
            <ToastDemo type="error" message="Failed to submit application. Please try again." />
        </ToastProvider>
    ),
};

export const Warning: Story = {
    render: () => (
        <ToastProvider>
            <ToastDemo type="warning" message="Your session will expire in 5 minutes." />
        </ToastProvider>
    ),
};

export const Info: Story = {
    render: () => (
        <ToastProvider>
            <ToastDemo type="info" message="New feature available! Check out the analytics dashboard." />
        </ToastProvider>
    ),
};

export const WithAction: Story = {
    render: () => (
        <ToastProvider>
            <WithActionDemo />
        </ToastProvider>
    ),
};

function WithActionDemo() {
    const toast = useToast();
    return (
        <div className="flex flex-col gap-4 p-8">
            <button
                onClick={() => {
                    toast.info('Application saved as draft', 'Info', {
                        label: 'View',
                        onClick: () => console.log('View clicked'),
                    });
                }}
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
                Show Toast with Action
            </button>
        </div>
    );
}
};

export const LongDuration: Story = {
    render: () => (
        <ToastProvider>
            <ToastDemo type="info" message="This toast will stay for 10 seconds" duration={10000} />
        </ToastProvider>
    ),
};

export const Multiple: Story = {
    render: () => (
        <ToastProvider>
            <MultipleDemo />
        </ToastProvider>
    ),
};

function MultipleDemo() {
    const toast = useToast();
    return (
        <div className="flex flex-col gap-4 p-8">
            <button
                onClick={() => {
                    toast.info('First notification');
                    setTimeout(() => toast.success('Second notification'), 500);
                    setTimeout(() => toast.warning('Third notification'), 1000);
                }}
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
                Show Multiple Toasts
            </button>
        </div>
    );
}
};
