import React, { useState } from 'react';
import { Dialog2 } from './Dialog2';
import type { Meta, StoryObj } from '@storybook/react';
import Button from './Button2';

const meta: Meta<typeof Dialog2> = {
    title: 'Components/UI/Dialog2',
    component: Dialog2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Dialog2>;

export const Default: Story = {
    render: () => {
        const [isOpen, setIsOpen] = useState(false);
        return (
            <div>
                <Button onClick={() => setIsOpen(true)}>Open Dialog</Button>
                <Dialog2
                    open={isOpen}
                    onClose={() => setIsOpen(false)}
                    title="Dialog Title"
                    description="This is the dialog description."
                >
                    <p>This is the dialog content.</p>
                </Dialog2>
            </div>
        );
    },
};
