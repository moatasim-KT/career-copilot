import React, { useState } from 'react';
import { AlertDialog2 } from './AlertDialog2';
import type { Meta, StoryObj } from '@storybook/react';
import Button from './Button2';

const meta: Meta<typeof AlertDialog2> = {
    title: 'Components/UI/AlertDialog2',
    component: AlertDialog2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof AlertDialog2>;

export const Default: Story = {
    render: () => {
        const [isOpen, setIsOpen] = useState(false);
        return (
            <div>
                <Button onClick={() => setIsOpen(true)}>Open Alert Dialog</Button>
                <AlertDialog2
                    open={isOpen}
                    onClose={() => setIsOpen(false)}
                    onConfirm={() => setIsOpen(false)}
                    title="Are you sure?"
                    description="This action cannot be undone."
                />
            </div>
        );
    },
};

export const Danger: Story = {
    render: () => {
        const [isOpen, setIsOpen] = useState(false);
        return (
            <div>
                <Button onClick={() => setIsOpen(true)} variant="destructive">Open Danger Alert Dialog</Button>
                <AlertDialog2
                    open={isOpen}
                    onClose={() => setIsOpen(false)}
                    onConfirm={() => setIsOpen(false)}
                    title="Are you absolutely sure?"
                    description="This will permanently delete your account and all of your data."
                    danger
                />
            </div>
        );
    },
};
